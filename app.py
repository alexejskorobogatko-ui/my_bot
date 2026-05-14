import os
import asyncio
import threading
from flask import Flask
from telethon import TelegramClient, events

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
    await client.start()
    print("✅ Telethon connected!", flush=True)
    me = await client.get_me()
    print(f"👹 Logged in as: {me.first_name} (@{me.username})", flush=True)
    
    # Регистрируем обработчик команд
    @client.on(events.NewMessage(outgoing=True))
    async def handler(event):
        msg = event.message.text
        if msg == '.ping':
            await event.edit("🏓 **pong!**")
            print("Command .ping executed", flush=True)
    
    await client.run_until_disconnected()

def run_bot():
    asyncio.run(main())

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    run_bot()
