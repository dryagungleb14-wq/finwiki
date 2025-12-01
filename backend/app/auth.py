from fastapi import Header, HTTPException, Security
from fastapi.security import APIKeyHeader
import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
SLACK_API_KEY = os.getenv("SLACK_API_KEY")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_admin_key(api_key: str = Security(api_key_header)) -> str:
    """Проверка API ключа администратора"""
    if not ADMIN_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="ADMIN_API_KEY не настроен на сервере"
        )

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Отсутствует API ключ. Добавьте заголовок X-API-Key"
        )

    if api_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Неверный API ключ"
        )

    return api_key


async def verify_slack_key(api_key: str = Security(api_key_header)) -> str:
    """Проверка API ключа для Slack бота"""
    if not SLACK_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="SLACK_API_KEY не настроен на сервере"
        )

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Отсутствует API ключ. Добавьте заголовок X-API-Key"
        )

    if api_key != SLACK_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Неверный API ключ"
        )

    return api_key
