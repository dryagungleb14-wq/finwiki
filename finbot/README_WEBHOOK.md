# FinBot — настройка через Webhooks (Events API)

## Что нужно сделать

Настроить Slack бота, который будет отвечать на вопросы сотрудников из базы знаний FinWiki.

## Шаг 1: Создание приложения в Slack

1. Откройте https://api.slack.com/apps
2. Нажмите "Create New App"
3. Выберите "From scratch"
4. Введите название: **FinBot** (или любое другое)
5. Выберите ваш workspace
6. Нажмите "Create App"

## Шаг 2: Настройка Bot Token Scopes (права бота)

1. В меню слева выберите "OAuth & Permissions"
2. Прокрутите до раздела "Bot Token Scopes"
3. Нажмите "Add an OAuth Scope" и добавьте по очереди:
   - `app_mentions:read` — читать упоминания бота
   - `chat:write` — отправлять сообщения
   - `im:history` — читать историю личных сообщений
   - `im:read` — читать личные сообщения
   - `im:write` — писать в личные сообщения
   - `channels:history` — читать историю каналов (опционально)
   - `groups:history` — читать историю групп (опционально)

## Шаг 3: Настройка Event Subscriptions (вебхуки)

1. В меню слева выберите "Event Subscriptions"
2. Включите переключатель "Enable Events"
3. В поле "Request URL" укажите URL вашего бота:
   - **Для облачного сервиса:** URL будет предоставлен после деплоя (см. шаг 6, вариант C)
   - **Для своего сервера:** `https://ваш-домен.com/slack/events`
   - **Для локального тестирования:** используйте ngrok (см. шаг 6, вариант B)
   - **Важно:** URL должен быть доступен из интернета (HTTPS)
   - **Примечание:** Если URL еще нет, сначала выполните шаг 6, затем вернитесь сюда
4. В разделе "Subscribe to bot events" нажмите "Add Bot User Event" и добавьте:
   - `app_mention` — когда бота упоминают в канале
   - `message.im` — когда пишут боту в личку
5. Нажмите "Save Changes"

## Шаг 4: Получение токенов

1. **Bot Token:**
   - Перейдите в "OAuth & Permissions"
   - В разделе "OAuth Tokens for Your Workspace" найдите "Bot User OAuth Token"
   - Скопируйте токен (начинается с `xoxb-`)
   - Сохраните его — понадобится позже

2. **Signing Secret:**
   - Перейдите в "Basic Information"
   - В разделе "App Credentials" найдите "Signing Secret"
   - Нажмите "Show" и скопируйте секрет
   - Сохраните его — понадобится позже

## Шаг 5: Установка бота в workspace

1. Перейдите в "OAuth & Permissions"
2. Нажмите кнопку "Install to Workspace" (вверху страницы)
3. Разрешите доступ
4. Бот установлен в ваш workspace

## Шаг 6: Настройка сервера (где будет работать бот)

### Вариант C: Деплой на облачный сервис (Railway, Heroku, Render и т.д.)

**Как получить URL:**

1. **Railway:**
   - Создайте проект на https://railway.app
   - Загрузите код бота (`bot_webhook.py` и `requirements.txt`)
   - Railway автоматически создаст URL вида: `https://ваш-проект.up.railway.app`
   - Ваш URL для Slack: `https://ваш-проект.up.railway.app/slack/events`
   - Установите переменные окружения в настройках проекта

2. **Heroku:**
   - Создайте приложение на https://heroku.com
   - Загрузите код через Git или Heroku CLI
   - Heroku создаст URL: `https://ваше-приложение.herokuapp.com`
   - Ваш URL для Slack: `https://ваше-приложение.herokuapp.com/slack/events`
   - Установите переменные окружения: `heroku config:set SLACK_BOT_TOKEN=...`

3. **Render:**
   - Создайте Web Service на https://render.com
   - Подключите репозиторий или загрузите код
   - Render создаст URL: `https://ваш-сервис.onrender.com`
   - Ваш URL для Slack: `https://ваш-сервис.onrender.com/slack/events`
   - Установите переменные окружения в настройках сервиса

4. **После получения URL:**
   - Вернитесь в Slack (шаг 3) и вставьте URL в поле "Request URL"
   - Slack проверит URL — должно появиться сообщение "Verified"

**Что нужно загрузить на сервис:**
- Файл `bot_webhook.py`
- Файл `requirements.txt`
- Файл `Procfile` (если нужен для вашего сервиса)

**Переменные окружения для установки на сервисе:**
```
SLACK_BOT_TOKEN=xoxb-ваш-бот-токен
SLACK_SIGNING_SECRET=ваш-signing-secret
API_URL=https://ваш-api-домен.com
PORT=3000
```

### Вариант A: Если у вас уже есть сервер

1. Загрузите файл `finbot/bot_webhook.py` на сервер
2. Установите зависимости:
   ```bash
   pip install -r finbot/requirements.txt
   ```
3. Создайте файл `.env` на сервере (скопируйте `env.example` и заполните значения):
   ```
   SLACK_BOT_TOKEN=xoxb-ваш-бот-токен
   SLACK_SIGNING_SECRET=ваш-signing-secret
   API_URL=https://ваш-api-домен.com
   PORT=3000
   ```
4. Запустите бота:
   ```bash
   python bot_webhook.py
   ```
5. Убедитесь, что бот доступен по адресу: `https://ваш-домен.com/slack/events`
6. Используйте этот URL в Slack (шаг 3): `https://ваш-домен.com/slack/events`

### Вариант B: Если нужно протестировать локально (через ngrok)

1. Установите ngrok: https://ngrok.com/download
2. Запустите ваш API (backend):
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```
3. В другом терминале запустите ngrok:
   ```bash
   ngrok http 3000
   ```
4. Скопируйте HTTPS URL (например: `https://abc123.ngrok.io`)
5. Обновите "Request URL" в Slack (шаг 3): `https://ваш-ngrok-url.ngrok.io/slack/events`
6. Создайте файл `.env` в папке `finbot` (скопируйте `env.example` и заполните значения):
   ```
   SLACK_BOT_TOKEN=xoxb-ваш-бот-токен
   SLACK_SIGNING_SECRET=ваш-signing-secret
   API_URL=http://localhost:8000
   PORT=3000
   ```
7. Запустите бота:
   ```bash
   cd finbot
   python bot_webhook.py
   ```

## Шаг 7: Проверка работы

1. Откройте Slack
2. Найдите вашего бота в списке приложений
3. Напишите боту в личку: "Привет, как дела?"
4. Бот должен ответить или сохранить вопрос

## Что делать, если не работает

- Проверьте, что все токены скопированы правильно
- Убедитесь, что URL доступен из интернета (для продакшена)
- Проверьте логи бота на наличие ошибок
- Убедитесь, что API (backend) работает и доступен

## Важные моменты

- **Bot Token** и **Signing Secret** — это секретные данные, не публикуйте их
- URL должен быть HTTPS (не HTTP) для продакшена
- Бот должен быть запущен постоянно (используйте systemd, PM2 или аналоги)
- Если меняете URL, обновите его в Slack (Event Subscriptions)


