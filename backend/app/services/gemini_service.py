import google.generativeai as genai
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def process_qa_pair(question: str, answer: str) -> Dict[str, str]:
    model = genai.GenerativeModel('gemini-pro')
    
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
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = """Распознай речь из этого аудио файла и верни текст. Если это вопрос и ответ, раздели их на две части: ВОПРОС: и ОТВЕТ:"""
        
        try:
            response = model.generate_content([prompt, {"mime_type": "audio/mpeg", "data": audio_data}])
            return response.text
        except:
            return "ВОПРОС: [Распознавание голоса временно недоступно]\nОТВЕТ: [Пожалуйста, используйте текстовый ввод]"
    except Exception as e:
        raise Exception(f"Ошибка обработки голоса: {str(e)}")

def semantic_search(query: str, qa_pairs: List[Dict]) -> List[Dict]:
    model = genai.GenerativeModel('gemini-pro')
    
    context = "\n\n".join([
        f"Вопрос {i+1}: {qa['question']}\nОтвет {i+1}: {qa['answer']}"
        for i, qa in enumerate(qa_pairs[:20])
    ])
    
    prompt = f"""Найди наиболее релевантные ответы на вопрос пользователя из следующей базы знаний.

Вопрос пользователя: {query}

База знаний:
{context}

Верни номера наиболее релевантных вопросов (например: 1, 3, 5) или "нет совпадений" если ничего не подходит."""
    
    try:
        response = model.generate_content(prompt)
        text = response.text.lower()
        
        if "нет совпадений" in text or "не найдено" in text:
            return []
        
        indices = []
        for word in text.split():
            if word.isdigit():
                idx = int(word) - 1
                if 0 <= idx < len(qa_pairs):
                    indices.append(idx)
        
        return [qa_pairs[i] for i in indices if i < len(qa_pairs)]
    except Exception as e:
        return []

