# Инструкция по подключению к GitHub

## 1. Создайте репозиторий на GitHub

1. Перейдите на https://github.com/new
2. Создайте новый репозиторий (например, `tool-zoo`)
3. **НЕ** инициализируйте его с README, .gitignore или лицензией (у нас уже есть файлы)

## 2. Подключите локальный репозиторий к GitHub

Выполните следующие команды (замените `YOUR_USERNAME` и `tool-zoo` на ваши данные):

```bash
cd "/Users/gleb/Разработка/API AI manager"
git remote add origin https://github.com/YOUR_USERNAME/tool-zoo.git
git branch -M main
git push -u origin main
```

## 3. Настройка деплоя

### Vercel (Frontend)

1. Перейдите на https://vercel.com
2. Подключите ваш GitHub репозиторий
3. В настройках проекта:
   - **Root Directory**: `frontend`
   - **Build Command**: (оставьте пустым, это статический сайт)
   - **Output Directory**: (оставьте пустым)
4. После деплоя обновите `frontend/config.js` с URL вашего бэкенда

### Railway (Backend)

1. Перейдите на https://railway.app
2. Создайте новый проект
3. Выберите "Deploy from GitHub repo"
4. Подключите ваш репозиторий
5. В настройках проекта:
   - **Root Directory**: `backend`
   - Railway автоматически определит Python
6. Добавьте PostgreSQL базу данных:
   - Нажмите "New" → "Database" → "PostgreSQL"
7. Установите переменные окружения:
   - `DATABASE_URL` (автоматически при подключении PostgreSQL)
   - `GEMINI_API_KEY` (ваш ключ от Google Gemini)
   - `FRONTEND_URL` (URL вашего фронтенда на Vercel, например: `https://your-app.vercel.app`)

## 4. Обновите конфигурацию фронтенда

После получения URL бэкенда на Railway, обновите `frontend/config.js`:

```javascript
window.API_URL = 'https://your-backend.railway.app';
```

И закоммитьте изменения:

```bash
git add frontend/config.js
git commit -m "Update backend URL"
git push
```

Vercel автоматически передеплоит фронтенд с новым URL.

