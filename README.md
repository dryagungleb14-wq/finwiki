# Tool Zoo - База знаний для финансового менеджера

Веб-приложение для сбора и управления базой знаний с интеграцией Google Gemini API.

## Структура проекта

- `backend/` - FastAPI приложение
- `frontend/` - Веб-интерфейс (HTML/CSS/JS)

## Настройка Backend

1. Установите зависимости:
```bash
cd backend
pip install -r requirements.txt
```

2. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

3. Заполните переменные окружения:
- `DATABASE_URL` - URL подключения к PostgreSQL
- `GEMINI_API_KEY` - API ключ Google Gemini
- `FRONTEND_URL` - URL фронтенда (для CORS)

4. Запустите миграции (если используете Alembic):
```bash
alembic upgrade head
```

5. Запустите сервер:
```bash
uvicorn app.main:app --reload
```

## Настройка Frontend

1. Отредактируйте `frontend/config.js` и укажите URL вашего бэкенда:
```javascript
window.API_URL = 'https://your-backend-url.railway.app';
```

2. Для локальной разработки используйте:
```javascript
window.API_URL = 'http://localhost:8000';
```

## Деплой

### Backend на Railway

1. Создайте проект на Railway
2. Подключите PostgreSQL базу данных
3. Установите переменные окружения:
   - `DATABASE_URL` (автоматически при подключении PostgreSQL)
   - `GEMINI_API_KEY`
   - `FRONTEND_URL` (URL вашего фронтенда на Vercel)
4. Railway автоматически определит Python и запустит приложение

### Frontend на Vercel

1. Подключите репозиторий к Vercel
2. Укажите корневую папку: `frontend`
3. Обновите `config.js` с URL бэкенда на Railway

## Использование

1. **Добавление вопросов-ответов:**
   - Через форму (текст)
   - Импорт из CSV/Excel файла
   - Голосовое сообщение

2. **Аппрув:**
   - Финансовый менеджер просматривает список pending записей
   - Видит оригинал и обработанную версию от Gemini
   - Одобряет или отклоняет

3. **Поиск:**
   - Поиск по ключевым словам
   - Семантический поиск через Gemini

