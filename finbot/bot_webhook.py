import os
import requests
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
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
        search_response = requests.get(
            f"{API_URL}/api/slack/search",
            params={"query": text},
            timeout=5
        )
        
        if search_response.status_code == 200:
            data = search_response.json()
            
            if data.get("found"):
                answer = data.get("answer", "")
                slack_client.chat_postMessage(
                    channel=channel,
                    text=answer
                )
            else:
                save_response = requests.post(
                    f"{API_URL}/api/slack/question",
                    json={
                        "question": text,
                        "slack_user": user_id
                    },
                    timeout=5
                )
                
                if save_response.status_code == 200:
                    slack_client.chat_postMessage(
                        channel=channel,
                        text="Финансовый менеджер ответит позже — ответ появится в базе знаний"
                    )
                else:
                    slack_client.chat_postMessage(
                        channel=channel,
                        text="Произошла ошибка. Попробуйте позже."
                    )
        else:
            slack_client.chat_postMessage(
                channel=channel,
                text="Произошла ошибка при поиске. Попробуйте позже."
            )
            
    except Exception as e:
        slack_client.chat_postMessage(
            channel=channel,
            text="Произошла ошибка. Попробуйте позже."
        )

@app.route("/slack/events", methods=["POST"])
def slack_events():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return jsonify({"error": "Invalid signature"}), 403
    
    data = request.json
    
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})
    
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


