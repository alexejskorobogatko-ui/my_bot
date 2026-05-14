import os
import asyncio
import threading
from flask import Flask
from telethon import TelegramClient

PHONE = os.environ.get("+16816004569")
API_ID = int(os.environ.get("API_ID", 30843796))
API_HASH = os.environ.get("API_HASH", '535bed75aaa17ed391bc11e1dac2cb21')

client = TelegramClient('session', API_ID, API_HASH)

async def main():
    await client.start(phone=PHONE)
    print("✅ Бот авторизован!")
    me = await client.get_me()
    print(f"👤 {me.first_name}")
    await client.run_until_disconnected()

app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is running", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

API_ID = 30843796
API_HASH = '535bed75aaa17ed391bc11e1dac2cb21'

client = TelegramClient('session', API_ID, API_HASH)

async def main():
    # Принудительно запрашиваем номер телефона и код в логах
    await client.start()
    print("✅ Бот успешно авторизован!")
    me = await client.get_me()
    print(f"👤 Имя: {me.first_name} (@{me.username})")
    await client.run_until_disconnected()

def run_bot():
    asyncio.run(main())

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    run_bot()
