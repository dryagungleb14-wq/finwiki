"""
Сервис для обработки текста:
- Лемматизация (приведение слов к начальной форме)
- Расширение запроса синонимами
- Нормализация текста
"""
from typing import List, Set

# Инициализация морфологического анализатора для русского языка
try:
    import pymorphy2
    morph = pymorphy2.MorphAnalyzer()
    PYMORPHY_AVAILABLE = True
    print("✅ Pymorphy2 loaded successfully")
except Exception as e:
    print(f"⚠️  Pymorphy2 not available: {e}. Lemmatization will use simple fallback.")
    morph = None
    PYMORPHY_AVAILABLE = False

# Словарь синонимов для финансовых терминов
SYNONYMS = {
    # Зарплата
    "зарплата": ["заработная плата", "з/п", "зп", "оплата труда", "выплата", "заработок"],
    "зарплату": ["заработную плату", "з/п", "зп", "оплату труда", "выплату"],
    "зарплаты": ["заработной платы", "з/п", "зп", "оплаты труда", "выплаты"],

    # Время
    "когда": ["какого числа", "в какой день", "дата", "срок", "время"],
    "дата": ["число", "день", "срок", "когда"],

    # Отпуск
    "отпуск": ["отпускные", "отдых", "vacation", "каникулы"],
    "отпускные": ["отпуск", "отдых", "vacation"],

    # Больничный
    "больничный": ["больничный лист", "болезнь", "sick leave", "больничка"],

    # Документы
    "справка": ["документ", "бумага", "certificate"],
    "договор": ["контракт", "соглашение", "contract"],

    # Выплаты
    "премия": ["бонус", "надбавка", "поощрение"],
    "аванс": ["предоплата", "задаток"],

    # Налоги
    "налог": ["налоги", "сбор", "отчисление", "tax"],
    "ндфл": ["подоходный налог", "налог на доходы"],

    # Работа
    "работа": ["должность", "позиция", "job", "работать"],
    "уволиться": ["увольнение", "resign", "quit"],

    # Время работы
    "график": ["расписание", "режим работы", "schedule"],
    "удаленка": ["удаленная работа", "remote", "дистанционка"],

    # Общие
    "получить": ["оформить", "взять", "забрать"],
    "как": ["каким образом", "способ"],
    "где": ["место", "адрес", "локация"],
}

# Стоп-слова (не несут смысловой нагрузки)
STOP_WORDS = {
    "а", "в", "во", "вы", "да", "еще", "и", "или", "их", "к", "как", "не",
    "на", "но", "о", "об", "от", "по", "с", "со", "то", "у", "уже", "я"
}


def lemmatize_word(word: str) -> str:
    """
    Приводит слово к начальной форме (лемме)
    Примеры:
    - "зарплаты" -> "зарплата"
    - "выплачивается" -> "выплачивать"
    - "работаем" -> "работать"
    """
    if PYMORPHY_AVAILABLE and morph:
        try:
            parsed = morph.parse(word.lower())[0]
            return parsed.normal_form
        except:
            pass

    # Fallback: простое приведение к lowercase
    return word.lower()


def get_synonyms(word: str) -> List[str]:
    """
    Возвращает список синонимов для слова
    """
    lemma = lemmatize_word(word)
    return SYNONYMS.get(lemma, [])


def expand_query_with_synonyms(query: str, include_lemmas: bool = True) -> str:
    """
    Расширяет запрос синонимами и леммами

    Args:
        query: исходный запрос
        include_lemmas: добавлять ли леммы слов

    Returns:
        расширенный запрос с синонимами

    Пример:
        "Когда зарплата?" -> "когда какого числа дата зарплата з/п оплата труда"
    """
    words = query.lower().split()
    expanded_words: Set[str] = set()

    for word in words:
        # Убираем знаки препинания
        clean_word = word.strip('.,!?:;')

        if not clean_word or clean_word in STOP_WORDS:
            continue

        # Добавляем исходное слово
        expanded_words.add(clean_word)

        # Добавляем лемму
        if include_lemmas:
            lemma = lemmatize_word(clean_word)
            expanded_words.add(lemma)

            # Добавляем синонимы леммы
            synonyms = get_synonyms(lemma)
            expanded_words.update(synonyms)
        else:
            # Синонимы исходного слова
            synonyms = get_synonyms(clean_word)
            expanded_words.update(synonyms)

    return ' '.join(sorted(expanded_words))


def normalize_query(query: str) -> str:
    """
    Нормализует запрос:
    - lowercase
    - удаление лишних пробелов
    - удаление знаков препинания
    """
    # Убираем знаки препинания
    for char in '.,!?:;':
        query = query.replace(char, ' ')

    # lowercase и удаление лишних пробелов
    return ' '.join(query.lower().split())


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Извлекает ключевые слова из текста
    - Приводит к леммам
    - Убирает стоп-слова
    - Фильтрует по минимальной длине
    """
    words = text.lower().split()
    keywords = []

    for word in words:
        # Очистка от знаков препинания
        clean_word = word.strip('.,!?:;-—')

        if not clean_word or len(clean_word) < min_length:
            continue

        # Лемматизация
        lemma = lemmatize_word(clean_word)

        # Пропускаем стоп-слова
        if lemma in STOP_WORDS:
            continue

        keywords.append(lemma)

    return list(set(keywords))  # Убираем дубликаты


def enhance_search_query(query: str) -> dict:
    """
    Комплексная обработка поискового запроса

    Returns:
        dict с разными вариантами запроса:
        - original: исходный запрос
        - normalized: нормализованный
        - with_lemmas: с леммами
        - with_synonyms: с синонимами
        - keywords: ключевые слова
    """
    return {
        "original": query,
        "normalized": normalize_query(query),
        "with_lemmas": ' '.join([lemmatize_word(w) for w in query.split()]),
        "with_synonyms": expand_query_with_synonyms(query),
        "keywords": extract_keywords(query)
    }


# Примеры использования
if __name__ == "__main__":
    # Тестирование
    test_queries = [
        "Когда зарплата?",
        "Как оформить отпуск?",
        "Где получить справку 2-НДФЛ?",
        "График работы в праздники"
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Исходный запрос: {query}")
        enhanced = enhance_search_query(query)
        print(f"Нормализованный: {enhanced['normalized']}")
        print(f"С леммами: {enhanced['with_lemmas']}")
        print(f"С синонимами: {enhanced['with_synonyms']}")
        print(f"Ключевые слова: {enhanced['keywords']}")
