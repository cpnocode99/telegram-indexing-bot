import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
KEY_PATH = os.getenv("KEY_PATH", "key.json")

bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

def submit_url_to_indexing(url):
    SCOPES = ["https://www.googleapis.com/auth/indexing"]
    credentials = service_account.Credentials.from_service_account_file(KEY_PATH, scopes=SCOPES)
    service = build("indexing", "v3", credentials=credentials)
    body = {"url": url, "type": "URL_UPDATED"}
    response = service.urlNotifications().publish(body=body).execute()
    return response

def submit(update, context):
    if len(context.args) != 1:
        update.message.reply_text("❌ Dùng đúng cú pháp: /submit https://your-url.com")
        return
    url = context.args[0]
    try:
        result = submit_url_to_indexing(url)
        update.message.reply_text(f"✅ Đã gửi URL: {url}\n📬 Phản hồi: {result}")
    except Exception as e:
        update.message.reply_text(f"❌ Lỗi: {str(e)}")

dispatcher.add_handler(CommandHandler("submit", submit))

@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

@app.route("/")
def home():
    return "Bot is running (Webhook mode)", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
