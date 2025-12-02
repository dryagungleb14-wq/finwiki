import os
import requests
import logging
import time
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
SLACK_API_KEY = os.getenv("SLACK_API_KEY")
API_URL = os.getenv("API_URL", "http://localhost:8000")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
slack_client = WebClient(token=SLACK_BOT_TOKEN)
signature_verifier = SignatureVerifier(SLACK_SIGNING_SECRET)

logger.info(f"Бот запущен. Backend URL: {API_URL}")
logger.info(f"API Key настроен: {'Да' if SLACK_API_KEY else 'Нет'}")

_bot_user_id = None

def get_bot_user_id():
    global _bot_user_id
    if _bot_user_id is None:
        _bot_user_id = slack_client.auth_test()["user_id"]
    return _bot_user_id

def request_with_retry(method, url, max_retries=2, **kwargs):
    """Выполняет HTTP запрос с повторами при сетевых ошибках"""
    logger.debug(f"Запрос {method} к {url}")
    
    for attempt in range(max_retries + 1):
        try:
            if method == "GET":
                response = requests.get(url, **kwargs)
            elif method == "POST":
                response = requests.post(url, **kwargs)
            else:
                logger.error(f"Неподдерживаемый метод: {method}")
                return None
            
            logger.info(f"Запрос {method} {url} - статус: {response.status_code}")
            if response.status_code != 200:
                logger.warning(f"Неуспешный статус {response.status_code} для {url}. Ответ: {response.text[:200]}")
            
            return response
            
        except requests.Timeout as e:
            error_msg = f"Timeout при запросе к {url} (попытка {attempt + 1}/{max_retries + 1})"
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.warning(f"{error_msg}. Повтор через {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"{error_msg}. Все попытки исчерпаны.")
                return None
                
        except requests.ConnectionError as e:
            error_msg = f"Ошибка соединения с {url} (попытка {attempt + 1}/{max_retries + 1}): {str(e)}"
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.warning(f"{error_msg}. Повтор через {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"{error_msg}. Все попытки исчерпаны.")
                return None
                
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запросе к {url}: {type(e).__name__}: {e}")
            return None
    
    return None

def handle_message(event):
    user_id = event.get("user")
    text = event.get("text", "").strip()
    channel = event.get("channel")

    if not text or not user_id or user_id == get_bot_user_id():
        return

    headers = {"X-API-Key": SLACK_API_KEY} if SLACK_API_KEY else {}

    try:
        logger.info(f"Обработка вопроса от {user_id}: {text[:100]}...")

        search_url = f"{API_URL}/api/slack/search"
        logger.info(f"Поиск ответа в БЗ: GET {search_url}")

        search_response = request_with_retry(
            "GET",
            search_url,
            params={"query": text},
            headers=headers,
            timeout=5
        )

        if search_response and search_response.status_code == 200:
            try:
                data = search_response.json()
                logger.info(f"Ответ от backend: found={data.get('found')}, call_manager={data.get('call_manager')}, confidence={data.get('confidence', 0.0)}")

                if data.get("found") and not data.get("call_manager"):
                    answer = data.get("answer", "")
                    confidence = data.get("confidence", 0.0)
                    message_text = f"**Вопрос:** {text}\n\n{answer}"
                    logger.info(f"Ответ найден (confidence: {confidence}) для {user_id}, отправляю ответ")
                    slack_client.chat_postMessage(
                        channel=channel,
                        text=message_text,
                        thread_ts=event.get("ts")
                    )
                    return
                elif data.get("call_manager"):
                    logger.info(f"AI не уверен в ответе (confidence: {data.get('confidence', 0.0)}), призываем менеджера для {user_id}")
                else:
                    logger.info(f"Ответ не найден в БЗ для вопроса: {text[:50]}")
            except Exception as json_error:
                logger.error(f"Ошибка парсинга JSON ответа от backend: {json_error}. Ответ: {search_response.text[:200]}")
        else:
            if search_response:
                logger.warning(f"Поиск не удался: статус {search_response.status_code}, ответ: {search_response.text[:200]}")
            else:
                logger.warning(f"Поиск не удался: нет ответа от backend (возможно, недоступен)")

        save_url = f"{API_URL}/api/slack/question"
        logger.info(f"Сохранение вопроса: POST {save_url}")

        save_response = request_with_retry(
            "POST",
            save_url,
            json={
                "question": text,
                "slack_user": user_id
            },
            headers=headers,
            timeout=5
        )

        if save_response and save_response.status_code == 200:
            try:
                save_data = save_response.json()
                logger.info(f"Вопрос успешно сохранён для {user_id}. ID: {save_data.get('id')}")
                message_text = f"**Вопрос:** {text}\n\nПока я не могу помочь с вашим вопросом. Но я передал его финансовому менеджеру. Пожалуйста, дождитесь ответа."
            except Exception as json_error:
                logger.warning(f"Ошибка парсинга JSON ответа при сохранении: {json_error}")
                message_text = f"**Вопрос:** {text}\n\nПока я не могу помочь с вашим вопросом. Но я передал его финансовому менеджеру. Пожалуйста, дождитесь ответа."
            
            try:
                slack_client.chat_postMessage(
                    channel=channel,
                    text=message_text,
                    thread_ts=event.get("ts")
                )
                logger.info(f"Сообщение отправлено пользователю {user_id}")
            except Exception as send_error:
                logger.error(f"Ошибка отправки сообщения в Slack: {send_error}")
        else:
            if save_response:
                error_detail = f"статус {save_response.status_code}"
                if save_response.text:
                    error_detail += f", ответ: {save_response.text[:200]}"
                logger.error(f"Не удалось сохранить вопрос: {error_detail}")
            else:
                logger.error(f"Не удалось сохранить вопрос: backend недоступен (нет ответа)")
            
            message_text = f"**Вопрос:** {text}\n\nИзвините, произошла техническая ошибка. Ваш вопрос не был сохранён. Пожалуйста, попробуйте позже или свяжитесь с финансовым менеджером напрямую."
            
            try:
                slack_client.chat_postMessage(
                    channel=channel,
                    text=message_text,
                    thread_ts=event.get("ts")
                )
            except Exception as send_error:
                logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")

    except Exception as e:
        logger.error(f"Критическая ошибка при обработке вопроса от {user_id}: {type(e).__name__}: {e}", exc_info=True)
        message_text = f"**Вопрос:** {text}\n\nИзвините, произошла техническая ошибка. Ваш вопрос не был обработан. Пожалуйста, попробуйте позже или свяжитесь с финансовым менеджером напрямую."
        try:
            slack_client.chat_postMessage(
                channel=channel,
                text=message_text,
                thread_ts=event.get("ts")
            )
        except Exception as send_error:
            logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.json
    
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})
    
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return jsonify({"error": "Invalid signature"}), 403
    
    if data.get("type") == "event_callback":
        event = data.get("event", {})
        event_type = event.get("type")
        
        if event_type == "app_mention":
            handle_message(event)
        elif event_type == "message" and event.get("channel_type") == "im":
            if event.get("subtype") is None:
                handle_message(event)
    
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    app.run(host="0.0.0.0", port=port)


