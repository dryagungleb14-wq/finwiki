from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import QAPair, Keyword, QAPairStatus
from app.services.gemini_service import semantic_search
from app.services.cache_service import get_cached_result, set_cached_result
from app.services.text_processing_service import expand_query_with_synonyms, extract_keywords
from typing import List

def search_by_keywords(db: Session, query: str) -> List[QAPair]:
    """
    Поиск по ключевым словам с расширением синонимами
    """
    # Извлекаем ключевые слова из запроса (с лемматизацией)
    keywords = extract_keywords(query)

    # Расширяем синонимами
    expanded_query = expand_query_with_synonyms(query)
    expanded_keywords = extract_keywords(expanded_query)

    # Объединяем все ключевые слова
    all_keywords = list(set(keywords + expanded_keywords))

    if not all_keywords:
        # Fallback к простому разбиению
        all_keywords = query.lower().split()

    # Поиск в БД
    keyword_matches = db.query(Keyword).filter(
        or_(*[Keyword.keyword.ilike(f"%{word}%") for word in all_keywords])
    ).all()

    qa_pair_ids = list(set([kw.qa_pair_id for kw in keyword_matches]))

    if not qa_pair_ids:
        return []

    qa_pairs = db.query(QAPair).filter(
        QAPair.id.in_(qa_pair_ids),
        QAPair.status == QAPairStatus.approved
    ).all()

    return qa_pairs

def search_full_text(db: Session, query: str) -> List[QAPair]:
    """
    Полнотекстовый поиск с расширением синонимами
    """
    # Получаем ключевые слова с синонимами
    keywords = extract_keywords(query)
    expanded_query = expand_query_with_synonyms(query)
    expanded_keywords = extract_keywords(expanded_query)

    # Объединяем
    all_keywords = list(set(keywords + expanded_keywords))

    if not all_keywords:
        all_keywords = query.lower().split()

    # Поиск по всем полям
    qa_pairs = db.query(QAPair).filter(
        QAPair.status == QAPairStatus.approved,
        or_(
            *[QAPair.question.ilike(f"%{word}%") for word in all_keywords],
            *[QAPair.answer.ilike(f"%{word}%") for word in all_keywords],
            *[QAPair.question_processed.ilike(f"%{word}%") for word in all_keywords],
            *[QAPair.answer_processed.ilike(f"%{word}%") for word in all_keywords]
        )
    ).all()

    return qa_pairs

def search_semantic(db: Session, query: str) -> List[QAPair]:
    """
    Семантический поиск через Gemini 2.0 Flash
    - Убран лимит на количество QA пар
    - Использует все approved пары для максимальной точности
    """
    # Получаем ВСЕ approved QA пары (без лимита)
    qa_pairs = db.query(QAPair).filter(
        QAPair.status == QAPairStatus.approved
    ).all()

    if not qa_pairs:
        return []

    # Если QA пар очень много (>100), делаем keyword pre-filtering
    # чтобы не перегружать Gemini контекстом
    if len(qa_pairs) > 100:
        # Сначала быстрый keyword filter, затем semantic на топ-100
        keyword_filtered = search_by_keywords(db, query)
        fulltext_filtered = search_full_text(db, query)

        # Объединяем и убираем дубликаты
        combined = {qa.id: qa for qa in (keyword_filtered + fulltext_filtered)}
        pre_filtered = list(combined.values())

        # Если после pre-filter есть результаты, используем их
        # Иначе берем все QA пары (semantic search найдет релевантные)
        if pre_filtered:
            qa_pairs = pre_filtered[:100]  # Топ-100 для Gemini

    qa_list = [
        {
            "id": qa.id,
            "question": qa.question_processed or qa.question,
            "answer": qa.answer_processed or qa.answer,
            "qa_pair": qa
        }
        for qa in qa_pairs
    ]

    results = semantic_search(query, qa_list)

    return [item["qa_pair"] for item in results]

def search(db: Session, query: str) -> List[QAPair]:
    """
    Каскадный поиск с кэшированием:
    1. Проверяем кэш
    2. Keyword search (быстро)
    3. Full-text search (средне)
    4. Semantic search через Gemini (медленно, но точно)
    5. Сохраняем результат в кэш
    """
    # 1. Проверяем кэш
    cached = get_cached_result(query)
    if cached is not None:
        # Восстанавливаем QAPair объекты из кэша
        qa_ids = cached.get("qa_ids", [])
        if qa_ids:
            results = db.query(QAPair).filter(QAPair.id.in_(qa_ids)).all()
            # Сортируем в том же порядке, что был в кэше
            results_dict = {qa.id: qa for qa in results}
            results = [results_dict[qa_id] for qa_id in qa_ids if qa_id in results_dict]
            return results[:10]

    # 2. Keyword search
    results = search_by_keywords(db, query)

    # 3. Full-text search
    if not results:
        results = search_full_text(db, query)

    # 4. Semantic search (Gemini)
    if not results:
        results = search_semantic(db, query)

    # 5. Кэшируем результаты
    if results:
        cache_data = {
            "qa_ids": [qa.id for qa in results[:10]],
            "found": True
        }
        set_cached_result(query, cache_data, ttl=3600)  # 1 час

    return results[:10]

