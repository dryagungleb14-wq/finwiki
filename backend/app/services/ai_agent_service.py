import google.generativeai as genai
import os
import json
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.services.rate_limiter_service import get_rate_limiter
from app.services.cache_service import get_cached_result, set_cached_result
from app.services.search_service import search_semantic, search_by_keywords, search_full_text
from app.models import QAPair

logger = logging.getLogger(__name__)

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
rate_limiter = get_rate_limiter(rpm=10)

def analyze_intent(question: str) -> Dict:
    cache_key = f"intent:{question}"
    cached = get_cached_result(cache_key)
    if cached:
        return cached

    model = genai.GenerativeModel('gemini-2.0-flash-exp')

    prompt = f"""Проанализируй вопрос пользователя и извлеки ключевую информацию.

ВОПРОС: {question}

Верни JSON:
{{
  "intent": "краткое описание намерения пользователя",
  "entities": ["ключевые сущности", "например: зарплата, отпуск, налоги"],
  "search_queries": ["расширенный поисковый запрос 1", "альтернативный запрос 2"]
}}

Верни только JSON без дополнительного текста."""

    try:
        def make_request():
            return model.generate_content(prompt)

        response = rate_limiter.call(make_request)
        text = response.text.strip()

        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        elif text.startswith("```"):
            text = text.replace("```", "").strip()

        result = json.loads(text)
        set_cached_result(cache_key, result, ttl=3600)
        return result

    except Exception as e:
        return {
            "intent": question,
            "entities": [],
            "search_queries": [question]
        }

def synthesize_answer(question: str, qa_pairs: List[QAPair]) -> Dict:
    if not qa_pairs:
        logger.warning(f"synthesize_answer вызван без QA пар для вопроса: '{question}'")
        return {
            "found": False,
            "answer": "",
            "confidence": 0.0,
            "sources": []
        }
    
    logger.info(f"synthesize_answer для вопроса '{question}' с {len(qa_pairs)} QA парами")

    model = genai.GenerativeModel('gemini-2.0-flash-exp')

    context = "\n\n".join([
        f"Запись {i+1}:\nВопрос: {qa.question}\nОтвет: {qa.answer}"
        for i, qa in enumerate(qa_pairs)
    ])

    prompt = f"""Ты - финансовый помощник компании. Ответь на вопрос пользователя на основе базы знаний.

ВОПРОС ПОЛЬЗОВАТЕЛЯ: {question}

БАЗА ЗНАНИЙ:
{context}

ВАЖНО:
- Если вопрос пользователя совпадает по смыслу с вопросом из базы знаний (даже если формулировка отличается) - это релевантный ответ
- Примеры совпадений по смыслу:
  * "когда выплачивается зарплата?" = "дата выплаты заработной платы" = "когда получу зарплату?"
  * "отпуск" = "отпускные" = "как оформить отпуск?"
- Если в базе знаний есть ответ на похожий вопрос - используй его с высокой уверенностью (confidence >= 0.85)
- Если ответ точно соответствует вопросу - confidence должен быть >= 0.9
- Если ответ частично соответствует - confidence может быть 0.7-0.85
- Только если ответ совсем не соответствует вопросу - confidence < 0.7

ЗАДАЧА:
1. Если в базе знаний есть точный или релевантный ответ - используй его
2. Если нужно объединить информацию из нескольких записей - сделай это
3. Оцени свою уверенность в ответе (0.0 - 1.0)
4. Будь более лояльным к оценке confidence - если вопрос и ответ связаны по смыслу, это уже хороший результат

ФОРМАТ ОТВЕТА (верни только JSON):
{{
  "found": true,
  "answer": "твой ответ на вопрос",
  "confidence": 0.95,
  "sources": [1, 2],
  "reason": "почему ты уверен или не уверен"
}}

Если нет релевантного ответа:
{{
  "found": false,
  "answer": "",
  "confidence": 0.0,
  "sources": [],
  "reason": "причина"
}}

Верни только JSON."""

    try:
        def make_request():
            return model.generate_content(prompt)

        response = rate_limiter.call(make_request)
        text = response.text.strip()

        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        elif text.startswith("```"):
            text = text.replace("```", "").strip()

        result = json.loads(text)

        source_ids = []
        for idx in result.get("sources", []):
            if isinstance(idx, int) and 0 < idx <= len(qa_pairs):
                source_ids.append(qa_pairs[idx - 1].id)

        return {
            "found": result.get("found", False),
            "answer": result.get("answer", ""),
            "confidence": float(result.get("confidence", 0.0)),
            "sources": source_ids,
            "reason": result.get("reason", "")
        }

    except Exception as e:
        if len(qa_pairs) == 1:
            return {
                "found": True,
                "answer": qa_pairs[0].answer,
                "confidence": 0.85,
                "sources": [qa_pairs[0].id],
                "reason": "fallback to single match"
            }

        return {
            "found": False,
            "answer": "",
            "confidence": 0.0,
            "sources": [],
            "reason": f"error: {str(e)}"
        }

def process_question(db: Session, question: str, confidence_threshold: float = 0.8) -> Dict:
    cache_key = f"agent:{question}"
    cached = get_cached_result(cache_key)
    if cached:
        logger.info(f"Кэш найден для вопроса: '{question}'")
        return cached

    logger.info(f"Анализ intent для вопроса: '{question}'")
    intent_data = analyze_intent(question)
    logger.info(f"Intent результат: {intent_data}")

    search_queries = intent_data.get("search_queries", [question])
    logger.info(f"Поисковые запросы: {search_queries}")
    
    all_results = []
    seen_ids = set()

    for query in search_queries[:2]:
        logger.info(f"Поиск для запроса: '{query}'")
        
        semantic_results = search_semantic(db, query)
        logger.info(f"Semantic search нашел {len(semantic_results)} результатов")
        
        keyword_results = search_by_keywords(db, query)
        logger.info(f"Keyword search нашел {len(keyword_results)} результатов")
        
        fulltext_results = search_full_text(db, query)
        logger.info(f"Full-text search нашел {len(fulltext_results)} результатов")

        combined_results = semantic_results + keyword_results + fulltext_results
        
        for qa in combined_results:
            if qa.id not in seen_ids:
                all_results.append(qa)
                seen_ids.add(qa.id)
                logger.debug(f"Добавлена QA пара ID={qa.id}, вопрос: '{qa.question[:50]}...'")

    logger.info(f"Всего найдено уникальных QA пар: {len(all_results)}")

    if not all_results:
        logger.warning(f"Не найдено ни одной QA пары для вопроса: '{question}'")
        result = {
            "found": False,
            "answer": "",
            "confidence": 0.0,
            "sources": [],
            "call_manager": True,
            "intent": intent_data,
            "reason": "Не найдено релевантных QA пар в базе знаний"
        }
        set_cached_result(cache_key, result, ttl=1800)
        return result

    logger.info(f"Генерация ответа на основе {len(all_results[:5])} QA пар")
    synthesis = synthesize_answer(question, all_results[:5])
    logger.info(f"Synthesis результат: found={synthesis.get('found')}, confidence={synthesis.get('confidence', 0.0)}, reason={synthesis.get('reason', '')}")

    call_manager = synthesis["confidence"] < confidence_threshold

    result = {
        "found": synthesis["found"],
        "answer": synthesis["answer"],
        "confidence": synthesis["confidence"],
        "sources": synthesis["sources"],
        "call_manager": call_manager,
        "intent": intent_data,
        "reason": synthesis.get("reason", "")
    }

    if synthesis["found"]:
        set_cached_result(cache_key, result, ttl=3600)

    return result
