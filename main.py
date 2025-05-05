import os
import tempfile
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
KEY_PATH = os.getenv("KEY_PATH", "key.json")

bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# Hàm gửi URL đến Google Indexing API
def submit_url_to_indexing(url):
    SCOPES = ["https://www.googleapis.com/auth/indexing"]
    credentials = service_account.Credentials.from_service_account_file(KEY_PATH, scopes=SCOPES)
    service = build("indexing", "v3", credentials=credentials)
    body = {"url": url, "type": "URL_UPDATED"}
    response = service.urlNotifications().publish(body=body).execute()
    return response

# Lệnh /submit
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

# Lệnh /submitall
def submitall(update, context):
    message_lines = update.message.text.split("\n")
    urls = message_lines[1:]  # Bỏ dòng đầu là /submitall

    if not urls:
        update.message.reply_text("❌ Bạn chưa nhập danh sách URL.")
        return

    errors = []
    success_count = 0

    for url in urls:
        url = url.strip()
        if not url:
            continue
        try:
            submit_url_to_indexing(url)
            success_count += 1
        except Exception as e:
            errors.append(f"❌ {url} – {str(e)}")

    reply_lines = []
    if success_count > 0:
        reply_lines.append(f"✅ Đã gửi thành công {success_count} URL.")
    if errors:
        reply_lines.append("\n".join(errors))

    update.message.reply_text("\n".join(reply_lines)[:4096])

# Xử lý file .txt
def handle_txt_file(update, context):
    document = update.message.document
    if not document.file_name.endswith(".txt"):
        update.message.reply_text("❌ Chỉ hỗ trợ file .txt chứa danh sách URL.")
        return

    file = document.get_file()
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        file.download(custom_path=tmp_file.name)
        tmp_file.seek(0)
        lines = tmp_file.read().decode("utf-8").splitlines()

    errors = []
    success_count = 0

    for url in lines:
        url = url.strip()
        if not url:
            continue
        try:
            submit_url_to_indexing(url)
            success_count += 1
        except Exception as e:
            errors.append(f"❌ {url} – {str(e)}")

    reply_lines = []
    if success_count > 0:
        reply_lines.append(f"✅ Đã gửi thành công {success_count} URL từ file.")
    if errors:
        reply_lines.append("\n".join(errors))

    update.message.reply_text("\n".join(reply_lines)[:4096])

# Gắn các handler
dispatcher.add_handler(CommandHandler("submit", submit))
dispatcher.add_handler(CommandHandler("submitall", submitall))
dispatcher.add_handler(MessageHandler(Filters.document.mime_type("text/plain"), handle_txt_file))

# Webhook endpoint
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
