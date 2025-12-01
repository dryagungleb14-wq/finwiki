#!/usr/bin/env python3
"""
Скрипт для добавления тестового вопроса в базу знаний
"""
import requests
import os

# URL вашего backend на Railway
BACKEND_URL = input("Введите URL вашего backend (например, https://your-backend.railway.app): ").strip()
ADMIN_API_KEY = input("Введите ADMIN_API_KEY: ").strip()

headers = {
    "X-API-Key": ADMIN_API_KEY,
    "Content-Type": "application/json"
}

# Создаем QA пару
qa_data = {
    "question": "Когда выплачивается зарплата?",
    "answer": "Зарплата выплачивается 5-го и 20-го числа каждого месяца. 5-го числа - первая часть (аванс), 20-го числа - вторая часть (основная зарплата).",
    "submitted_by": "admin",
    "status": "approved"
}

print(f"\n📝 Добавляем тестовый вопрос в базу знаний...")
print(f"Вопрос: {qa_data['question']}")
print(f"Ответ: {qa_data['answer'][:50]}...")

try:
    # Отправляем POST запрос
    response = requests.post(
        f"{BACKEND_URL}/api/admin/qa",
        json=qa_data,
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Вопрос успешно добавлен! ID: {result.get('id')}")
        print(f"Статус: {result.get('status')}")
        print(f"\n🧪 Теперь попробуйте спросить бота: 'Когда зарплата?'")
    else:
        print(f"\n❌ Ошибка: {response.status_code}")
        print(f"Ответ: {response.text}")

except Exception as e:
    print(f"\n❌ Ошибка подключения: {e}")
    print("\nПроверьте:")
    print("1. URL backend правильный")
    print("2. ADMIN_API_KEY правильный")
    print("3. Backend запущен")
