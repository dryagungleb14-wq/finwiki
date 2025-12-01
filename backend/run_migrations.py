#!/usr/bin/env python3
"""
Скрипт для запуска миграций базы данных Alembic.
Запускайте этот скрипт перед стартом приложения или при деплое.

Использование:
    python run_migrations.py
"""

import logging
from alembic.config import Config
from alembic import command
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migrations():
    """Применяет все pending миграции до последней версии"""
    try:
        logger.info("🔄 Запуск миграций Alembic...")
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("✅ Миграции успешно применены")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при применении миграций: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = run_migrations()
    sys.exit(0 if success else 1)
