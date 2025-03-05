from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent import process_chat

load_dotenv()

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
if not bot_token:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.json
    if 'message' in update:
        chat_id = update['message']['chat']['id']
        process_message(update['message'], chat_id)
    return jsonify({'status': 'OK'}), 200

def process_message(message, chat_id):
    if 'text' in message:
        user_input = message['text']
        print(f"Chat Id: {chat_id}")
        print(f"Received message: {user_input}")

        bot_response = process_chat(user_input)

        print(bot_response)
    else:
        print("Received a non-text message (e.g., file, image).")

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

def set_webhook(url):
    webhook_url = f'https://api.telegram.org/bot{bot_token}/setWebhook?url={url}'
    response = requests.get(webhook_url)
    return response.json()

if __name__ == '__main__':
    webhook_url = 'https://2937-106-51-65-235.ngrok-free.app/webhook'
    set_webhook(webhook_url)
    app.run(port=5000)
