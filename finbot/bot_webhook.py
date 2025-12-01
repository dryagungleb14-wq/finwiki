import os
import requests
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
SLACK_API_KEY = os.getenv("SLACK_API_KEY")
API_URL = os.getenv("API_URL", "http://localhost:8000")

app = Flask(__name__)
slack_client = WebClient(token=SLACK_BOT_TOKEN)
signature_verifier = SignatureVerifier(SLACK_SIGNING_SECRET)

_bot_user_id = None

def get_bot_user_id():
    global _bot_user_id
    if _bot_user_id is None:
        _bot_user_id = slack_client.auth_test()["user_id"]
    return _bot_user_id

def handle_message(event):
    user_id = event.get("user")
    text = event.get("text", "").strip()
    channel = event.get("channel")
    
    if not text or not user_id or user_id == get_bot_user_id():
        return
    
    try:
        headers = {"X-API-Key": SLACK_API_KEY} if SLACK_API_KEY else {}
        search_response = requests.get(
            f"{API_URL}/api/slack/search",
            params={"query": text},
            headers=headers,
            timeout=5
        )
        
        if search_response.status_code == 200:
            data = search_response.json()
            
            if data.get("found"):
                answer = data.get("answer", "")
                message_text = f"**Вопрос:** {text}\n\n{answer}"
                slack_client.chat_postMessage(
                    channel=channel,
                    text=message_text,
                    thread_ts=event.get("ts")
                )
            else:
                save_response = requests.post(
                    f"{API_URL}/api/slack/question",
                    json={
                        "question": text,
                        "slack_user": user_id
                    },
                    headers=headers,
                    timeout=5
                )
                
                if save_response.status_code == 200:
                    message_text = f"**Вопрос:** {text}\n\nПока я не могу помочь с вашим вопросом. Но я передал его финансовому менеджеру. Пожалуйста, дождитесь ответа."
                    slack_client.chat_postMessage(
                        channel=channel,
                        text=message_text,
                        thread_ts=event.get("ts")
                    )
                else:
                    message_text = f"**Вопрос:** {text}\n\nПроизошла ошибка. Попробуйте позже."
                    slack_client.chat_postMessage(
                        channel=channel,
                        text=message_text,
                        thread_ts=event.get("ts")
                    )
        else:
            message_text = f"**Вопрос:** {text}\n\nПроизошла ошибка при поиске. Попробуйте позже."
            slack_client.chat_postMessage(
                channel=channel,
                text=message_text,
                thread_ts=event.get("ts")
            )
            
    except Exception as e:
        message_text = f"**Вопрос:** {text}\n\nПроизошла ошибка. Попробуйте позже."
        slack_client.chat_postMessage(
            channel=channel,
            text=message_text,
            thread_ts=event.get("ts")
        )

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


