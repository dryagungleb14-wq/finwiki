#!/bin/bash
set -e

echo "Применяю миграции Alembic..."
alembic upgrade head

echo "Запускаю приложение..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

