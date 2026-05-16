# -*- coding: utf-8 -*-
import os
import sys
import time
import asyncio
import threading
from random import choice
from datetime import datetime, timedelta

import requests
import psutil

from flask import Flask
from telethon import TelegramClient, events
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.types import Channel
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
menutext = "<b>{}</b>\nвторой хелп - <code>.menu</code>\n\n остальные команды:\n<code>.words</code> + репл — количество слов в сообщении.\n<code>.load</code> + репл — смена шаблов бота.\n<code>.file</code> — основной шаблон бота.\n<code>.uptime</code> — аптайм.\n<code>.ping</code> — пинг.\n<code>.id</code> — узнать чат /юз айди\n<code>.x0</code> + репл — загрузить медию на хостинг\n\nthis chat id: <code>{}</code>\nyour user id: <code>{}</code>\nyour name: <code>{}</code>\nyour username: @{}</b>\nbot owner — <a href='.'>@misosphere</a></b>"

shablon = ["я тебе все ебало переломаю", "ты сын шлюхи ебаный", "ты давай отсоси мою залупу"]

menu = "первый хелп -  <code>.help</code>\n\n команды спам:\n<code>.tagger</code> + айди + время + скорость + реплай — спам-теггер.\n<code>.tag</code> + чат_айди + юз_айди + время + скорость — спам-теггер.\n<code>.off</code> / .tagoff + айди — остановка теггера.\n<code>.clr</code> + время + скорость + реплай — календарь.\n<code>.cal</code> + чат_айди + время + скорость — календарь.\n<code>.uchange</code> + [shapka,скорость,вреmя] + юз_айди — смена аргументов автоответчика.\n<code>.avt</code> + время + реплай\n<code>.target</code> + юз.\nовнер бота - <tg://user?id=472362019'>@misosphere</a>"

# ==================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ====================
afk_photo = ""
state = None
spam_state = {}
spam_state1 = {}
user_list = []
start_time = time.time()
autoreply_list = []
autoreply_time = {}
last_reply_time = {}
autoreply_photo = {}
autoreply_shpk = {}
start_timer = 10
tagger_chats = {}
tag_chats = {}
reason = "бот"
mid = 'https://x0.at/cUQa.jpg'
name = "ебательный аппарат"
mh = 'https://x0.at/4JEh.jpeg'
mm = 'https://x0.at/4JEh.jpeg'
cmds = 'https://x0.at/Dv0D.jpg'

# ========== МЕДИА КОМАНДЫ ==========
media_storage = {}
media_counter = 0

# ========== АВТО-ПИАР ==========
poste_list = {}
poste_blocklist = []

# ========== DETECT ==========
detect_list = {}

# ========== МЕДИА ДЛЯ НОВЫХ КОМАНД ==========
status_media = None
post_media = None
media_cmd_media = None

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
        global state, user_list, start_timer, reason, afk_photo
        if state is True:
            user_id = msg.sender_id
            if user_id not in user_list:
                if msg.is_private:
                    user_list.append(user_id)
                    time_now = datetime.now()
                    timing = time_now - start_timer
                    time_result = str(timing).split('.')[0]
                    await msg.reply(
                        f"я в AFK режиме <code>{time_result}</code>\nпричина: <code>{reason}</code>",
                        file=afk_photo,
                        parse_mode='html'
                    )
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

    # ========== AFK ==========
    async def afk_handler(self, msg):
        global state, user_list, start_timer, reason, afk_photo
        me = await self.client.get_me()
        if msg.sender_id != me.id: return
        args = msg.text.split()[1:]
        if not args:
            status = "включен" if state else "выключен"
            media = f"установлено медиа: <code>{afk_photo}</code>" if afk_photo else "медиа не было установлено"
            return await msg.edit(f"статус афк: <code>{status}</code>\n{media}\nпричина: <code>{reason}</code>", parse_mode='html')
        if args[0] == '1':
            state = True
            start_timer = datetime.now()
            me = await self.client.get_me()
            user_list.append(int(me.id))
            return await msg.edit("<b>afk включен.</b>", parse_mode='html')
        elif args[0] == '2':
            state = False
            start_timer = 10
            user_list = []
            return await msg.edit("<b>афк выключен</b>", parse_mode='html')
        elif 'https' in args[0]:
            afk_photo = args[0]
            return await msg.edit("<b>фото для афк изменено</b>", parse_mode='html')
        reason = ' '.join(args)
        await msg.edit(f'причина изменена: <code>{reason}</code>', parse_mode='html')

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

    async def spam_handler(self, msg):
        global spam_state1
        args = msg.text.split(maxsplit=1)
        if len(args) < 2: return await msg.edit("<b>укажи аргументы</b>", parse_mode='html')
        parts = args[1].split()
        if len(parts) < 2: return await msg.edit("<b>недостаточно аргументов</b>", parse_mode='html')
        chat_id = int(parts[0])
        time_val = int(parts[1])
        if time_val < 3: return await msg.edit("<b>мин. задержка - 3</b>", parse_mode='html')
        photo = parts[2] if len(parts) > 2 and 'https' in parts[2] else None
        shapka_text = ' '.join(parts[3:]) if len(parts) > 3 else ''
        spam_state1[chat_id] = True
        await msg.edit(f'<b>включен в чате {chat_id}\nвыкл: <code>.rstop {chat_id}</code></b>', parse_mode='html')
        while chat_id in spam_state1 and spam_state1[chat_id]:
            try:
                if photo: await self.client.send_file(chat_id, photo, caption=shapka_text + " " + choice(shablon))
                else: await self.client.send_message(chat_id, shapka_text + " " + choice(shablon))
            except Exception as e:
                if "TypeNotFoundError" in str(e) or "Constructor ID" in str(e):
                    pass
                elif "FloodWaitError" in str(e):
                    await asyncio.sleep(e.seconds)
                else:
                    print(f"Спам ошибка: {e}")
            await asyncio.sleep(time_val)
        if chat_id in spam_state1: del spam_state1[chat_id]

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

    # ========== ТЕГГЕРЫ ==========
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

    async def tag_handler(self, msg):
        args = msg.text.split(maxsplit=1)
        if len(args) < 2: return
        parts = args[1].split()
        if len(parts) < 3: return
        chat_id = int(parts[0])
        user_id = int(parts[1])
        time_val = int(parts[2])
        if time_val < 3: return await msg.edit("<b>мин. задержка - 3</b>", parse_mode='html')
        photo = parts[3] if len(parts) > 3 and 'https' in parts[3] else None
        caption = ' '.join(parts[4:]) if len(parts) > 4 else ''
        tag_chats[chat_id] = True
        await msg.edit(f'<b>включен\nвыкл: <code>.tagoff {chat_id}</code></b>', parse_mode='html')
        while chat_id in tag_chats:
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
        if chat_id in tag_chats: del tag_chats[chat_id]

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

    # ========== UPTIME ==========
    async def uptime_handler(self, msg):
        bot_runtime = int(time.time() - start_time)
        await msg.edit(f'аптайм бота: <code>{str(timedelta(seconds=bot_runtime))}</code>', parse_mode='html')

    # ========== PING ==========
    async def ping_handler(self, msg):
        ping_now = time.perf_counter_ns()
        await msg.edit(f'<b>пинг: <code>{round((time.perf_counter_ns() - ping_now) / 10**2, 2)} ms</code></b>', parse_mode='html')

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

    async def zstop_handler(self, msg):
        global spam_state1
        args = await self.get_args(msg)
        chat_id = int(args.split()[0]) if args else msg.chat_id
        if chat_id in spam_state1: del spam_state1[chat_id]
        await msg.edit(f"<b>остановлено в чате <code>{chat_id}</code></b>", parse_mode='html')

    async def tagoff_handler(self, msg):
        global tag_chats
        args = await self.get_args(msg)
        chat_id = int(args.split()[0]) if args else msg.chat_id
        if chat_id in tag_chats: del tag_chats[chat_id]
        await msg.edit(f"<b>остановлено в чате <code>{chat_id}</code></b>", parse_mode='html')

    async def target_handler(self, msg):
        args = await self.get_args(msg)
        if args:
            self.target_user = args.strip().replace('@', '')
            await msg.edit(f"цель: <code>{self.target_user}</code>", parse_mode='html')
        else: await msg.edit("<b>укажи юзернейм или ID</b>", parse_mode='html')

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
        
        commands_text = """
<bold>ПОЛНЫЙ СПИСОК КОМАНД:</bold>

<bold>ОСНОВНЫЕ КОМАНДЫ:</bold>
<code>.help</code> — главное меню
<code>.menu</code> — второе меню
<code>.cmd</code> — этот список команд
<code>.id</code> — узнать chat id / user id
<code>.ping</code> — проверить пинг бота
<code>.uptime</code> — аптайм бота
<code>.name</code> + текст — изменить имя бота

<bold>AFK РЕЖИМ:</bold>
<code>.afk 1</code> — включить AFK
<code>.afk 2</code> — выключить AFK
<code>.afk [причина]</code> — установить причину
<code>.afk [ссылка]</code> — установить медиа для AFK

<bold>АВТООТВЕТЧИК (на пользователя):</bold>
<code>.nrc [время] [медиа] [шапка]</code> + реплай — включить автоответ
<code>.nrcc [id]</code> — выключить автоответ
<code>.rchange shapka [id] [текст]</code> — сменить шапку
<code>.rchange time [id] [секунды]</code> — сменить задержку
<code>.rchange media [id] [ссылка]</code> — сменить медиа

<bold>СПАМ В ЧАТЕ (reply):</bold>
<code>.avt [время] [медиа] [шапка]</code> + реплай — спам в чат
<code>.stop [chat_id]</code> — остановить спам

<bold>СПАМ В ДРУГОЙ ЧАТ:</bold>
<code>.nzt [chat_id] [время] [медиа] [шапка]</code> — спам в другой чат
<code>.rstop [chat_id]</code> — остановить

<bold>КАЛЕНДАРЬ (отложенный спам):</bold>
<code>.clr [время] [медиа] [шапка]</code> + реплай — календарь
<code>.cal [chat_id] [время] [медиа] [шапка]</code> — календарь в другой чат

<bold>ТЕГГЕРЫ:</bold>
<code>.tagger [user_id] [время] [медиа] [текст]</code> + реплай — теггер
<code>.tag [chat_id] [user_id] [время] [медиа] [текст]</code> — теггер в другой чат
<code>.off [chat_id]</code> — остановить tagger
<code>.tagoff [chat_id]</code> — остановить tag

<bold>РАБОТА С ШАБЛОНАМИ:</bold>
<code>.load</code> + реплай на файл — загрузить свой шаблон
<code>.file</code> — выгрузить текущий шаблон

<bold>ХОСТИНГИ:</bold>
<code>.x0</code> + реплай на медиа — загрузить на x0.at

<bold>ДЕТЕКТ:</bold>
<code>.detect [@username/id]</code> или реплай — начать слежение
<code>.detectoff [@username/id]</code> или реплай — остановить слежение
<code>.detectlist</code> — список активных детектов

<bold>ДРУГИЕ КОМАНДЫ:</bold>
<code>.words</code> + реплай — подсчёт слов/символов
<code>.target [username/id]</code> — установить цель для авто-удаления

<bold>МЕДИА ДЛЯ КОМАНД:</bold>
<code>.help [ссылка]</code> — установить медиа для .help
<code>.menu [ссылка]</code> — установить медиа для .menu
<code>.cmd [ссылка]</code> — установить медиа для .cmd
<code>.id [ссылка]</code> — установить медиа для .id

<bold>МЕДИА КОМАНДЫ:</bold>
<code>.pfl [имя]</code> — ответом на фото, видео или m4a скачать и сделать активным
<code>.phocount</code> — сколько всего медиа скачано
<code>.pholist</code> — список медиа и активное
<code>.phoset номер|имя 1|2</code> — поменять активное медиа (1=основное, 2=hntd)
<code>.resetm 1|2</code> — сбросить выбранное медиа на фото профиля
<code>.phoren старый новый</code> — переименовать номер медиа
<code>.phodel номер|имя</code> — удалить медиа

<bold>POST КОМАНДЫ:</bold>
<code>.poste 'ссылка' минуты</code> — пересылка поста в чаты (кроме каналов и ЛС)
<code>.poste_stop</code> — остановить все рассылки
<code>.poste_stop ссылка</code> — остановить по ссылке
<code>.poste_list</code> — список активных рассылок
<code>.pblk list</code> — список групп из блок-листа
<code>.pblk add id</code> / del id / clear — блок-лист пересылки
<code>.pblkclear</code> — полностью очистить весь pblk list

<bold>СИСТЕМНЫЕ КОМАНДЫ:</bold>
<code>.status</code> — статус работы функций
<code>.zw</code> — остановить все функции
"""
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

    # ========== MEDIA COMMANDS ==========
    async def pfl_handler(self, msg):
        global media_storage, media_counter
        args = await self.get_args(msg)
        if not msg.is_reply: return await msg.edit("<b>нужен ответ на фото, видео или аудио</b>", parse_mode='html')
        reply = await msg.get_reply_message()
        if not reply.media: return await msg.edit("<b>в ответе нет медиа</b>", parse_mode='html')
        name = args if args else f"media_{media_counter+1}"
        try:
            file_data = await reply.download_media(bytes)
            media_type = "photo"
            if hasattr(reply.media, 'video') and reply.media.video: media_type = "video"
            elif hasattr(reply.media, 'audio') and reply.media.audio: media_type = "audio"
            elif hasattr(reply.media, 'document') and reply.media.document:
                mime = reply.media.document.mime_type
                if 'video' in mime: media_type = "video"
                elif 'audio' in mime: media_type = "audio"
                else: media_type = "document"
            media_storage[name] = {'data': file_data, 'type': media_type, 'active_1': False, 'active_2': False}
            media_counter += 1
            await msg.edit(f"<b>медиа сохранено как {name} (тип: {media_type})</b>", parse_mode='html')
        except Exception as e: await msg.edit(f"<b>ошибка при сохранении: {e}</b>", parse_mode='html')

    async def phocount_handler(self, msg): await msg.edit(f"<b>всего медиа скачано: {media_counter}</b>", parse_mode='html')
    
    async def pholist_handler(self, msg):
        if not media_storage: return await msg.edit("<b>нет сохранённых медиа</b>", parse_mode='html')
        lines = []
        for idx, (name, data) in enumerate(media_storage.items(), 1):
            active1 = "+" if data.get('active_1') else "-"
            active2 = "+" if data.get('active_2') else "-"
            lines.append(f"{idx}. {name} [осн:{active1} hntd:{active2}] ({data['type']})")
        await msg.edit("<b>список медиа:</b>\n" + "\n".join(lines), parse_mode='html')

    async def phoset_handler(self, msg):
        global media_storage
        args = await self.get_args(msg)
        if not args: return await msg.edit("<b>использование: .phoset номер|имя 1|2</b>", parse_mode='html')
        parts = args.split()
        if len(parts) < 2: return await msg.edit("<b>укажи имя/номер и тип (1 или 2)</b>", parse_mode='html')
        target, target_type = parts[0], parts[1]
        if target_type not in ['1', '2']: return await msg.edit("<b>тип должен быть 1 (основное) или 2 (hntd)</b>", parse_mode='html')
        found = None
        if target.isdigit():
            idx = int(target)-1
            names = list(media_storage.keys())
            if 0 <= idx < len(names): found = names[idx]
        elif target in media_storage: found = target
        if not found: return await msg.edit(f"<b>медиа '{target}' не найдено</b>", parse_mode='html')
        for name, data in media_storage.items():
            if target_type == '1': data['active_1'] = (name == found)
            else: data['active_2'] = (name == found)
        await msg.edit(f"<b>активное {'основное' if target_type=='1' else 'hntd'} медиа: {found}</b>", parse_mode='html')

    async def resetm_handler(self, msg):
        global media_storage
        args = await self.get_args(msg)
        target_type = args if args else "1"
        if target_type not in ['1', '2']: return await msg.edit("<b>тип должен быть 1 (основное) или 2 (hntd)</b>", parse_mode='html')
        for data in media_storage.values():
            if target_type == '1': data['active_1'] = False
            else: data['active_2'] = False
        await msg.edit(f"<b>активное {'основное' if target_type=='1' else 'hntd'} медиа сброшено на фото профиля</b>", parse_mode='html')

    async def phoren_handler(self, msg):
        global media_storage
        args = await self.get_args(msg)
        if not args: return await msg.edit("<b>использование: .phoren старый новый</b>", parse_mode='html')
        parts = args.split()
        if len(parts) < 2: return await msg.edit("<b>укажи старое и новое имя</b>", parse_mode='html')
        old_name, new_name = parts[0], parts[1]
        if old_name not in media_storage: return await msg.edit(f"<b>медиа '{old_name}' не найдено</b>", parse_mode='html')
        if new_name in media_storage: return await msg.edit(f"<b>медиа '{new_name}' уже существует</b>", parse_mode='html')
        media_storage[new_name] = media_storage.pop(old_name)
        await msg.edit(f"<b>медиа переименовано: {old_name} -> {new_name}</b>", parse_mode='html')

    async def phodel_handler(self, msg):
        global media_storage, media_counter
        args = await self.get_args(msg)
        if not args: return await msg.edit("<b>использование: .phodel номер|имя</b>", parse_mode='html')
        target = args.strip()
        found = None
        if target.isdigit():
            idx = int(target)-1
            names = list(media_storage.keys())
            if 0 <= idx < len(names): found = names[idx]
        elif target in media_storage: found = target
        if not found: return await msg.edit(f"<b>медиа '{target}' не найдено</b>", parse_mode='html')
        del media_storage[found]
        media_counter = len(media_storage)
        await msg.edit(f"<b>медиа '{found}' удалено</b>", parse_mode='html')

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
спам (nzt): {len(spam_state1)} активных
теггер (tagger): {len(tagger_chats)} активных
теггер (tag): {len(tag_chats)} активных
автоответчик: {len(autoreply_list)} пользователей
рассылки (poste): {len(poste_list)} активных
блок-лист (pblk): {len(poste_blocklist)} чатов
AFK: {'включен' if state else 'выключен'}
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
        global spam_state, spam_state1, tagger_chats, tag_chats, autoreply_list, poste_list, state, user_list, start_timer, reason, afk_photo, detect_list
        
        spam_state.clear()
        spam_state1.clear()
        tagger_chats.clear()
        tag_chats.clear()
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
        
        state = False
        user_list = []
        start_timer = 10
        reason = "бот"
        afk_photo = ""
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
            
            if text.startswith('.afk'): await self.afk_handler(msg)
            elif text.startswith('.avt'): await self.renewal_handler(msg)
            elif text.startswith('.nzt'): await self.spam_handler(msg)
            elif text.startswith('.clr'): await self.kalendar_handler(msg)
            elif text.startswith('.nrc') or text.startswith('.nrcc') or text.startswith('.setshpk'): await self.autoreply_handler(msg)
            elif text.startswith('.rchange'): await self.rchange_handler(msg)
            elif text.startswith('.tagger'): await self.tagger_handler(msg)
            elif text.startswith('.tag ') and not text.startswith('.tagoff'): await self.tag_handler(msg)
            elif text.startswith('.tagoff'): await self.tagoff_handler(msg)
            elif text.startswith('.stop'): await self.stop_handler(msg)
            elif text.startswith('.off'): await self.off_handler(msg)
            elif text.startswith('.zstop'): await self.zstop_handler(msg)
            elif text.startswith('.id'): await self.id_handler(msg)
            elif text.startswith('.words'): await self.words_handler(msg)
            elif text.startswith('.load'): await self.load_handler(msg)
            elif text.startswith('.file'): await self.file_handler(msg)
            elif text.startswith('.uptime'): await self.uptime_handler(msg)
            elif text.startswith('.ping'): await self.ping_handler(msg)
            elif text.startswith('.target'): await self.target_handler(msg)
            elif text.startswith('.help'): await self.help_handler(msg)
            elif text.startswith('.menu'): await self.menu_handler(msg)
            elif text.startswith('.cmd'): await self.cmd_handler(msg)
            elif text.startswith('.x0'): await self.x0_handler(msg)
            elif text.startswith('.name'): await self.name_handler(msg)
            elif text.startswith('.pfl'): await self.pfl_handler(msg)
            elif text.startswith('.phocount'): await self.phocount_handler(msg)
            elif text.startswith('.pholist'): await self.pholist_handler(msg)
            elif text.startswith('.phoset'): await self.phoset_handler(msg)
            elif text.startswith('.resetm'): await self.resetm_handler(msg)
            elif text.startswith('.phoren'): await self.phoren_handler(msg)
            elif text.startswith('.phodel'): await self.phodel_handler(msg)
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
