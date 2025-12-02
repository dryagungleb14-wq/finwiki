import os
import requests
import logging
import time
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_API_KEY = os.getenv("SLACK_API_KEY")
API_URL = os.getenv("API_URL", "http://localhost:8000")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = App(token=SLACK_BOT_TOKEN)

def request_with_retry(method, url, max_retries=2, **kwargs):
    """Выполняет HTTP запрос с повторами при сетевых ошибках"""
    for attempt in range(max_retries + 1):
        try:
            if method == "GET":
                return requests.get(url, **kwargs)
            elif method == "POST":
                return requests.post(url, **kwargs)
        except (requests.Timeout, requests.ConnectionError) as e:
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.warning(f"Попытка {attempt + 1} не удалась: {type(e).__name__}. Повтор через {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Все попытки исчерпаны: {e}")
                raise
    return None

@app.message("")
def handle_message(message, say):
    user_id = message.get("user")
    text = message.get("text", "").strip()

    if not text:
        return

    headers = {"X-API-Key": SLACK_API_KEY} if SLACK_API_KEY else {}

    try:
        logger.info(f"Поиск ответа для вопроса от {user_id}: {text[:50]}...")

        search_response = request_with_retry(
            "GET",
            f"{API_URL}/api/slack/search",
            params={"query": text},
            headers=headers,
            timeout=5
        )

        if search_response and search_response.status_code == 200:
            data = search_response.json()

            if data.get("found") and not data.get("call_manager"):
                answer = data.get("answer", "")
                confidence = data.get("confidence", 0.0)
                message_text = f"**Вопрос:** {text}\n\n{answer}"
                logger.info(f"Ответ найден (confidence: {confidence}) для {user_id}")
                say(text=message_text, thread_ts=message.get("ts"))
                return
            elif data.get("call_manager"):
                logger.info(f"AI не уверен в ответе (confidence: {data.get('confidence', 0.0)}), призываем менеджера для {user_id}")
                pass

        # Ответ не найден или ошибка поиска - сохраняем вопрос
        logger.info(f"Ответ не найден, сохраняю вопрос для {user_id}...")

        save_response = request_with_retry(
            "POST",
            f"{API_URL}/api/slack/question",
            json={
                "question": text,
                "slack_user": user_id
            },
            headers=headers,
            timeout=5
        )

        if save_response and save_response.status_code == 200:
            message_text = f"**Вопрос:** {text}\n\nПока я не могу помочь с вашим вопросом. Но я передал его финансовому менеджеру. Пожалуйста, дождитесь ответа."
            logger.info(f"Вопрос сохранён для {user_id}")
            say(text=message_text, thread_ts=message.get("ts"))
        else:
            message_text = f"**Вопрос:** {text}\n\nВаш вопрос принят. Менеджер ответит позже."
            logger.warning(f"Не удалось сохранить вопрос (код: {save_response.status_code if save_response else 'нет ответа'}), но отправляю нейтральное сообщение")
            say(text=message_text, thread_ts=message.get("ts"))

    except Exception as e:
        logger.error(f"Ошибка при обработке вопроса от {user_id}: {e}", exc_info=True)
        message_text = f"**Вопрос:** {text}\n\nВаш вопрос принят. Менеджер ответит позже."
        try:
            say(text=message_text, thread_ts=message.get("ts"))
        except Exception as send_error:
            logger.error(f"Не удалось отправить сообщение: {send_error}")

if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()

