import os
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_API_KEY = os.getenv("SLACK_API_KEY")
API_URL = os.getenv("API_URL", "http://localhost:8000")

app = App(token=SLACK_BOT_TOKEN)

@app.message("")
def handle_message(message, say):
    user_id = message.get("user")
    text = message.get("text", "").strip()
    
    if not text:
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
                say(text=message_text, thread_ts=message.get("ts"))
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
                    say(text=message_text, thread_ts=message.get("ts"))
                else:
                    message_text = f"**Вопрос:** {text}\n\nПроизошла ошибка. Попробуйте позже."
                    say(text=message_text, thread_ts=message.get("ts"))
        else:
            message_text = f"**Вопрос:** {text}\n\nПроизошла ошибка при поиске. Попробуйте позже."
            say(text=message_text, thread_ts=message.get("ts"))
            
    except Exception as e:
        message_text = f"**Вопрос:** {text}\n\nПроизошла ошибка. Попробуйте позже."
        say(text=message_text, thread_ts=message.get("ts"))

if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()

