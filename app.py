# -*- coding: utf-8 -*-
import os
import sys
import time
import asyncio
import threading
from random import choice
from datetime import datetime, timedelta

import requests

from flask import Flask
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

# Windows fix
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ==================== ВЕБ-СЕРВЕР ДЛЯ RENDER ====================
web_app = Flask(__name__)

@web_app.route('/')
def health():
    return "Bot is running", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# ==================== ДАННЫЕ ДЛЯ АККАУНТА ====================
SESSION_NAME = 'session2'
API_ID = 30843796
API_HASH = '535bed75aaa17ed391bc11e1dac2cb21'

# ==================== ТЕКСТЫ ====================
menutext = """
╭───────❖ 𝐇𝐄𝐋𝐏 𝐌𝐄𝐍𝐔 ❖───────╮
│        ✦ {} ✦          │
╰──────────────────────────╯

┌───▸ 𝐎𝐒𝐍𝐎𝐕𝐍𝐘𝐄 𝐊𝐎𝐌𝐀𝐍𝐃𝐘
├ <code>.help</code> — главное меню
├ <code>.menu</code> — второе меню  
├ <code>.cmd</code> — полный список команд
├ <code>.id</code> — узнать ID чата/пользователя
├ <code>.ping</code> — пинг + аптайм
├ <code>.name</code> + текст — изменить имя бота
└ <code>.x0</code> + репл — загрузить медиа на хостинг

┌───▸ 𝐃𝐎𝐏𝐎𝐋𝐍𝐈𝐓𝐄𝐋𝐍𝐎
├ <code>.words</code> + репл — подсчёт слов/символов
├ <code>.load</code> + репл — смена шаблонов
└ <code>.file</code> — выгрузить текущий шаблон

┌───▸ 𝐈𝐍𝐅𝐎
├ Чат ID: <code>{}</code>
├ Ваш ID: <code>{}</code>
├ Ваше имя: <code>{}</code>
└ Username: @{}

╭───❖ 𝐎𝐖𝐍𝐄𝐑 ❖───╮
│  <a href='.'>@misosphere</a>  │
╰────────────────╯
"""

menu = """
╭───────❖ 𝐌𝐄𝐍𝐔 𝐂𝐎𝐌𝐀𝐍𝐃𝐒 ❖───────╮
│      дополнительное меню       │
╰───────────────────────────────╯

┌───▸ 𝐒𝐏𝐀𝐌 & 𝐓𝐄𝐆𝐆𝐄𝐑
├ <code>.avt</code> + время + реплай — спам в чат
├ <code>.stop [chat_id]</code> — остановить спам
├ <code>.tagger</code> + айди + время + реплай — теггер
└ <code>.off [chat_id]</code> — остановить теггер

┌───▸ 𝐊𝐀𝐋𝐄𝐍𝐃𝐀𝐑 (отложенный спам)
└ <code>.clr</code> + время + реплай — календарь

┌───▸ 𝐀𝐕𝐓𝐎𝐎𝐓𝐕𝐄𝐓𝐂𝐇𝐈𝐊
├ <code>.nrc [время] [медиа] [шапка]</code> + репл — включить
├ <code>.nrcc [id]</code> — выключить
├ <code>.rchange shapka [id] [текст]</code> — сменить шапку
├ <code>.rchange time [id] [секунды]</code> — сменить задержку
└ <code>.rchange media [id] [ссылка]</code> — сменить медиа

┌───▸ 𝐓𝐀𝐑𝐆𝐄𝐓
├ <code>.target [username/id]</code> — установить цель
└ <code>.tgoff</code> — отключить цель

╭───❖ 𝐎𝐖𝐍𝐄𝐑 ❖───╮
│  <a href='tg://user?id=472362019'>@misosphere</a>  │
╰────────────────╯
"""

commands_text = """
╔════════════════════════════════════════════════════════════╗
║                ✦ 𝐅𝐔𝐋𝐋 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒 𝐋𝐈𝐒𝐓 ✦                    ║
╚════════════════════════════════════════════════════════════╝

┌─── ❖ 𝐎𝐒𝐍𝐎𝐕𝐍𝐘𝐄 𝐊𝐎𝐌𝐀𝐍𝐃𝐘 ───
│ <code>.help</code> — главное меню
│ <code>.menu</code> — второе меню
│ <code>.cmd</code> — этот список команд
│ <code>.id</code> — узнать chat id / user id
│ <code>.ping</code> — пинг + аптайм бота
│ <code>.name</code> + текст — изменить имя бота
└────────────────────────────────────

┌─── ❖ 𝐀𝐕𝐓𝐎𝐎𝐓𝐕𝐄𝐓𝐂𝐇𝐈𝐊 ───
│ <code>.nrc [время] [медиа] [шапка]</code> + реплай — включить автоответ
│ <code>.nrcc [id]</code> — выключить автоответ
│ <code>.rchange shapka [id] [текст]</code> — сменить шапку
│ <code>.rchange time [id] [секунды]</code> — сменить задержку
│ <code>.rchange media [id] [ссылка]</code> — сменить медиа
└────────────────────────────────────

┌─── ❖ 𝐒𝐏𝐀𝐌 𝐕 𝐂𝐇𝐀𝐓𝐄 (reply) ───
│ <code>.avt [время] [медиа] [шапка]</code> + реплай — спам в чат
│ <code>.stop [chat_id]</code> — остановить спам
└────────────────────────────────────

┌─── ❖ 𝐊𝐀𝐋𝐄𝐍𝐃𝐀𝐑 (отложенный спам) ───
│ <code>.clr [время] [медиа] [шапка]</code> + реплай — календарь
└────────────────────────────────────

┌─── ❖ 𝐓𝐄𝐆𝐆𝐄𝐑 ───
│ <code>.tagger [user_id] [время] [медиа] [текст]</code> + реплай — теггер
│ <code>.off [chat_id]</code> — остановить tagger
└────────────────────────────────────

┌─── ❖ 𝐑𝐀𝐁𝐎𝐓𝐀 𝐒 𝐒𝐇𝐀𝐁𝐋𝐎𝐍𝐀𝐌𝐈 ───
│ <code>.load</code> + реплай на файл — загрузить свой шаблон
│ <code>.file</code> — выгрузить текущий шаблон
└────────────────────────────────────

┌─── ❖ 𝐇𝐎𝐒𝐓𝐈𝐍𝐆𝐈 ───
│ <code>.x0</code> + реплай на медиа — загрузить на x0.at
└────────────────────────────────────

┌─── ❖ 𝐃𝐄𝐓𝐄𝐊𝐓 ───
│ <code>.detect [@username/id]</code> или реплай — начать слежение
│ <code>.detectoff [@username/id]</code> или реплай — остановить
│ <code>.detectlist</code> — список активных детектов
└────────────────────────────────────

┌─── ❖ 𝐃𝐑𝐔𝐆𝐈𝐄 𝐊𝐎𝐌𝐀𝐍𝐃𝐘 ───
│ <code>.words</code> + реплай — подсчёт слов/символов
│ <code>.target [username/id]</code> — установить цель для авто-удаления
│ <code>.tgoff</code> — отключить цель (target)
└────────────────────────────────────

┌─── ❖ 𝐌𝐄𝐃𝐈𝐀 𝐃𝐋𝐘𝐀 𝐊𝐎𝐌𝐀𝐍𝐃 ───
│ <code>.help [ссылка]</code> — установить медиа для .help
│ <code>.menu [ссылка]</code> — установить медиа для .menu
│ <code>.cmd [ссылка]</code> — установить медиа для .cmd
│ <code>.id [ссылка]</code> — установить медиа для .id
└────────────────────────────────────

┌─── ❖ 𝐏𝐎𝐒𝐓 𝐊𝐎𝐌𝐀𝐍𝐃𝐘 ───
│ <code>.poste 'ссылка' минуты</code> — пересылка поста в чаты
│ <code>.poste_stop</code> — остановить все рассылки
│ <code>.poste_stop ссылка</code> — остановить по ссылке
│ <code>.poste_list</code> — список активных рассылок
│ <code>.pblk list</code> — список групп из блок-листа
│ <code>.pblk add id</code> / del id / clear — блок-лист пересылки
│ <code>.pblkclear</code> — полностью очистить весь pblk list
└────────────────────────────────────

┌─── ❖ 𝐒𝐈𝐒𝐓𝐄𝐌𝐍𝐘𝐄 𝐊𝐎𝐌𝐀𝐍𝐃𝐘 ───
│ <code>.status</code> — статус работы функций
│ <code>.zw</code> — остановить все функции
└────────────────────────────────────

╔════════════════════════════════════════════════════════════╗
║                    ✦ 𝐎𝐖𝐍𝐄𝐑: @misosphere ✦                  ║
╚════════════════════════════════════════════════════════════╝
"""

shablon = ["я тебе все ебало переломаю", "ты сын шлюхи ебаный", "ты давай отсоси мою залупу"]

# ==================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ====================
spam_state = {}
start_time = time.time()
autoreply_list = []
autoreply_time = {}
last_reply_time = {}
autoreply_photo = {}
autoreply_shpk = {}
tagger_chats = {}
mid = 'https://x0.at/cUQa.jpg'
name = "ебательный аппарат"
mh = 'https://x0.at/4JEh.jpeg'
mm = 'https://x0.at/4JEh.jpeg'
cmds = 'https://x0.at/Dv0D.jpg'

# ========== АВТО-ПИАР ==========
poste_list = {}
poste_blocklist = []

# ========== DETECT ==========
detect_list = {}

# ========== МЕДИА ДЛЯ НОВЫХ КОМАНД ==========
status_media = None

# ==================== КЛАСС ЮЗЕРБОТА ====================
class Userbot:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        self.target_user = None

    async def get_args(self, msg):
        try:
            text = msg.text if hasattr(msg, 'text') else msg.message.message
            return text.split(maxsplit=1)[1]
        except (IndexError, AttributeError):
            return None

    async def reply_with_media(self, msg, media_url, caption):
        if media_url:
            try:
                await self.client.send_file(msg.chat_id, media_url, caption=caption, parse_mode='html')
                await msg.delete()
            except Exception:
                await msg.edit(caption, parse_mode='html')
        else:
            await msg.edit(caption, parse_mode='html')

    async def get_entity_name(self, entity):
        try:
            if hasattr(entity, 'first_name'):
                name = entity.first_name or "None"
                if hasattr(entity, 'last_name') and entity.last_name:
                    name += f" {entity.last_name}"
                return name
            elif hasattr(entity, 'title'):
                return entity.title
            else:
                return str(entity.id)
        except:
            return str(entity.id)

    # ========== WATCHER ==========
    async def watcher(self, msg):
        user_id = msg.sender_id
        if user_id in autoreply_list:
            if user_id not in last_reply_time or time.time() - last_reply_time[user_id] >= autoreply_time[user_id]:
                last_reply_time[user_id] = time.time()
                await asyncio.sleep(autoreply_time[user_id])
                text = autoreply_shpk.get(user_id, '') + " " + choice(shablon) if autoreply_shpk.get(user_id) else choice(shablon)
                await msg.reply(text, file=autoreply_photo.get(user_id), parse_mode='html')
        
        # DETECT: если сообщение от отслеживаемого пользователя — сбрасываем таймер
        chat_id = msg.chat_id
        if chat_id in detect_list:
            user_id = msg.sender_id
            if user_id in detect_list[chat_id]:
                old_task = detect_list[chat_id][user_id].get('task')
                if old_task and not old_task.done():
                    old_task.cancel()
                user_name = detect_list[chat_id][user_id]['name']
                chat_name = await self.get_entity_name(await self.client.get_entity(chat_id))
                
                async def wait_and_notify():
                    await asyncio.sleep(3600)
                    try:
                        saved_messages = await self.client.get_entity('me')
                        await self.client.send_message(
                            saved_messages,
                            f"⛧ *Detect*\n\n"
                            f"⛧ *Пользователь:* {user_name}\n"
                            f"⛧ *Чат:* {chat_name}\n"
                            f"⛧ *Статус:* не писал 1 час"
                        )
                    except Exception as e:
                        print(f"Ошибка отправки уведомления: {e}")
                    if chat_id in detect_list and user_id in detect_list[chat_id]:
                        del detect_list[chat_id][user_id]
                        if not detect_list[chat_id]:
                            del detect_list[chat_id]
                
                task = asyncio.create_task(wait_and_notify())
                detect_list[chat_id][user_id]['task'] = task

    # ========== СПАМ ==========
    async def renewal_handler(self, msg):
        global spam_state
        args = await self.get_args(msg)
        if not args: return await msg.edit("<b>аргументы не указаны</b>", parse_mode='html')
        reply = await msg.get_reply_message()
        chat_id = msg.chat_id
        time_val = int(args.split()[0])
        if time_val < 3: return await msg.edit("<b>мин. задержка - 3</b>", parse_mode='html')
        photo = args.split()[1] if len(args.split()) > 1 and 'https' in args.split()[1] else None
        shapka_text = ' '.join(args.split()[2:]) if len(args.split()) > 2 else ''
        spam_state[chat_id] = True
        await msg.edit(f'<b>включен\nвыкл: <code>.stop {chat_id}</code></b>', parse_mode='html')
        while chat_id in spam_state and spam_state[chat_id]:
            try:
                if photo: await msg.respond(shapka_text + " " + choice(shablon), file=photo, reply_to=reply.id if reply else None)
                else: await msg.respond(shapka_text + " " + choice(shablon), reply_to=reply.id if reply else None)
            except Exception as e:
                if "TypeNotFoundError" in str(e) or "Constructor ID" in str(e):
                    pass
                elif "FloodWaitError" in str(e):
                    await asyncio.sleep(e.seconds)
                else:
                    print(f"Спам ошибка: {e}")
            await asyncio.sleep(time_val)
        if chat_id in spam_state: del spam_state[chat_id]

    # ========== АВТООТВЕТЧИК ==========
    async def autoreply_handler(self, msg):
        global autoreply_photo, autoreply_list, autoreply_time, autoreply_shpk
        args = msg.text.split()
        if not args: return
        cmd = args[0]
        if cmd == '.nrc':
            if msg.is_reply:
                user_id = (await msg.get_reply_message()).sender_id
                autoreply_list.append(user_id)
                autoreply_shpk[user_id] = ' '.join(args[1:])
                autoreply_time[user_id] = 1
                autoreply_photo[user_id] = None
                await msg.edit(f'<b>включен на <code>{user_id}</code>\nвыкл: <code>.nrcc</code></b>', parse_mode='html')
            else:
                user_id = int(args[1])
                autoreply_list.append(user_id)
                autoreply_time[user_id] = int(args[2])
                autoreply_photo[user_id] = args[3] if len(args) > 3 and 'https' in args[3] else None
                autoreply_shpk[user_id] = ' '.join(args[4:]) if len(args) > 4 else ''
                await msg.edit(f'<b>включен\nвыкл: <code>.nrcc {user_id}</code></b>', parse_mode='html')
        elif cmd == '.nrcc':
            if msg.is_reply: user_id = (await msg.get_reply_message()).sender_id
            else: user_id = int(args[1]) if len(args) > 1 else 0
            if user_id in autoreply_list:
                autoreply_list.remove(user_id)
                autoreply_time.pop(user_id, None)
                autoreply_photo.pop(user_id, None)
                autoreply_shpk.pop(user_id, None)
                await msg.edit(f'<b>выключен на <code>{user_id}</code></b>', parse_mode='html')

    # ========== КАЛЕНДАРЬ ==========
    async def kalendar_handler(self, msg):
        args = await self.get_args(msg)
        if not args: return await msg.edit("<b>аргументы: время медиа шапка</b>", parse_mode='html')
        parts = args.split()
        time_val = int(parts[0])
        photo = parts[1] if len(parts) > 1 and 'https' in parts[1] else None
        shapka_text = ' '.join(parts[2:]) if len(parts) > 2 else ''
        await msg.edit(f"{shapka_text} {choice(shablon)}", parse_mode='html')
        for i in range(100):
            schedule_date = datetime.now() + timedelta(minutes=time_val)
            await msg.respond(f"{shapka_text} {choice(shablon)}", file=photo, schedule=schedule_date.timestamp())
            await asyncio.sleep(0)

    # ========== ИЗМЕНЕНИЕ АРГУМЕНТОВ АВТООТВЕТЧИКА ==========
    async def rchange_handler(self, msg):
        global autoreply_photo, autoreply_time, autoreply_shpk
        args = msg.text.split()
        if len(args) < 4: return
        action = args[1]
        user_id = int(args[2])
        value = ' '.join(args[3:])
        if action == 'shapka':
            autoreply_shpk[user_id] = value
            await msg.edit(f'<b>шапка для {user_id} изменена</b>', parse_mode='html')
        elif action == 'media':
            autoreply_photo[user_id] = value if 'https' in value else None
            await msg.edit(f'<b>медиа для {user_id} изменено</b>', parse_mode='html')
        elif action == 'time':
            autoreply_time[user_id] = int(value)
            await msg.edit(f'<b>задержка для {user_id}: {autoreply_time[user_id]} сек</b>', parse_mode='html')

    # ========== ТЕГГЕР ==========
    async def tagger_handler(self, msg):
        args = msg.text.split(maxsplit=1)
        if len(args) < 2: return await msg.edit("<b>аргументы: user_id время [медиа] [текст]</b>", parse_mode='html')
        parts = args[1].split()
        if len(parts) < 2: return
        user_id = int(parts[0])
        time_val = int(parts[1])
        if time_val < 3: return await msg.edit("<b>мин. задержка - 3</b>", parse_mode='html')
        photo = parts[2] if len(parts) > 2 and 'https' in parts[2] else None
        caption = ' '.join(parts[3:]) if len(parts) > 3 else ''
        reply_to_msg = await msg.get_reply_message()
        chat_id = reply_to_msg.chat_id if reply_to_msg else msg.chat_id
        tagger_chats[chat_id] = True
        await msg.edit(f'<b>включен\nвыкл: <code>.off {chat_id}</code></b>', parse_mode='html')
        while chat_id in tagger_chats:
            text = f"{caption} <a href='tg://user?id={user_id}'>{choice(shablon)}</a>"
            try:
                if photo: await self.client.send_file(chat_id, photo, caption=text, parse_mode='html')
                else: await self.client.send_message(chat_id, text, parse_mode='html')
            except Exception as e:
                if "TypeNotFoundError" in str(e) or "Constructor ID" in str(e):
                    pass
                elif "FloodWaitError" in str(e):
                    await asyncio.sleep(e.seconds)
                else:
                    print(f"Теггер ошибка: {e}")
            await asyncio.sleep(time_val)
        if chat_id in tagger_chats: del tagger_chats[chat_id]

    # ========== ID ==========
    async def id_handler(self, msg):
        global mid
        try:
            if len(msg.text.split()) > 1 and msg.text.split()[1].startswith('http'):
                mid = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
                return await msg.edit("<b>медиа для .id установлено</b>", parse_mode='html')
            
            if msg.is_reply:
                reply_msg = await msg.get_reply_message()
                sender = await reply_msg.get_sender()
                if sender:
                    name = sender.first_name or "None"
                    if hasattr(sender, 'last_name') and sender.last_name:
                        name += f" {sender.last_name}"
                    user_id = sender.id
                    username = f"@{sender.username}" if sender.username else "нет username"
                    result = f"⛧ <b>Name:</b> {name}\n⛧ <b>ID:</b> <code>{user_id}</code>\n⛧ <b>Username:</b> {username}"
                else:
                    result = f"⛧ <b>Name:</b> Unknown\n⛧ <b>ID:</b> <code>unknown</code>\n⛧ <b>Username:</b> unknown"
                
                if mid:
                    await self.client.send_file(msg.chat_id, mid, caption=result, parse_mode='html')
                    await msg.delete()
                else:
                    await msg.edit(result, parse_mode='html')
                return
            
            if len(msg.text.split()) > 1 and msg.text.split()[1].startswith('@'):
                entity = await self.client.get_entity(msg.text.split()[1])
                name = getattr(entity, 'first_name', None) or getattr(entity, 'title', None) or "Unknown"
                if hasattr(entity, 'last_name') and entity.last_name:
                    name += f" {entity.last_name}"
                user_id = entity.id
                username = f"@{entity.username}" if hasattr(entity, 'username') and entity.username else "нет username"
                result = f"⛧ <b>Name:</b> {name}\n⛧ <b>ID:</b> <code>{user_id}</code>\n⛧ <b>Username:</b> {username}"
                
                if mid:
                    await self.client.send_file(msg.chat_id, mid, caption=result, parse_mode='html')
                    await msg.delete()
                else:
                    await msg.edit(result, parse_mode='html')
                return
            
            chat = await msg.get_chat()
            chat_title = chat.title if hasattr(chat, 'title') and chat.title else "Личный чат"
            chat_id = chat.id
            chat_username = f"@{chat.username}" if hasattr(chat, 'username') and chat.username else "нет username"
            result = f"⛧ <b>Name:</b> {chat_title}\n⛧ <b>ID:</b> <code>{chat_id}</code>\n⛧ <b>Username:</b> {chat_username}"
            
            if mid:
                await self.client.send_file(msg.chat_id, mid, caption=result, parse_mode='html')
                await msg.delete()
            else:
                await msg.edit(result, parse_mode='html')
                
        except Exception as e:
            await msg.edit(f"<b>ошибка: {e}</b>", parse_mode='html')

    # ========== СЧЁТ СЛОВ ==========
    async def words_handler(self, msg):
        if msg.is_reply:
            reply_msg = await msg.get_reply_message()
            words = reply_msg.text.split()
            total_words = len(words)
            total_chars = len(reply_msg.text)
            total_lines = reply_msg.text.count('\n') + 1
            result = f"<b>результат:</b>\nслов: {total_words}\nсимволов: {total_chars}\nстрок: {total_lines}"
            await msg.edit(result, parse_mode='html')

    # ========== ЗАГРУЗКА ШАБЛОНА ==========
    async def load_handler(self, msg):
        if msg.is_reply:
            reply_msg = await msg.get_reply_message()
            if reply_msg.file:
                file = await reply_msg.download_media()
                with open(file, 'r', encoding='utf-8') as f:
                    shablon.clear()
                    shablon.extend([line.strip() for line in f.readlines()])
                os.remove(file)
                await msg.edit("Успешно!")

    # ========== ВЫГРУЗКА ШАБЛОНА ==========
    async def file_handler(self, msg):
        with open('texts.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(shablon))
        await self.client.send_file(msg.chat_id, 'texts.txt')
        os.remove('texts.txt')
        await msg.delete()

    # ========== PING + UPTIME ==========
    async def ping_handler(self, msg):
        ping_start = time.perf_counter_ns()
        bot_runtime = int(time.time() - start_time)
        uptime_str = str(timedelta(seconds=bot_runtime))
        ping_ms = round((time.perf_counter_ns() - ping_start) / 10**6, 2)
        await msg.edit(f'<b>аптайм: <code>{uptime_str}</code>\nпинг: <code>{ping_ms} ms</code></b>', parse_mode='html')

    # ========== ОСТАНОВКА СПАМА ==========
    async def stop_handler(self, msg):
        global spam_state
        args = await self.get_args(msg)
        chat_id = int(args.split()[0]) if args else msg.chat_id
        if chat_id in spam_state: del spam_state[chat_id]
        await msg.edit(f"<b>остановлено в чате <code>{chat_id}</code></b>", parse_mode='html')

    async def off_handler(self, msg):
        global tagger_chats
        args = await self.get_args(msg)
        chat_id = int(args.split()[0]) if args else msg.chat_id
        if chat_id in tagger_chats: del tagger_chats[chat_id]
        await msg.edit(f"<b>остановлено в чате <code>{chat_id}</code></b>", parse_mode='html')

    async def target_handler(self, msg):
        args = await self.get_args(msg)
        if args:
            self.target_user = args.strip().replace('@', '')
            await msg.edit(f"цель: <code>{self.target_user}</code>", parse_mode='html')
        else: await msg.edit("<b>укажи юзернейм или ID</b>", parse_mode='html')

    async def tgoff_handler(self, msg):
        self.target_user = None
        await msg.edit("<b>цель (target) отключена</b>", parse_mode='html')

    # ========== HELP ==========
    async def help_handler(self, msg):
        global mh, name
        me = await self.client.get_me()
        if len(msg.text.split()) > 1:
            mh = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            return await msg.edit("<b>медиа для .help установлено</b>", parse_mode='html')
        caption = menutext.format(name, msg.chat_id, me.id, me.first_name, me.username)
        if mh:
            try:
                await self.client.send_file(msg.chat_id, mh, caption=caption, parse_mode='html')
                await msg.delete()
            except: await msg.edit(caption, parse_mode='html')
        else: await msg.edit(caption, parse_mode='html')

    # ========== MENU ==========
    async def menu_handler(self, msg):
        global mm
        if len(msg.text.split()) > 1:
            mm = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            return await msg.edit("<b>медиа для .menu установлено</b>", parse_mode='html')
        if mm:
            try:
                await self.client.send_file(msg.chat_id, mm, caption=menu, parse_mode='html')
                await msg.delete()
            except: await msg.edit(menu, parse_mode='html')
        else: await msg.edit(menu, parse_mode='html')

    # ========== CMD ==========
    async def cmd_handler(self, msg):
        global cmds
        if len(msg.text.split()) > 1:
            cmds = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            return await msg.edit("<b>медиа для .cmd установлено</b>", parse_mode='html')
        if cmds:
            try:
                await self.client.send_file(msg.chat_id, cmds, caption=commands_text, parse_mode='html')
                await msg.delete()
            except: await msg.edit(commands_text, parse_mode='html')
        else: await msg.edit(commands_text, parse_mode='html')

    # ========== X0 ==========
    async def x0_handler(self, msg):
        if not msg.is_reply:
            return await msg.edit("<b>нужен реплай на медиа</b>", parse_mode='html')
        
        reply_msg = await msg.get_reply_message()
        if not reply_msg.media:
            return await msg.edit("<b>нет медиа</b>", parse_mode='html')
        
        await msg.edit("<b>загружаю на x0.at...</b>", parse_mode='html')
        
        file = None
        try:
            file = await reply_msg.download_media()
            if not file:
                return await msg.edit("<b>не удалось скачать файл</b>", parse_mode='html')
            
            with open(file, 'rb') as f:
                response = requests.post(
                    'https://x0.at/',
                    files={'file': f},
                    timeout=60
                )
            
            if response.status_code == 200:
                link = response.text.strip()
                await msg.edit(f"<b>ссылка на x0.at:</b>\n<code>{link}</code>", parse_mode='html', link_preview=False)
            else:
                await msg.edit(f"<b>ошибка x0.at: {response.status_code}</b>", parse_mode='html')
                
        except requests.exceptions.Timeout:
            await msg.edit("<b>таймаут подключения. попробуй позже</b>", parse_mode='html')
        except Exception as e:
            await msg.edit(f"<b>ошибка: {e}</b>", parse_mode='html')
        finally:
            if file and os.path.exists(file):
                try:
                    os.remove(file)
                except:
                    pass

    # ========== NAME ==========
    async def name_handler(self, msg):
        global name
        args = await self.get_args(msg)
        if args:
            name = args
            await msg.edit(f'<b>имя бота изменено: {name}</b>', parse_mode='html')

    # ========== POST COMMANDS ==========
    async def poste_handler(self, msg):
        global poste_list, poste_blocklist
        args = await self.get_args(msg)
        if not args:
            return await msg.edit("<b>использование: .poste ссылка_на_пост минуты</b>", parse_mode='html')
        
        parts = args.split()
        if len(parts) < 2:
            return await msg.edit("<b>укажи ссылку на пост и интервал (минуты)</b>", parse_mode='html')
        
        link, interval = parts[0], parts[1]
        try:
            interval = int(interval)
        except ValueError:
            return await msg.edit("<b>интервал должен быть числом</b>", parse_mode='html')
        
        if interval < 1:
            return await msg.edit("<b>интервал не может быть меньше 1 минуты</b>", parse_mode='html')
        
        if link in poste_list:
            return await msg.edit(f"<b>рассылка для {link} уже запущена</b>", parse_mode='html')
        
        if not link.startswith("https://t.me/"):
            return await msg.edit("<b>ссылка должна быть на пост в Telegram (https://t.me/...)</b>", parse_mode='html')
        
        path = link.replace("https://t.me/", "").split("?")[0]
        parts_path = path.split("/")
        if len(parts_path) != 2:
            return await msg.edit("<b>неверный формат ссылки. нужно: https://t.me/username/12345</b>", parse_mode='html')
        
        chat_username, msg_id_str = parts_path[0], parts_path[1]
        try:
            msg_id = int(msg_id_str)
        except ValueError:
            return await msg.edit("<b>неверный ID сообщения в ссылке</b>", parse_mode='html')
        
        try:
            entity = await self.client.get_entity(chat_username)
        except Exception as e:
            return await msg.edit(f"<b>не удалось найти канал/чат {chat_username}. ошибка: {e}</b>", parse_mode='html')
        
        try:
            message = await self.client.get_messages(entity, ids=msg_id)
            if message is None:
                return await msg.edit(f"<b>не удалось найти сообщение {msg_id} в {chat_username}</b>", parse_mode='html')
        except Exception as e:
            return await msg.edit(f"<b>ошибка при получении сообщения: {e}</b>", parse_mode='html')
        
        dialogs = await self.client.get_dialogs()
        target_chats = []
        
        for d in dialogs:
            if d.is_channel and d.entity.broadcast:
                continue
            if d.is_user:
                continue
            if d.entity.id in poste_blocklist:
                continue
            target_chats.append(d.entity.id)
        
        if not target_chats:
            return await msg.edit("<b>нет доступных чатов для рассылки</b>", parse_mode='html')
        
        poste_list[link] = {
            'chats': target_chats,
            'interval': interval,
            'running': True,
            'entity': entity,
            'msg_id': msg_id
        }
        
        await msg.edit(f"<b>рассылка запущена\nссылка: {link}\nинтервал: {interval} мин\nчатов: {len(target_chats)}\nостановить: .poste_stop {link}</b>", parse_mode='html')
        asyncio.create_task(self._poste_worker(link))

    async def _poste_worker(self, link):
        global poste_list
        while poste_list.get(link, {}).get('running', False):
            data = poste_list[link]
            for chat_id in data['chats']:
                if not poste_list.get(link, {}).get('running', False):
                    break
                try:
                    await self.client.forward_messages(chat_id, messages=data['msg_id'], from_peer=data['entity'])
                    await asyncio.sleep(2)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                except Exception:
                    pass
            await asyncio.sleep(data['interval'] * 60)

    async def poste_stop_handler(self, msg):
        global poste_list
        args = await self.get_args(msg)
        if not args:
            for link in list(poste_list.keys()):
                poste_list[link]['running'] = False
            poste_list.clear()
            return await msg.edit("<b>все рассылки остановлены</b>", parse_mode='html')
        link = args.strip()
        if link in poste_list:
            poste_list[link]['running'] = False
            del poste_list[link]
            await msg.edit(f"<b>рассылка для {link} остановлена</b>", parse_mode='html')
        else: await msg.edit(f"<b>рассылка для {link} не найдена</b>", parse_mode='html')

    async def poste_list_handler(self, msg):
        if not poste_list: return await msg.edit("<b>активных рассылок нет</b>", parse_mode='html')
        lines = []
        for link, data in poste_list.items():
            lines.append(f"ссылка: {link}\n  чатов: {len(data['chats'])} интервал: {data['interval']} мин")
        await msg.edit("<b>активные рассылки:</b>\n" + "\n".join(lines), parse_mode='html')

    async def pblk_handler(self, msg):
        global poste_blocklist
        args = await self.get_args(msg)
        if not args: return await msg.edit("<b>использование: .pblk list|add id|del id|clear</b>", parse_mode='html')
        parts = args.split()
        action = parts[0].lower()
        
        if action == 'list':
            if not poste_blocklist:
                return await msg.edit("<b>блок-лист пуст</b>", parse_mode='html')
            lines = []
            for cid in poste_blocklist:
                try:
                    entity = await self.client.get_entity(cid)
                    name = entity.title if hasattr(entity, 'title') and entity.title else str(cid)
                    username = f" (@{entity.username})" if hasattr(entity, 'username') and entity.username else ""
                    lines.append(f"  {cid} - {name}{username}")
                except:
                    lines.append(f"  {cid}")
            await msg.edit("<b>блок-лист (чаты, куда НЕ отправлять):</b>\n" + "\n".join(lines), parse_mode='html')
        
        elif action == 'add':
            if len(parts) < 2:
                return await msg.edit("<b>укажи id чата или username</b>", parse_mode='html')
            target = parts[1]
            try:
                if target.isdigit():
                    chat_id = int(target)
                else:
                    entity = await self.client.get_entity(target)
                    chat_id = entity.id
                if chat_id not in poste_blocklist:
                    poste_blocklist.append(chat_id)
                await msg.edit(f"<b>чат {chat_id} добавлен в блок-лист</b>", parse_mode='html')
            except Exception as e:
                await msg.edit(f"<b>ошибка: {e}</b>", parse_mode='html')
        
        elif action == 'del':
            if len(parts) < 2:
                return await msg.edit("<b>укажи id чата</b>", parse_mode='html')
            target = parts[1]
            try:
                if target.isdigit():
                    chat_id = int(target)
                else:
                    entity = await self.client.get_entity(target)
                    chat_id = entity.id
                if chat_id in poste_blocklist:
                    poste_blocklist.remove(chat_id)
                await msg.edit(f"<b>чат {chat_id} удалён из блок-листа</b>", parse_mode='html')
            except Exception as e:
                await msg.edit(f"<b>ошибка: {e}</b>", parse_mode='html')
        
        elif action == 'clear':
            poste_blocklist.clear()
            await msg.edit("<b>блок-лист очищен</b>", parse_mode='html')
        
        else:
            await msg.edit("<b>неизвестное действие. доступно: list, add, del, clear</b>", parse_mode='html')

    async def pblkclear_handler(self, msg):
        global poste_blocklist
        poste_blocklist.clear()
        await msg.edit("<b>блок-лист полностью очищен</b>", parse_mode='html')

    # ========== STATUS ==========
    async def status_handler(self, msg):
        global status_media
        if len(msg.text.split()) > 1:
            status_media = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            return await msg.edit("<b>медиа для .status установлено</b>", parse_mode='html')
        
        me = await self.client.get_me()
        target_info = self.target_user if self.target_user else "не установлена"
        
        status_text = f"""
<bold>статус работы функций:</bold>

спам (avt): {len(spam_state)} активных
теггер (tagger): {len(tagger_chats)} активных
автоответчик: {len(autoreply_list)} пользователей
рассылки (poste): {len(poste_list)} активных
блок-лист (pblk): {len(poste_blocklist)} чатов
цель (target): {target_info}
детекты: {sum(len(v) for v in detect_list.values())} активных

--- аккаунт ---
имя: {me.first_name}
юзернейм: @{me.username}
айди: {me.id}
"""
        await self.reply_with_media(msg, status_media, status_text)

    # ========== DETECT ==========
    async def detect_handler(self, msg):
        global detect_list
        
        target_user = None
        
        if msg.is_reply:
            reply_msg = await msg.get_reply_message()
            target_user = await reply_msg.get_sender()
        else:
            args = await self.get_args(msg)
            if args:
                try:
                    target_user = await self.client.get_entity(args.strip())
                except:
                    return await msg.edit("⛧ *Ошибка:* не удалось найти пользователя")
            else:
                return await msg.edit("⛧ *Использование:* .detect [@username/id] или реплай на сообщение")
        
        if not target_user:
            return await msg.edit("⛧ *Ошибка:* не удалось определить пользователя")
        
        user_id = target_user.id
        user_name = await self.get_entity_name(target_user)
        chat_id = msg.chat_id
        chat_name = await self.get_entity_name(await msg.get_chat())
        
        if chat_id in detect_list and user_id in detect_list[chat_id]:
            old_task = detect_list[chat_id][user_id].get('task')
            if old_task and not old_task.done():
                old_task.cancel()
        
        async def wait_and_notify():
            await asyncio.sleep(3600)
            try:
                saved_messages = await self.client.get_entity('me')
                await self.client.send_message(
                    saved_messages,
                    f"⛧ *Detect*\n\n"
                    f"⛧ *Пользователь:* {user_name}\n"
                    f"⛧ *Чат:* {chat_name}\n"
                    f"⛧ *Статус:* не писал 1 час"
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления: {e}")
            if chat_id in detect_list and user_id in detect_list[chat_id]:
                del detect_list[chat_id][user_id]
                if not detect_list[chat_id]:
                    del detect_list[chat_id]
        
        task = asyncio.create_task(wait_and_notify())
        
        if chat_id not in detect_list:
            detect_list[chat_id] = {}
        detect_list[chat_id][user_id] = {
            'name': user_name,
            'task': task
        }
        
        await msg.edit(
            f"⛧ *Detect установлен*\n\n"
            f"⛧ *Пользователь:* {user_name}\n"
            f"⛧ *Чат:* {chat_name}\n"
            f"⛧ *Условие:* если не напишет 1 час — уведомлю в избранное"
        )

    async def detectoff_handler(self, msg):
        global detect_list
        
        target_user = None
        
        if msg.is_reply:
            reply_msg = await msg.get_reply_message()
            target_user = await reply_msg.get_sender()
        else:
            args = await self.get_args(msg)
            if args:
                try:
                    target_user = await self.client.get_entity(args.strip())
                except:
                    return await msg.edit("⛧ *Ошибка:* не удалось найти пользователя")
            else:
                return await msg.edit("⛧ *Использование:* .detectoff [@username/id] или реплай на сообщение")
        
        if not target_user:
            return await msg.edit("⛧ *Ошибка:* не удалось определить пользователя")
        
        user_id = target_user.id
        chat_id = msg.chat_id
        
        if chat_id in detect_list and user_id in detect_list[chat_id]:
            task = detect_list[chat_id][user_id].get('task')
            if task and not task.done():
                task.cancel()
            del detect_list[chat_id][user_id]
            if not detect_list[chat_id]:
                del detect_list[chat_id]
            await msg.edit(f"⛧ *Детект отключен* для пользователя {target_user.first_name or target_user.id}")
        else:
            await msg.edit("⛧ *Ошибка:* детект на этого пользователя не найден")

    async def detectlist_handler(self, msg):
        global detect_list
        
        if not detect_list:
            return await msg.edit("⛧ *Нет активных детектов*")
        
        lines = ["⛧ *Активные детекты:*\n"]
        for chat_id, users in detect_list.items():
            try:
                chat_entity = await self.client.get_entity(chat_id)
                chat_name = await self.get_entity_name(chat_entity)
            except:
                chat_name = str(chat_id)
            lines.append(f"*Чат:* {chat_name}")
            for user_id, data in users.items():
                lines.append(f"  • {data['name']} ({user_id})")
            lines.append("")
        
        await msg.edit("\n".join(lines))

    # ========== ОСТАНОВИТЬ ВСЕ ФУНКЦИИ ==========
    async def zw_handler(self, msg):
        global spam_state, tagger_chats, autoreply_list, poste_list, detect_list
        
        spam_state.clear()
        tagger_chats.clear()
        autoreply_list.clear()
        
        for link in list(poste_list.keys()):
            poste_list[link]['running'] = False
        poste_list.clear()
        
        for chat_id, users in detect_list.items():
            for user_id, data in users.items():
                task = data.get('task')
                if task and not task.done():
                    task.cancel()
        detect_list.clear()
        
        self.target_user = None
        
        await msg.edit("<bold>все функции остановлены</bold>", parse_mode='html')

    # ========== RUN ==========
    async def run(self):
        await self.client.start()
        print(f"Бот запущен! ({self.client.session.filename})", flush=True)
        me = await self.client.get_me()
        print(f"Имя: {me.first_name} (@{me.username})", flush=True)
        print("Команды загружены. Ожидание сообщений...", flush=True)

        @self.client.on(events.NewMessage)
        async def handler(event):
            msg = event.message
            if not msg.out:
                await self.watcher(msg)
                if self.target_user and not msg.out:
                    sender = await msg.get_sender()
                    if sender and (sender.username == self.target_user or str(sender.id) == self.target_user):
                        try: await msg.delete()
                        except: pass
                return
            text = msg.text or ""
            
            if text.startswith('.avt'): await self.renewal_handler(msg)
            elif text.startswith('.clr'): await self.kalendar_handler(msg)
            elif text.startswith('.nrc') or text.startswith('.nrcc') or text.startswith('.setshpk'): await self.autoreply_handler(msg)
            elif text.startswith('.rchange'): await self.rchange_handler(msg)
            elif text.startswith('.tagger'): await self.tagger_handler(msg)
            elif text.startswith('.stop'): await self.stop_handler(msg)
            elif text.startswith('.off'): await self.off_handler(msg)
            elif text.startswith('.id'): await self.id_handler(msg)
            elif text.startswith('.words'): await self.words_handler(msg)
            elif text.startswith('.load'): await self.load_handler(msg)
            elif text.startswith('.file'): await self.file_handler(msg)
            elif text.startswith('.ping'): await self.ping_handler(msg)
            elif text.startswith('.target'): await self.target_handler(msg)
            elif text.startswith('.tgoff'): await self.tgoff_handler(msg)
            elif text.startswith('.help'): await self.help_handler(msg)
            elif text.startswith('.menu'): await self.menu_handler(msg)
            elif text.startswith('.cmd'): await self.cmd_handler(msg)
            elif text.startswith('.x0'): await self.x0_handler(msg)
            elif text.startswith('.name'): await self.name_handler(msg)
            elif text.startswith('.poste ') and not text.startswith('.poste_stop') and not text.startswith('.poste_list'): await self.poste_handler(msg)
            elif text.startswith('.poste_stop'): await self.poste_stop_handler(msg)
            elif text.startswith('.poste_list'): await self.poste_list_handler(msg)
            elif text.startswith('.pblk '): await self.pblk_handler(msg)
            elif text.startswith('.pblkclear'): await self.pblkclear_handler(msg)
            elif text.startswith('.status'): await self.status_handler(msg)
            elif text.startswith('.zw'): await self.zw_handler(msg)
            elif text.startswith('.detect ') and not text.startswith('.detectoff') and not text.startswith('.detectlist'): await self.detect_handler(msg)
            elif text.startswith('.detectoff'): await self.detectoff_handler(msg)
            elif text.startswith('.detectlist'): await self.detectlist_handler(msg)

        await self.client.run_until_disconnected()

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot = Userbot()
    asyncio.run(bot.run())
