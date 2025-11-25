# FinBot — настройка через Webhooks (Events API)

## Настройка в Slack

### 1. Создание приложения
1. Перейдите на https://api.slack.com/apps
2. Создайте новое приложение или выберите существующее
3. Выберите ваш workspace

### 2. Bot Token Scopes
В "OAuth & Permissions" → "Bot Token Scopes" добавьте:
- `app_mentions:read`
- `chat:write`
- `im:history`
- `im:read`
- `im:write`
- `channels:history` (опционально)
- `groups:history` (опционально)

### 3. Event Subscriptions
1. В меню выберите "Event Subscriptions"
2. Включите "Enable Events"
3. В "Request URL" укажите ваш публичный URL: `https://ваш-домен.com/slack/events`
4. В "Subscribe to bot events" добавьте:
   - `app_mention` — упоминания бота в каналах
   - `message.im` — личные сообщения боту
5. Нажмите "Save Changes"

### 4. Получение токенов
1. **Bot Token** (xoxb-...): "OAuth & Permissions" → "Bot User OAuth Token"
2. **Signing Secret**: "Basic Information" → "App Credentials" → "Signing Secret"

### 5. Установка в workspace
В "OAuth & Permissions" нажмите "Install to Workspace"

## Настройка локально (для тестирования)

### 1. Установите ngrok
```bash
brew install ngrok
# или скачайте с https://ngrok.com/
```

### 2. Запустите ngrok туннель
```bash
ngrok http 3000
```

Скопируйте HTTPS URL (например: `https://abc123.ngrok.io`)

### 3. Обновите Request URL в Slack
В "Event Subscriptions" → "Request URL" вставьте: `https://ваш-ngrok-url.ngrok.io/slack/events`

### 4. Создайте .env файл
```env
SLACK_BOT_TOKEN=xoxb-ваш-бот-токен
SLACK_SIGNING_SECRET=ваш-signing-secret
API_URL=http://localhost:8000
PORT=3000
```

### 5. Установите зависимости
```bash
pip install -r requirements.txt
```

### 6. Запустите бота
```bash
python bot_webhook.py
```

## Деплой в продакшен

1. Задеплойте `bot_webhook.py` на сервер (Railway, Heroku, etc.)
2. Укажите публичный URL в "Event Subscriptions" → "Request URL"
3. Установите переменные окружения на сервере

## Проверка работы

1. Напишите боту в личку или упомяните в канале
2. Бот должен ответить или сохранить вопрос


