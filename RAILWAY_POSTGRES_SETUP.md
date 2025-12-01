# Инструкция: настройка PostgreSQL в Railway для двух проектов

## Обзор

У тебя два сервиса на Railway:
1. **finwiki backend** — FastAPI приложение (нужен PostgreSQL)
2. **finbot backend** — Slack бот (делает HTTP запросы к finwiki backend, БД не нужна)

PostgreSQL нужен только для **finwiki backend**.

---

## Шаг 1: Создать PostgreSQL в проекте finwiki backend

1. Открой проект **finwiki backend** в Railway (тот, что с фиолетовой рамкой на скриншоте).

2. В панели проекта нажми кнопку **"+ New"** или **"Add Service"**.

3. Выбери **"Database"** → **"Add PostgreSQL"**.

4. Railway создаст новый сервис PostgreSQL в том же проекте.

5. Дождись завершения создания (обычно 1–2 минуты).

---

## Шаг 2: Получить строку подключения PostgreSQL

1. Открой созданный сервис PostgreSQL в том же проекте.

2. Перейди на вкладку **"Variables"** или **"Connect"**.

3. Найди переменную **`DATABASE_URL`** или **`POSTGRES_URL`** — это строка подключения.

   Пример формата:
   ```
   postgresql://postgres:password@containers-us-west-xxx.railway.app:5432/railway
   ```

4. Скопируй эту строку — она понадобится дальше.

   **Важно:** Railway может показывать её как **`${{Postgres.DATABASE_URL}}`** — это переменная, которую можно использовать в других сервисах того же проекта.

---

## Шаг 3: Подключить PostgreSQL к сервису finwiki backend

### Вариант А: через переменную окружения (рекомендуется)

1. Открой сервис **finwiki backend** в том же проекте.

2. Перейди на вкладку **"Variables"**.

3. Добавь или обнови переменную:
   - **Имя:** `DATABASE_URL`
   - **Значение:** вставь скопированную строку подключения из PostgreSQL сервиса

   Или, если Railway показывает переменную как `${{Postgres.DATABASE_URL}}`, используй её:
   - **Имя:** `DATABASE_URL`
   - **Значение:** `${{Postgres.DATABASE_URL}}`

4. Сохрани изменения.

### Вариант Б: через автоматическое связывание (если доступно)

1. В сервисе **finwiki backend** нажми **"Settings"**.

2. В разделе **"Connected Services"** или **"Service Dependencies"** выбери созданный PostgreSQL сервис.

3. Railway автоматически добавит переменную `DATABASE_URL` в finwiki backend.

---

## Шаг 4: Применить миграции Alembic на Railway

**Миграции применяются автоматически!**

Я настроил автоматическое применение миграций при каждом деплое:

1. Создан скрипт `backend/start.sh`, который:
   - Сначала применяет миграции Alembic (`alembic upgrade head`)
   - Затем запускает приложение

2. Обновлён `backend/Procfile`, чтобы использовать этот скрипт

3. **Тебе нужно только закоммитить и запушить изменения в GitHub:**
   ```bash
   git add backend/Procfile backend/start.sh backend/app/main.py
   git commit -m "Настроено автоматическое применение миграций Alembic"
   git push
   ```

4. Railway автоматически:
   - Запустит новый деплой
   - Применит миграции при старте приложения
   - Создаст все необходимые таблицы в PostgreSQL

**Важно:** Миграции применяются только один раз — Alembic отслеживает, какие миграции уже применены, и не будет пытаться создавать таблицы заново.

---

## Шаг 5: Проверить, что всё работает

1. После применения миграций открой URL finwiki backend:
   ```
   https://finwiki-backend-production.up.railway.app
   ```

2. Проверь эндпоинт здоровья:
   ```
   https://finwiki-backend-production.up.railway.app/health
   ```
   Должен вернуть `{"status": "ok"}`.

3. Проверь логи вопросов (должен вернуть пустой массив, если данных ещё нет):
   ```
   https://finwiki-backend-production.up.railway.app/api/log/questions
   ```

4. Проверь поиск:
   ```
   https://finwiki-backend-production.up.railway.app/api/slack/search?query=тест
   ```
   Должен вернуть `{"found": false}` (если в базе нет данных).

5. В логах сервиса **finwiki backend** на Railway не должно быть ошибок подключения к БД.

---

## Шаг 6: Настроить локальную разработку (опционально)

Если хочешь тестировать локально с PostgreSQL:

1. Создай файл `backend/.env` (не коммить в Git):
   ```bash
   DATABASE_URL=postgresql://user:password@host:port/database
   GEMINI_API_KEY=your_gemini_api_key_here
   FRONTEND_URL=http://localhost:3000
   ```

2. Используй либо:
   - Локальный PostgreSQL (установи и создай БД локально)
   - Или временно скопируй `DATABASE_URL` из Railway (для тестирования, не для продакшена)

3. Примени миграции локально:
   ```bash
   cd backend
   alembic upgrade head
   ```

4. Запусти backend:
   ```bash
   uvicorn app.main:app --reload
   ```

---

## Важные замечания

### Про finbot backend

- **finbot backend** не нуждается в PostgreSQL.
- Он только делает HTTP запросы к finwiki backend через переменную `API_URL`.
- Убедись, что в finbot backend есть переменная:
  - `API_URL=https://finwiki-backend-production.up.railway.app`

### Про безопасность

- Не коммить файлы `.env` с реальными `DATABASE_URL` в Git.
- Railway автоматически скрывает значения переменных в интерфейсе.
- Если нужно поделиться доступом к БД, используй Railway Sharing или создай отдельного пользователя БД.

### Про резервное копирование

- Railway автоматически делает бэкапы PostgreSQL, но можно настроить дополнительные через настройки сервиса PostgreSQL.

---

## Что дальше

После настройки PostgreSQL:

1. Все вопросы из Slack будут сохраняться в таблицу `questions`.
2. Все ответы бота будут сохраняться в таблицу `answers`.
3. База знаний (QAPair) будет храниться в `qa_pairs` и `keywords`.
4. Можно использовать эндпоинт `GET /api/log/questions` для просмотра истории вопросов/ответов.

---

## Если что-то пошло не так

### Ошибка подключения к БД

- Проверь, что переменная `DATABASE_URL` правильно установлена в finwiki backend.
- Проверь, что PostgreSQL сервис запущен (зелёный статус в Railway).
- Проверь логи finwiki backend на ошибки подключения.

### Ошибка миграций

- Убедись, что в `backend/migrations/versions/` есть файл миграции `20251201_0001_init_db.py`.
- Проверь, что Alembic установлен (должен быть в `requirements.txt`).
- Попробуй выполнить миграции через Railway Shell вручную.

### Данные не сохраняются

- Проверь логи finwiki backend — должны быть записи о создании вопросов/ответов.
- Проверь через `GET /api/log/questions` — должны появляться новые записи.
- Убедись, что миграции применены (`alembic upgrade head` выполнен успешно).

