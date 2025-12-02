import google.generativeai as genai
import os
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.services.rate_limiter_service import get_rate_limiter
from app.services.cache_service import get_cached_result, set_cached_result
from app.services.search_service import search_semantic, search_by_keywords, search_full_text
from app.models import QAPair

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
        return {
            "found": False,
            "answer": "",
            "confidence": 0.0,
            "sources": []
        }

    model = genai.GenerativeModel('gemini-2.0-flash-exp')

    context = "\n\n".join([
        f"Запись {i+1}:\nВопрос: {qa.question}\nОтвет: {qa.answer}"
        for i, qa in enumerate(qa_pairs)
    ])

    prompt = f"""Ты - финансовый помощник компании. Ответь на вопрос пользователя на основе базы знаний.

ВОПРОС ПОЛЬЗОВАТЕЛЯ: {question}

БАЗА ЗНАНИЙ:
{context}

ЗАДАЧА:
1. Если в базе знаний есть точный или релевантный ответ - используй его
2. Если нужно объединить информацию из нескольких записей - сделай это
3. Оцени свою уверенность в ответе (0.0 - 1.0)
4. Если уверенность < 0.8, лучше не отвечать

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
        return cached

    intent_data = analyze_intent(question)

    search_queries = intent_data.get("search_queries", [question])
    all_results = []
    seen_ids = set()

    for query in search_queries[:2]:
        results = search_semantic(db, query)
        if not results:
            results = search_by_keywords(db, query)
        if not results:
            results = search_full_text(db, query)

        for qa in results[:5]:
            if qa.id not in seen_ids:
                all_results.append(qa)
                seen_ids.add(qa.id)

    if not all_results:
        result = {
            "found": False,
            "answer": "",
            "confidence": 0.0,
            "sources": [],
            "call_manager": True,
            "intent": intent_data
        }
        set_cached_result(cache_key, result, ttl=1800)
        return result

    synthesis = synthesize_answer(question, all_results[:5])

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
