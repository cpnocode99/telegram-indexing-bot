import os
from telegram.ext import Updater, CommandHandler
from google.oauth2 import service_account
from googleapiclient.discovery import build

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
KEY_PATH = os.getenv("KEY_PATH", "key.json")

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

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("submit", submit))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
