import os
import asyncio
import threading
from flask import Flask
from telethon import TelegramClient

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
    await client.start() # Он уже НЕ спросит телефон, так как session.session есть
    print("✅ Бот запущен и авторизован!")
    me = await client.get_me()
    print(f"👤 Имя: {me.first_name} (@{me.username})")
    await client.run_until_disconnected()

def run_bot():
    asyncio.run(main())

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    run_bot()
