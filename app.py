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
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import InputPhoneContact
from telethon.tl.functions.contacts import ImportContactsRequest

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

# ==================== ДАННЫЕ ДЛЯ ДВУХ АККАУНТОВ ====================

# Аккаунт 1: Мерцифал
ACCOUNT1_SESSION = 'session'
ACCOUNT1_API_ID = 30843796
ACCOUNT1_API_HASH = '535bed75aaa17ed391bc11e1dac2cb21'

# Аккаунт 2: Ralvatron
ACCOUNT2_SESSION = 'session2'
ACCOUNT2_API_ID = 30843796
ACCOUNT2_API_HASH = '535bed75aaa17ed391bc11e1dac2cb21'

# ==================== ТЕКСТЫ ====================
menutext = "<b>{}</b>\nвторой хелп - <code>.menu</code>\n\n остальные команды:\n<code>.list</code> + медия — список работы бота.\n<code>.help</code> + медия — mеnю.\n<code>.menu</code> — второе меню.\n<code>.words</code> + репл — количество слов в сообщении.\n<code>.load</code> + репл — смена шаблов бота.\n<code>.file</code> — основной шаблон бота.\n<code>.uptime</code> — аптайм.\n<code>.ping</code> — пинг.\n<code>.id</code> — узнать чат /юз айди\n<code>.x0</code> + репл — загрузить медию на хостинг\n\nthis chat id: <code>{}</code>\nyour user id: <code>{}</code>\nyour name: <code>{}</code>\nyour username: @{}</b>\nbot owner — <a href='.'>@misosphere</a></b>"

shablon = ["я тебе все ебало переломаю", "ты сын шлюхи ебаный", "ты давай отсоси мою залупу"]

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
name = " ебательный аппарат "
menu = "первый хелп -  <code>.help</code>\n\n команды спам:\n<code>.tagger</code> + айди + время + скорость + реплай — спам-теггер.\n<code>.tag</code> + чат_айди + юз_айди + время + скорость — спам-теггер.\n<code>.off</code> / .tagoff + айди — остановка теггера.\n<code>.clr</code> + время + скорость + реплай — календарь.\n<code>.cal</code> + чат_айди + время + скорость — календарь.\n<code>.uchange</code> + [shapka,скорость,вреmя] + юз_айди — смена аргументов автоответчика.\n<code>.avt</code> + время + реплай\n<code>.target</code> + юз.\n<code>.farm</code> | хелп фарма.\n\овнер бота - <tg://user?id=472362019'>@misosphere</a>"
mh = 'https://x0.at/4JEh.jpeg'
mm = 'https://x0.at/4JEh.jpeg'
mlist = 'https://x0.at/Dv0D.jpg'
cmds = 'https://x0.at/Dv0D.jpg'

# ==================== МЕДИА КОМАНДЫ ====================
media_storage = {}
media_counter = 0

# ==================== АВТО-ПИАР ====================
poste_list = {}
poste_blocklist = []

# ==================== КЛАСС ЮЗЕРБОТА ====================
class Userbot:
    def __init__(self, session_name, api_id, api_hash):
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.droch_active = False
        self.pharma_active = False
        self.target_user = None

    async def get_args(self, msg):
        try:
            text = msg.text if hasattr(msg, 'text') else msg.message.message
            return text.split(maxsplit=1)[1]
        except (IndexError, AttributeError):
            return None

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

    # ========== AFK ==========
    async def afk_handler(self, msg):
        global state, user_list, start_timer, reason, afk_photo
        me = await self.client.get_me()
        if msg.sender_id != me.id:
            return
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
        if not args:
            return await msg.edit("<b>аргументы не указаны</b>", parse_mode='html')
        reply = await msg.get_reply_message()
        chat_id = msg.chat_id
        time_val = int(args.split()[0])
        if time_val < 3:
            return await msg.edit("<b>мин. задержка - 3</b>", parse_mode='html')
        photo = args.split()[1] if len(args.split()) > 1 and 'https' in args.split()[1] else None
        shapka_text = ' '.join(args.split()[2:]) if len(args.split()) > 2 else ''
        spam_state[chat_id] = True
        await msg.edit(f'<b>включен\nвыкл: <code>.stop {chat_id}</code></b>', parse_mode='html')
        while chat_id in spam_state and spam_state[chat_id]:
            try:
                if photo:
                    await msg.respond(shapka_text + " " + choice(shablon), file=photo, reply_to=reply.id if reply else None)
                else:
                    await msg.respond(shapka_text + " " + choice(shablon), reply_to=reply.id if reply else None)
            except:
                pass
            await asyncio.sleep(time_val)
        if chat_id in spam_state:
            del spam_state[chat_id]

    async def spam_handler(self, msg):
        global spam_state1
        args = msg.text.split(maxsplit=1)
        if len(args) < 2:
            return await msg.edit("<b>укажи аргументы</b>", parse_mode='html')
        parts = args[1].split()
        if len(parts) < 2:
            return await msg.edit("<b>недостаточно аргументов</b>", parse_mode='html')
        chat_id = int(parts[0])
        time_val = int(parts[1])
        if time_val < 3:
            return await msg.edit("<b>мин. задержка - 3</b>", parse_mode='html')
        photo = parts[2] if len(parts) > 2 and 'https' in parts[2] else None
        shapka_text = ' '.join(parts[3:]) if len(parts) > 3 else ''
        spam_state1[chat_id] = True
        await msg.edit(f'<b>включен в чате {chat_id}\nвыкл: <code>.rstop {chat_id}</code></b>', parse_mode='html')
        while chat_id in spam_state1 and spam_state1[chat_id]:
            try:
                if photo:
                    await self.client.send_file(chat_id, photo, caption=shapka_text + " " + choice(shablon))
                else:
                    await self.client.send_message(chat_id, shapka_text + " " + choice(shablon))
            except:
                pass
            await asyncio.sleep(time_val)
        if chat_id in spam_state1:
            del spam_state1[chat_id]

    # ========== АВТООТВЕТЧИК ==========
    async def autoreply_handler(self, msg):
        global autoreply_photo, autoreply_list, autoreply_time, autoreply_shpk
        args = msg.text.split()
        if not args:
            return
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
            if msg.is_reply:
                user_id = (await msg.get_reply_message()).sender_id
            else:
                user_id = int(args[1]) if len(args) > 1 else 0
            if user_id in autoreply_list:
                autoreply_list.remove(user_id)
                autoreply_time.pop(user_id, None)
                autoreply_photo.pop(user_id, None)
                autoreply_shpk.pop(user_id, None)
                await msg.edit(f'<b>выключен на <code>{user_id}</code></b>', parse_mode='html')

    # ========== КАЛЕНДАРЬ ==========
    async def kalendar_handler(self, msg):
        args = await self.get_args(msg)
        if not args:
            return await msg.edit("<b>аргументы: время медиа шапка</b>", parse_mode='html')
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
        if len(args) < 4:
            return
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
        if len(args) < 2:
            return await msg.edit("<b>аргументы: user_id время [медиа] [текст]</b>", parse_mode='html')
        parts = args[1].split()
        if len(parts) < 2:
            return
        user_id = int(parts[0])
        time_val = int(parts[1])
        if time_val < 3:
            return await msg.edit("<b>мин. задержка - 3</b>", parse_mode='html')
        photo = parts[2] if len(parts) > 2 and 'https' in parts[2] else None
        caption = ' '.join(parts[3:]) if len(parts) > 3 else ''
        reply_to_msg = await msg.get_reply_message()
        chat_id = reply_to_msg.chat_id if reply_to_msg else msg.chat_id
        tagger_chats[chat_id] = True
        await msg.edit(f'<b>включен\nвыкл: <code>.off {chat_id}</code></b>', parse_mode='html')
        while chat_id in tagger_chats:
            text = f"{caption} <a href='tg://user?id={user_id}'>{choice(shablon)}</a>"
            try:
                if photo:
                    await self.client.send_file(chat_id, photo, caption=text, parse_mode='html')
                else:
                    await self.client.send_message(chat_id, text, parse_mode='html')
            except:
                pass
            await asyncio.sleep(time_val)
        if chat_id in tagger_chats:
            del tagger_chats[chat_id]

    async def tag_handler(self, msg):
        args = msg.text.split(maxsplit=1)
        if len(args) < 2:
            return
        parts = args[1].split()
        if len(parts) < 3:
            return
        chat_id = int(parts[0])
        user_id = int(parts[1])
        time_val = int(parts[2])
        if time_val < 3:
            return await msg.edit("<b>мин. задержка - 3</b>", parse_mode='html')
        photo = parts[3] if len(parts) > 3 and 'https' in parts[3] else None
        caption = ' '.join(parts[4:]) if len(parts) > 4 else ''
        tag_chats[chat_id] = True
        await msg.edit(f'<b>включен\nвыкл: <code>.tagoff {chat_id}</code></b>', parse_mode='html')
        while chat_id in tag_chats:
            text = f"{caption} <a href='tg://user?id={user_id}'>{choice(shablon)}</a>"
            try:
                if photo:
                    await self.client.send_file(chat_id, photo, caption=text, parse_mode='html')
                else:
                    await self.client.send_message(chat_id, text, parse_mode='html')
            except:
                pass
            await asyncio.sleep(time_val)
        if chat_id in tag_chats:
            del tag_chats[chat_id]

    # ========== ID ==========
    async def id_handler(self, msg):
        global mid
        try:
            if msg.is_reply:
                reply_msg = await msg.get_reply_message()
                caption = f'<b>user id: <code>{reply_msg.sender_id}</code></b>'
                if mid:
                    await self.client.send_file(msg.chat_id, mid, caption=caption, parse_mode='html')
                    await msg.delete()
                else:
                    await msg.edit(caption, parse_mode='html')
            elif len(msg.text.split()) > 1 and msg.text.split()[1].startswith('@'):
                entity = await self.client.get_entity(msg.text.split()[1])
                caption = f'<b>user id: <code>{entity.id}</code></b>'
                await msg.edit(caption, parse_mode='html')
            else:
                caption = f'<b>chat id: <code>{msg.chat_id}</code></b>'
                await msg.edit(caption, parse_mode='html')
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
                    lines = f.readlines()
                    shablon.clear()
                    for line in lines:
                        shablon.append(line.strip())
                os.remove(file)
                await msg.edit("Успешно!")

    # ========== ВЫГРУЗКА ШАБЛОНА ==========
    async def file_handler(self, msg):
        with open('texts.txt', 'w', encoding='utf-8') as f:
            for line in shablon:
                f.write(line + '\n')
        await self.client.send_file(msg.chat_id, 'texts.txt')
        os.remove('texts.txt')
        await msg.delete()

    # ========== UPTIME ==========
    async def uptime_handler(self, msg):
        bot_runtime = int(time.time() - start_time)
        bot_runtime_formatted = str(timedelta(seconds=bot_runtime))
        await msg.edit(f'аптайм бота: <code>{bot_runtime_formatted}</code>', parse_mode='html')

    # ========== PING ==========
    async def ping_handler(self, msg):
        ping_now = time.perf_counter_ns()
        await msg.edit(f'<b>пинг: <code>{round((time.perf_counter_ns() - ping_now) / 10**2, 2)} ms</code></b>', parse_mode='html')

    # ========== ВСТУПИТЬ В ЧАТ ==========
    async def join_handler(self, msg):
        args = await self.get_args(msg)
        if args:
            chat_entity = await self.client.get_entity(args.split()[0])
            await self.client(JoinChannelRequest(chat_entity))

    # ========== ВЫЙТИ ИЗ ЧАТА ==========
    async def leave_handler(self, msg):
        args = await self.get_args(msg)
        if args:
            chat_entity = await self.client.get_entity(args.split()[0])
            await self.client(LeaveChannelRequest(chat_entity))
        else:
            await self.client(LeaveChannelRequest(msg.chat_id))

    # ========== ОСТАНОВКА СПАМА ==========
    async def stop_handler(self, msg):
        global spam_state
        args = await self.get_args(msg)
        chat_id = int(args.split()[0]) if args else msg.chat_id
        if chat_id in spam_state:
            spam_state[chat_id] = False
            del spam_state[chat_id]
            await msg.edit(f"<b>остановлено в чате <code>{chat_id}</code></b>", parse_mode='html')

    async def off_handler(self, msg):
        global tagger_chats
        args = await self.get_args(msg)
        chat_id = int(args.split()[0]) if args else msg.chat_id
        if chat_id in tagger_chats:
            del tagger_chats[chat_id]
            await msg.edit(f"<b>остановлено в чате <code>{chat_id}</code></b>", parse_mode='html')

    async def zstop_handler(self, msg):
        global spam_state1
        args = await self.get_args(msg)
        chat_id = int(args.split()[0]) if args else msg.chat_id
        if chat_id in spam_state1:
            del spam_state1[chat_id]
            await msg.edit(f"<b>остановлено в чате <code>{chat_id}</code></b>", parse_mode='html')

    async def tagoff_handler(self, msg):
        global tag_chats
        args = await self.get_args(msg)
        chat_id = int(args.split()[0]) if args else msg.chat_id
        if chat_id in tag_chats:
            del tag_chats[chat_id]
            await msg.edit(f"<b>остановлено в чате <code>{chat_id}</code></b>", parse_mode='html')

    async def clear_flood_handler(self, msg):
        global spam_state, spam_state1, tag_chats, tagger_chats
        spam_state.clear()
        spam_state1.clear()
        tag_chats.clear()
        tagger_chats.clear()
        await msg.edit("все флудилки оффнуты")

    async def list_handler(self, msg):
        global mlist
        if len(msg.text.split()) > 1:
            mlist = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            await msg.edit("<b>медиа изменено</b>", parse_mode='html')
            return
        response = f"spam_state: {spam_state}\n\nspam_state1: {spam_state1}\n\nautoreply_list: {autoreply_list}\n\ntagger_chats: {tagger_chats}\n\ntag_chats: {tag_chats}"
        if mlist:
            await self.client.send_file(msg.chat_id, mlist, caption=response, parse_mode='html')
            await msg.delete()
        else:
            await msg.edit(response, parse_mode='html')

    async def target_handler(self, msg):
        args = await self.get_args(msg)
        if args:
            self.target_user = args.strip().replace('@', '')
            await msg.edit(f"цель: <code>{self.target_user}</code>", parse_mode='html')
        else:
            await msg.edit("<b>укажи юзернейм или ID</b>", parse_mode='html')

    # ========== ДРОЧ ==========
    async def droch_handler(self, msg, action):
        if action == "старт":
            if self.droch_active:
                return await msg.edit("<b>уже фармлю!</b>", parse_mode='html')
            self.droch_active = True
            await msg.edit("<b>запущен цикл: 11 минут</b>", parse_mode='html')
            await asyncio.sleep(2)
            await msg.delete()
            while self.droch_active:
                try:
                    m = await self.client.send_message(msg.chat_id, "дроч")
                    await asyncio.sleep(5)
                    await m.delete()
                    await asyncio.sleep(660)
                except:
                    self.droch_active = False
                    break
        elif action == "стоп":
            self.droch_active = False
            await msg.edit("<b>авто-дроч остановлен</b>", parse_mode='html')

    # ========== ФАРМА ==========
    async def pharma_handler(self, msg, action):
        if action == "старт":
            if self.pharma_active:
                return await msg.edit("<b>ошибка: фарма уже запущена</b>", parse_mode='html')
            self.pharma_active = True
            await msg.edit("<b>авто-фарма запущена. интервал: 4 часа 5 минут</b>", parse_mode='html')
            await asyncio.sleep(2)
            await msg.delete()
            while self.pharma_active:
                try:
                    m = await self.client.send_message(msg.chat_id, "фарма")
                    await asyncio.sleep(5)
                    await m.delete()
                    await asyncio.sleep(14700)
                except:
                    self.pharma_active = False
                    break
        elif action == "стоп":
            self.pharma_active = False
            await msg.edit("<b>авто-фарма остановлена</b>", parse_mode='html')

    async def farm_menu_handler(self, msg):
        st_d = "работает" if self.droch_active else "выключен"
        st_f = "работает" if self.pharma_active else "выключен"
        farm_text = (
            "<b>меню фарма</b>\n\n"
            "<code>.дроч старт</code> — запустить авто-дроч\n"
            "<code>.дроч стоп</code> — остановить\n\n"
            "<code>.фарма старт</code> — запустить авто-фарма\n"
            "<code>.фарма стоп</code> — остановить\n\n"
            f"Статус дроча: <b>{st_d}</b>\n"
            f"Статус фарма: <b>{st_f}</b>"
        )
        await msg.edit(farm_text, parse_mode='html')

    # ========== HELP ==========
    async def help_handler(self, msg):
        global mh, name
        me = await self.client.get_me()
        namee = name
        if len(msg.text.split()) > 1:
            mh = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            await msg.edit("<b>медиа установлено</b>", parse_mode='html')
            return
        reply_msg = await msg.get_reply_message()
        caption = menutext.format(namee, msg.chat_id, me.id, me.first_name, me.username)
        if mh:
            try:
                await self.client.send_file(msg.chat_id, mh, caption=caption, parse_mode='html')
                await msg.delete()
            except:
                await msg.edit(caption, parse_mode='html')
        else:
            await msg.edit(caption, parse_mode='html')

    # ========== MENU ==========
    async def menu_handler(self, msg):
        global mm
        if len(msg.text.split()) > 1:
            mm = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            await msg.edit("<b>медиа установлено</b>", parse_mode='html')
            return
        reply_msg = await msg.get_reply_message()
        if mm:
            try:
                await self.client.send_file(msg.chat_id, mm, caption=menu, parse_mode='html')
                await msg.delete()
            except:
                await msg.edit(menu, parse_mode='html')
        else:
            await msg.edit(menu, parse_mode='html')

    # ========== CMD ==========
    async def cmd_handler(self, msg):
        global cmds
        if len(msg.text.split()) > 1:
            cmds = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            await msg.edit("<b>медиа для .cmd установлено</b>", parse_mode='html')
            return
        
        commands_text = """
<bold>ПОЛНЫЙ СПИСОК КОМАНД:</bold>

ОСНОВНЫЕ КОМАНДЫ:
<code>.help</code> — главное меню
<code>.menu</code> — второе меню
<code>.cmd</code> — этот список команд
<code>.id</code> — узнать chat id / user id
<code>.ping</code> — проверить пинг бота
<code>.uptime</code> — аптайм бота
<code>.name</code> + текст — изменить имя бота

AFK РЕЖИМ:
<code>.afk 1</code> — включить AFK
<code>.afk 2</code> — выключить AFK
<code>.afk [причина]</code> — установить причину
<code>.afk [ссылка]</code> — установить медиа для AFK

АВТООТВЕТЧИК (на пользователя):
<code>.nrc [время] [медиа] [шапка]</code> + реплай — включить автоответ
<code>.nrcc [id]</code> — выключить автоответ
<code>.rchange shapka [id] [текст]</code> — сменить шапку
<code>.rchange time [id] [секунды]</code> — сменить задержку
<code>.rchange media [id] [ссылка]</code> — сменить медиа

СПАМ В ЧАТЕ (reply):
<code>.avt [время] [медиа] [шапка]</code> + реплай — спам в чат
<code>.stop [chat_id]</code> — остановить спам

СПАМ В ДРУГОЙ ЧАТ:
<code>.nzt [chat_id] [время] [медиа] [шапка]</code> — спам в другой чат
<code>.rstop [chat_id]</code> — остановить

КАЛЕНДАРЬ (отложенный спам):
<code>.clr [время] [медиа] [шапка]</code> + реплай — календарь
<code>.cal [chat_id] [время] [медиа] [шапка]</code> — календарь в другой чат

ТЕГГЕРЫ:
<code>.tagger [user_id] [время] [медиа] [текст]</code> + реплай — теггер
<code>.tag [chat_id] [user_id] [время] [медиа] [текст]</code> — теггер в другой чат
<code>.off [chat_id]</code> — остановить tagger
<code>.tagoff [chat_id]</code> — остановить tag

РАБОТА С ШАБЛОНАМИ:
<code>.load</code> + реплай на файл — загрузить свой шаблон
<code>.file</code> — выгрузить текущий шаблон

РАБОТА С ЧАТАМИ:
<code>.rrr [ссылка]</code> — вступить в чат
<code>.leave [ссылка]</code> — выйти из чата
<code>.contacts</code> — добавить участников чата в контакты

ХОСТИНГИ:
<code>.x0</code> + реплай на медиа — загрузить на catbox.moe

ФАРМ (для игры):
<code>.farm</code> — меню фарма
<code>.дроч старт / стоп</code> — авто-дроч (11 минут)
<code>.фарма старт / стоп</code> — авто-фарма (4 часа 5 минут)

ДРУГИЕ КОМАНДЫ:
<code>.words</code> + реплай — подсчёт слов/символов
<code>.list</code> — список активных процессов
<code>.c_flood</code> — отключить все флудилки
<code>.lz</code> — очистить список автоответа
<code>.target [username/id]</code> — установить цель для авто-удаления

МЕДИА ДЛЯ КОМАНД:
<code>.help [ссылка]</code> — установить медиа для .help
<code>.menu [ссылка]</code> — установить медиа для .menu
<code>.cmd [ссылка]</code> — установить медиа для .cmd
<code>.list [ссылка]</code> — установить медиа для .list
<code>.id [ссылка]</code> — установить медиа для .id

МЕДИА КОМАНДЫ:
<code>.pfl [имя]</code> — ответом на фото, видео или m4a скачать и сделать активным
<code>.phocount</code> — сколько всего медиа скачано
<code>.pholist</code> — список медиа и активное
<code>.phoset номер|имя 1|2</code> — поменять активное медиа (1=основное, 2=hntd)
<code>.resetm 1|2</code> — сбросить выбранное медиа на фото профиля
<code>.phoren старый новый</code> — переименовать номер медиа
<code>.phodel номер|имя</code> — удалить медиа

POST КОМАНДЫ:
<code>.poste 'ссылка' минуты</code> — рассылка поста в группы
<code>.poste_stop</code> — остановить все рассылки
<code>.poste_stop ссылка</code> — остановить по ссылке
<code>.poste_list</code> — список активных рассылок
<code>.pblk list</code> — список групп из блок-листа
<code>.pblk add id</code> / del id / clear — блок-лист пересылки
<code>.pblkclear</code> — полностью очистить весь pblk list

СИСТЕМНЫЕ КОМАНДЫ:
<code>.status</code> — статус работы функций
<code>.zw</code> — остановить все функции
<code>.selftest</code> — проверка работоспособности всех функций
"""
        if cmds:
            try:
                await self.client.send_file(msg.chat_id, cmds, caption=commands_text, parse_mode='html')
                await msg.delete()
            except:
                await msg.edit(commands_text, parse_mode='html')
        else:
            await msg.edit(commands_text, parse_mode='html')

    # ========== X0 ==========
    async def x0_handler(self, msg):
        if not msg.is_reply:
            return await msg.edit("<b>нужен реплай на медиа</b>", parse_mode='html')
        reply_msg = await msg.get_reply_message()
        if not reply_msg.media:
            return await msg.edit("<b>нет медиа</b>", parse_mode='html')
        await msg.edit("<b>загружаю на catbox.moe...</b>", parse_mode='html')
        
        file = None
        try:
            file = await reply_msg.download_media()
            if not file:
                return await msg.edit("<b>не удалось скачать файл</b>", parse_mode='html')
            
            url = 'https://catbox.moe/user/api.php'
            
            with open(file, 'rb') as f:
                files = {'fileToUpload': f}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                response = requests.post(url, files=files, timeout=60, headers=headers)
            
            if response.status_code == 200:
                link = response.text.strip()
                await msg.edit(f"<bold>ссылка на catbox.moe:</bold>\n<code>{link}</code>", parse_mode='html', link_preview=False)
            else:
                await msg.edit(f"<bold>ошибка: {response.status_code}</bold>", parse_mode='html')
                
        except requests.exceptions.Timeout:
            await msg.edit("<bold>таймаут подключения. попробуй позже</bold>", parse_mode='html')
        except Exception as e:
            await msg.edit(f"<bold>ошибка: {e}</bold>", parse_mode='html')
        finally:
            if file and os.path.exists(file):
                try:
                    await asyncio.sleep(0.3)
                    os.remove(file)
                except:
                    pass

    # ========== NAME ==========
    async def name_handler(self, msg):
        global name
        args = await self.get_args(msg)
        if args:
            name = args
            await msg.edit(f'<bold>имя бота изменено: {name}</bold>', parse_mode='html')

    # ========== MEDIA COMMANDS ==========
    async def pfl_handler(self, msg):
        global media_storage, media_counter
        args = await self.get_args(msg)
        if not msg.is_reply:
            return await msg.edit("<b>нужен ответ на фото, видео или аудио</b>", parse_mode='html')
        
        reply = await msg.get_reply_message()
        if not reply.media:
            return await msg.edit("<b>в ответе нет медиа</b>", parse_mode='html')
        
        name = args if args else f"media_{media_counter+1}"
        
        try:
            file_data = await reply.download_media(bytes)
            media_type = "photo"
            if hasattr(reply.media, 'video') and reply.media.video:
                media_type = "video"
            elif hasattr(reply.media, 'audio') and reply.media.audio:
                media_type = "audio"
            elif hasattr(reply.media, 'document') and reply.media.document:
                mime = reply.media.document.mime_type
                if 'video' in mime:
                    media_type = "video"
                elif 'audio' in mime:
                    media_type = "audio"
                else:
                    media_type = "document"
            
            media_storage[name] = {
                'data': file_data,
                'type': media_type,
                'active_1': False,
                'active_2': False
            }
            media_counter += 1
            await msg.edit(f"<b>медиа сохранено как {name} (тип: {media_type})</b>", parse_mode='html')
        except Exception as e:
            await msg.edit(f"<b>ошибка при сохранении: {e}</b>", parse_mode='html')

    async def phocount_handler(self, msg):
        global media_counter
        await msg.edit(f"<b>всего медиа скачано: {media_counter}</b>", parse_mode='html')

    async def pholist_handler(self, msg):
        global media_storage
        if not media_storage:
            return await msg.edit("<b>нет сохранённых медиа</b>", parse_mode='html')
        
        lines = []
        for idx, (name, data) in enumerate(media_storage.items(), 1):
            active1 = "+" if data.get('active_1') else "-"
            active2 = "+" if data.get('active_2') else "-"
            lines.append(f"{idx}. {name} [осн:{active1} hntd:{active2}] ({data['type']})")
        
        result = "<b>список медиа:</b>\n" + "\n".join(lines)
        await msg.edit(result, parse_mode='html')

    async def phoset_handler(self, msg):
        global media_storage
        args = await self.get_args(msg)
        if not args:
            return await msg.edit("<b>использование: .phoset номер|имя 1|2</b>", parse_mode='html')
        
        parts = args.split()
        if len(parts) < 2:
            return await msg.edit("<b>укажи имя/номер и тип (1 или 2)</b>", parse_mode='html')
        
        target = parts[0]
        target_type = parts[1]
        
        if target_type not in ['1', '2']:
            return await msg.edit("<b>тип должен быть 1 (основное) или 2 (hntd)</b>", parse_mode='html')
        
        # Поиск по имени или номеру
        found = None
        if target.isdigit():
            idx = int(target) - 1
            names = list(media_storage.keys())
            if 0 <= idx < len(names):
                found = names[idx]
        else:
            if target in media_storage:
                found = target
        
        if not found:
            return await msg.edit(f"<b>медиа '{target}' не найдено</b>", parse_mode='html')
        
        # Сброс активного для этого типа
        for name, data in media_storage.items():
            if target_type == '1':
                data['active_1'] = (name == found)
            else:
                data['active_2'] = (name == found)
        
        active_num = "основное" if target_type == '1' else "hntd"
        await msg.edit(f"<b>активное {active_num} медиа: {found}</b>", parse_mode='html')

    async def resetm_handler(self, msg):
        global media_storage
        args = await self.get_args(msg)
        target_type = args if args else "1"
        
        if target_type not in ['1', '2']:
            return await msg.edit("<b>тип должен быть 1 (основное) или 2 (hntd)</b>", parse_mode='html')
        
        for data in media_storage.values():
            if target_type == '1':
                data['active_1'] = False
            else:
                data['active_2'] = False
        
        await msg.edit(f"<b>активное { 'основное' if target_type == '1' else 'hntd' } медиа сброшено на фото профиля</b>", parse_mode='html')

    async def phoren_handler(self, msg):
        global media_storage
        args = await self.get_args(msg)
        if not args:
            return await msg.edit("<b>использование: .phoren старый_имя новый_имя</b>", parse_mode='html')
        
        parts = args.split()
        if len(parts) < 2:
            return await msg.edit("<b>укажи старое и новое имя</b>", parse_mode='html')
        
        old_name, new_name = parts[0], parts[1]
        
        if old_name not in media_storage:
            return await msg.edit(f"<b>медиа '{old_name}' не найдено</b>", parse_mode='html')
        if new_name in media_storage:
            return await msg.edit(f"<b>медиа '{new_name}' уже существует</b>", parse_mode='html')
        
        media_storage[new_name] = media_storage.pop(old_name)
        await msg.edit(f"<b>медиа переименовано: {old_name} -> {new_name}</b>", parse_mode='html')

    async def phodel_handler(self, msg):
        global media_storage, media_counter
        args = await self.get_args(msg)
        if not args:
            return await msg.edit("<b>использование: .phodel номер|имя</b>", parse_mode='html')
        
        target = args.strip()
        
        # Поиск по имени или номеру
        found = None
        if target.isdigit():
            idx = int(target) - 1
            names = list(media_storage.keys())
            if 0 <= idx < len(names):
                found = names[idx]
        else:
            if target in media_storage:
                found = target
        
        if not found:
            return await msg.edit(f"<b>медиа '{target}' не найдено</b>", parse_mode='html')
        
        del media_storage[found]
        media_counter = len(media_storage)
        await msg.edit(f"<b>медиа '{found}' удалено</b>", parse_mode='html')

    # ========== POST COMMANDS ==========
    async def poste_handler(self, msg):
        global poste_list, poste_blocklist
        args = await self.get_args(msg)
        if not args:
            return await msg.edit("<b>использование: .poste 'ссылка' минуты</b>", parse_mode='html')
        
        parts = args.split()
        if len(parts) < 2:
            return await msg.edit("<b>укажи ссылку и интервал (минуты)</b>", parse_mode='html')
        
        link = parts[0]
        try:
            interval = int(parts[1])
        except ValueError:
            return await msg.edit("<b>интервал должен быть числом</b>", parse_mode='html')
        
        if interval < 1:
            return await msg.edit("<b>интервал не может быть меньше 1 минуты</b>", parse_mode='html')
        
        if link in poste_list:
            return await msg.edit(f"<b>рассылка для {link} уже запущена</b>", parse_mode='html')
        
        # Получаем чаты, где есть бот
        dialogs = await self.client.get_dialogs()
        target_chats = [d.entity.id for d in dialogs if d.is_channel or d.is_group]
        target_chats = [c for c in target_chats if c not in poste_blocklist]
        
        poste_list[link] = {
            'chats': target_chats,
            'interval': interval,
            'running': True
        }
        
        await msg.edit(f"<b>рассылка запущена: {link}\nинтервал: {interval} мин\nчатов: {len(target_chats)}\nостановить: .poste_stop {link}</b>", parse_mode='html')
        
        # Запускаем рассылку в фоне
        asyncio.create_task(self._poste_worker(link, target_chats, interval))

    async def _poste_worker(self, link, chats, interval):
        global poste_list
        while poste_list.get(link, {}).get('running', False):
            for chat_id in chats:
                if not poste_list.get(link, {}).get('running', False):
                    break
                try:
                    await self.client.send_message(chat_id, link)
                except Exception:
                    pass
                await asyncio.sleep(2)  # небольшая задержка между чатами
            await asyncio.sleep(interval * 60)

    async def poste_stop_handler(self, msg):
        global poste_list
        args = await self.get_args(msg)
        
        if not args:
            # Остановить все
            for link in poste_list:
                poste_list[link]['running'] = False
            poste_list.clear()
            await msg.edit("<b>все рассылки остановлены</b>", parse_mode='html')
            return
        
        link = args.strip()
        if link in poste_list:
            poste_list[link]['running'] = False
            del poste_list[link]
            await msg.edit(f"<b>рассылка для {link} остановлена</b>", parse_mode='html')
        else:
            await msg.edit(f"<b>рассылка для {link} не найдена</b>", parse_mode='html')

    async def poste_list_handler(self, msg):
        global poste_list
        if not poste_list:
            return await msg.edit("<b>активных рассылок нет</b>", parse_mode='html')
        
        lines = []
        for link, data in poste_list.items():
            lines.append(f"ссылка: {link}\n  чатов: {len(data['chats'])} интервал: {data['interval']} мин")
        
        result = "<b>активные рассылки:</b>\n" + "\n".join(lines)
        await msg.edit(result, parse_mode='html')

    async def pblk_handler(self, msg):
        global poste_blocklist
        args = await self.get_args(msg)
        if not args:
            return await msg.edit("<b>использование: .pblk list|add id|del id|clear</b>", parse_mode='html')
        
        parts = args.split()
        action = parts[0].lower()
        
        if action == 'list':
            if not poste_blocklist:
                return await msg.edit("<b>блок-лист пуст</b>", parse_mode='html')
            ids_str = "\n".join(str(c) for c in poste_blocklist)
            await msg.edit(f"<b>блок-лист (чаты, куда НЕ отправлять):</b>\n{ids_str}", parse_mode='html')
        
        elif action == 'add':
            if len(parts) < 2:
                return await msg.edit("<b>укажи id чата</b>", parse_mode='html')
            try:
                chat_id = int(parts[1])
                if chat_id not in poste_blocklist:
                    poste_blocklist.append(chat_id)
                await msg.edit(f"<b>чат {chat_id} добавлен в блок-лист</b>", parse_mode='html')
            except ValueError:
                await msg.edit("<b>id должен быть числом</b>", parse_mode='html')
        
        elif action == 'del':
            if len(parts) < 2:
                return await msg.edit("<b>укажи id чата</b>", parse_mode='html')
            try:
                chat_id = int(parts[1])
                if chat_id in poste_blocklist:
                    poste_blocklist.remove(chat_id)
                await msg.edit(f"<b>чат {chat_id} удалён из блок-листа</b>", parse_mode='html')
            except ValueError:
                await msg.edit("<b>id должен быть числом</b>", parse_mode='html')
        
        elif action == 'clear':
            poste_blocklist.clear()
            await msg.edit("<b>блок-лист очищен</b>", parse_mode='html')
        
        else:
            await msg.edit("<b>неизвестное действие. доступно: list, add, del, clear</b>", parse_mode='html')

    async def pblkclear_handler(self, msg):
        global poste_blocklist
        poste_blocklist.clear()
        await msg.edit("<b>блок-лист полностью очищен</b>", parse_mode='html')

    # ========== SYSTEM COMMANDS ==========
    async def status_handler(self, msg):
        global spam_state, spam_state1, tagger_chats, tag_chats, autoreply_list, poste_list
        status_text = f"""
<bold>статус работы функций:</bold>

спам (avt): {len(spam_state)} активных
спам (nzt): {len(spam_state1)} активных
теггер (tagger): {len(tagger_chats)} активных
теггер (tag): {len(tag_chats)} активных
автоответчик: {len(autoreply_list)} пользователей
авто-дроч: {'включен' if self.droch_active else 'выключен'}
авто-фарма: {'включена' if self.pharma_active else 'выключена'}
рассылки (poste): {len(poste_list)} активных
блок-лист (pblk): {len(poste_blocklist)} чатов
"""
        await msg.edit(status_text, parse_mode='html')

    async def zw_handler(self, msg):
        global spam_state, spam_state1, tagger_chats, tag_chats, autoreply_list, poste_list
        spam_state.clear()
        spam_state1.clear()
        tagger_chats.clear()
        tag_chats.clear()
        autoreply_list.clear()
        self.droch_active = False
        self.pharma_active = False
        for link in poste_list:
            poste_list[link]['running'] = False
        poste_list.clear()
        await msg.edit("<bold>все функции остановлены</bold>", parse_mode='html')

    async def selftest_handler(self, msg):
        start_test = time.time()
        results = []
        
        # Проверка 1: клиент активен
        try:
            me = await self.client.get_me()
            results.append(f"клиент: OK ({me.first_name})")
        except Exception as e:
            results.append(f"клиент: ОШИБКА ({e})")
        
        # Проверка 2: права на отправку сообщений
        try:
            await msg.edit("<b>selftest...</b>", parse_mode='html')
            results.append("отправка сообщений: OK")
        except Exception as e:
            results.append(f"отправка сообщений: ОШИБКА ({e})")
        
        # Проверка 3: скорость ответа
        ping_ms = round((time.time() - start_test) * 1000, 2)
        results.append(f"задержка ответа: {ping_ms} ms")
        
        # Проверка 4: доступность глобальных переменных
        try:
            _ = spam_state
            _ = autoreply_list
            results.append("глобальные переменные: OK")
        except Exception as e:
            results.append(f"глобальные переменные: ОШИБКА ({e})")
        
        await msg.edit("\n".join(results), parse_mode='html')

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
                        try:
                            await msg.delete()
                        except:
                            pass
                return

            text = msg.text or ""
            
            # Существующие команды
            if text.startswith('.afk'):
                await self.afk_handler(msg)
            elif text.startswith('.avt'):
                await self.renewal_handler(msg)
            elif text.startswith('.nzt'):
                await self.spam_handler(msg)
            elif text.startswith('.clr'):
                await self.kalendar_handler(msg)
            elif text.startswith('.nrc') or text.startswith('.nrcc') or text.startswith('.setshpk'):
                await self.autoreply_handler(msg)
            elif text.startswith('.rchange'):
                await self.rchange_handler(msg)
            elif text.startswith('.tagger'):
                await self.tagger_handler(msg)
            elif text.startswith('.tag ') and not text.startswith('.tagoff'):
                await self.tag_handler(msg)
            elif text.startswith('.tagoff'):
                await self.tagoff_handler(msg)
            elif text.startswith('.stop'):
                await self.stop_handler(msg)
            elif text.startswith('.off'):
                await self.off_handler(msg)
            elif text.startswith('.zstop'):
                await self.zstop_handler(msg)
            elif text.startswith('.id'):
                await self.id_handler(msg)
            elif text.startswith('.words'):
                await self.words_handler(msg)
            elif text.startswith('.load'):
                await self.load_handler(msg)
            elif text.startswith('.file'):
                await self.file_handler(msg)
            elif text.startswith('.uptime'):
                await self.uptime_handler(msg)
            elif text.startswith('.ping'):
                await self.ping_handler(msg)
            elif text.startswith('.rrr'):
                await self.join_handler(msg)
            elif text.startswith('.leave'):
                await self.leave_handler(msg)
            elif text.startswith('.c_flood'):
                await self.clear_flood_handler(msg)
            elif text.startswith('.list'):
                await self.list_handler(msg)
            elif text.startswith('.target'):
                await self.target_handler(msg)
            elif text.startswith('.дроч старт'):
                await self.droch_handler(msg, "старт")
            elif text.startswith('.дроч стоп'):
                await self.droch_handler(msg, "стоп")
            elif text.startswith('.фарма старт'):
                await self.pharma_handler(msg, "старт")
            elif text.startswith('.фарма стоп'):
                await self.pharma_handler(msg, "стоп")
            elif text.startswith('.farm'):
                await self.farm_menu_handler(msg)
            elif text.startswith('.help'):
                await self.help_handler(msg)
            elif text.startswith('.menu'):
                await self.menu_handler(msg)
            elif text.startswith('.cmd'):
                await self.cmd_handler(msg)
            elif text.startswith('.x0'):
                await self.x0_handler(msg)
            elif text.startswith('.name'):
                await self.name_handler(msg)
            
            # Медиа команды
            elif text.startswith('.pfl'):
                await self.pfl_handler(msg)
            elif text.startswith('.phocount'):
                await self.phocount_handler(msg)
            elif text.startswith('.pholist'):
                await self.pholist_handler(msg)
            elif text.startswith('.phoset'):
                await self.phoset_handler(msg)
            elif text.startswith('.resetm'):
                await self.resetm_handler(msg)
            elif text.startswith('.phoren'):
                await self.phoren_handler(msg)
            elif text.startswith('.phodel'):
                await self.phodel_handler(msg)
            
            # Post команды
            elif text.startswith('.poste ') and not text.startswith('.poste_stop') and not text.startswith('.poste_list'):
                await self.poste_handler(msg)
            elif text.startswith('.poste_stop'):
                await self.poste_stop_handler(msg)
            elif text.startswith('.poste_list'):
                await self.poste_list_handler(msg)
            elif text.startswith('.pblk '):
                await self.pblk_handler(msg)
            elif text.startswith('.pblkclear'):
                await self.pblkclear_handler(msg)
            
            # Системные команды
            elif text.startswith('.status'):
                await self.status_handler(msg)
            elif text.startswith('.zw'):
                await self.zw_handler(msg)
            elif text.startswith('.selftest'):
                await self.selftest_handler(msg)

        await self.client.run_until_disconnected()

# ==================== ЗАПУСК ДВУХ АККАУНТОВ ====================
async def run_bots():
    bot1 = Userbot(ACCOUNT1_SESSION, ACCOUNT1_API_ID, ACCOUNT1_API_HASH)
    bot2 = Userbot(ACCOUNT2_SESSION, ACCOUNT2_API_ID, ACCOUNT2_API_HASH)
    
    await asyncio.gather(
        bot1.run(),
        bot2.run()
    )

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    asyncio.run(run_bots())
