import google.generativeai as genai
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
from app.services.rate_limiter_service import get_rate_limiter

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Инициализация rate limiter для Gemini API
# 10 RPM для Gemini 2.0 Flash free tier
rate_limiter = get_rate_limiter(rpm=10)

def process_qa_pair(question: str, answer: str) -> Dict[str, str]:
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    prompt = f"""Обработай следующий вопрос и ответ для базы знаний финансового менеджера.

Вопрос: {question}
Ответ: {answer}

Выполни следующие задачи:
1. Улучши формулировку вопроса, сделав его более понятным и структурированным
2. Улучши формулировку ответа, сделав его более четким и профессиональным
3. Извлеки 5-10 ключевых слов или фраз для поиска (каждое на новой строке, без нумерации)

Верни ответ в формате:
ВОПРОС_ОБРАБОТАННЫЙ: [улучшенный вопрос]
ОТВЕТ_ОБРАБОТАННЫЙ: [улучшенный ответ]
КЛЮЧЕВЫЕ_СЛОВА:
[список ключевых слов, каждое на новой строке]
"""
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        
        result = {
            "question_processed": question,
            "answer_processed": answer,
            "keywords": []
        }
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if 'ВОПРОС_ОБРАБОТАННЫЙ:' in line or 'ВОПРОС ОБРАБОТАННЫЙ:' in line:
                current_section = 'question'
                result["question_processed"] = line.split(':', 1)[-1].strip()
            elif 'ОТВЕТ_ОБРАБОТАННЫЙ:' in line or 'ОТВЕТ ОБРАБОТАННЫЙ:' in line:
                current_section = 'answer'
                result["answer_processed"] = line.split(':', 1)[-1].strip()
            elif 'КЛЮЧЕВЫЕ_СЛОВА:' in line or 'КЛЮЧЕВЫЕ СЛОВА:' in line:
                current_section = 'keywords'
            elif current_section == 'question' and line:
                result["question_processed"] = line
            elif current_section == 'answer' and line:
                result["answer_processed"] = line
            elif current_section == 'keywords' and line:
                keyword = line.strip().lstrip('- ').lstrip('* ').strip()
                if keyword:
                    result["keywords"].append(keyword)
        
        if not result["question_processed"] or result["question_processed"] == question:
            result["question_processed"] = question
        if not result["answer_processed"] or result["answer_processed"] == answer:
            result["answer_processed"] = answer
            
        return result
    except Exception as e:
        return {
            "question_processed": question,
            "answer_processed": answer,
            "keywords": []
        }

def process_voice_to_text(audio_data: bytes) -> str:
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = """Распознай речь из этого аудио файла и верни текст. Если это вопрос и ответ, раздели их на две части: ВОПРОС: и ОТВЕТ:"""
        
        try:
            response = model.generate_content([prompt, {"mime_type": "audio/mpeg", "data": audio_data}])
            return response.text
        except:
            return "ВОПРОС: [Распознавание голоса временно недоступно]\nОТВЕТ: [Пожалуйста, используйте текстовый ввод]"
    except Exception as e:
        raise Exception(f"Ошибка обработки голоса: {str(e)}")

def semantic_search(query: str, qa_pairs: List[Dict]) -> List[Dict]:
    """
    Улучшенный семантический поиск с использованием Gemini 2.0 Flash
    - Убран лимит на количество QA пар
    - Структурированный JSON ответ
    - Оценка релевантности для каждого результата
    """
    model = genai.GenerativeModel('gemini-2.0-flash-exp')

    # Форматируем все QA пары (без лимита)
    context = "\n\n".join([
        f"ID {i+1}:\nВопрос: {qa['question']}\nОтвет: {qa['answer']}"
        for i, qa in enumerate(qa_pairs)
    ])

    prompt = f"""Ты - система семантического поиска для финансовой базы знаний компании.

ЗАДАЧА: Найди наиболее релевантные вопросы из базы знаний, которые отвечают на вопрос пользователя.

ВАЖНО:
- Учитывай синонимы и разные формулировки одного вопроса
- "Когда зарплата?" = "Какого числа выплачивается зарплата?" = "Дата выплаты з/п"
- "Отпуск" = "отпускные" = "vacation"
- Анализируй смысл, а не точное совпадение слов

ВОПРОС ПОЛЬЗОВАТЕЛЯ: {query}

БАЗА ЗНАНИЙ:
{context}

ФОРМАТ ОТВЕТА (верни ТОЛЬКО валидный JSON):
{{
  "found": true,
  "matches": [
    {{"id": 1, "similarity": 0.95, "reason": "Прямое совпадение по смыслу"}},
    {{"id": 3, "similarity": 0.78, "reason": "Похожий контекст"}}
  ]
}}

Если совпадений нет, верни:
{{
  "found": false,
  "matches": []
}}

Верни только JSON, без дополнительного текста."""

    try:
        # Используем rate limiter для соблюдения API limits
        def make_request():
            return model.generate_content(prompt)

        response = rate_limiter.call(make_request)
        text = response.text.strip()

        # Убираем markdown code blocks если есть
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        elif text.startswith("```"):
            text = text.replace("```", "").strip()

        # Парсим JSON
        import json
        result = json.loads(text)

        if not result.get("found", False) or not result.get("matches"):
            return []

        # Собираем результаты, отсортированные по similarity
        matched_pairs = []
        for match in result["matches"]:
            idx = match["id"] - 1  # ID начинается с 1
            if 0 <= idx < len(qa_pairs):
                matched_pairs.append(qa_pairs[idx])

        return matched_pairs

    except json.JSONDecodeError as e:
        # Fallback: если JSON не распарсился, попробуем старый метод
        print(f"JSON parse error: {e}. Trying fallback parsing...")
        try:
            text = response.text.lower()
            if "нет совпадений" in text or "не найдено" in text or '"found": false' in text:
                return []

            # Ищем числа в ответе
            import re
            numbers = re.findall(r'"id":\s*(\d+)', text)
            if not numbers:
                numbers = re.findall(r'\b(\d+)\b', text)

            indices = []
            for num in numbers:
                idx = int(num) - 1
                if 0 <= idx < len(qa_pairs):
                    indices.append(idx)

            return [qa_pairs[i] for i in indices[:10]]  # Топ-10
        except:
            return []
    except Exception as e:
        print(f"Semantic search error: {e}")
        return []

