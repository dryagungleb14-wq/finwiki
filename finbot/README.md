# FinBot — Slack бот для FinWiki

Простой Slack бот, который отвечает на вопросы сотрудников из базы знаний FinWiki.

## Настройка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `.env`:
```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
API_URL=http://localhost:8000
```

3. Запустите бота:
```bash
python bot.py
```

## Как получить токены Slack

1. Перейдите на https://api.slack.com/apps
2. Создайте новое приложение
3. В разделе "OAuth & Permissions" добавьте scope: `app_mentions:read`, `chat:write`, `im:history`, `im:read`, `im:write`
4. В разделе "Socket Mode" включите Socket Mode
5. Скопируйте Bot Token (начинается с `xoxb-`) и App Token (начинается с `xapp-`)

## Как работает

1. Сотрудник пишет боту вопрос в Slack
2. Бот ищет ответ в базе знаний через API
3. Если ответ найден — отправляет его
4. Если не найден — сохраняет вопрос и пишет: "Финансовый менеджер ответит позже — ответ появится в базе знаний"
5. Финансовый менеджер видит неотвеченные вопросы в веб-интерфейсе FinWiki и добавляет ответы


