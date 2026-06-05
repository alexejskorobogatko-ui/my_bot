# -*- coding: utf-8 -*-
import os
import sys
import time
import asyncio
import threading
import glob
from random import choice
from datetime import datetime, timedelta

import requests

from flask import Flask
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

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

# ==================== ПУТИ ДЛЯ ФАЙЛОВ ====================
TEMPLATES_DIR = "templates"
MEDIA_DIR = "media"

# Создаём папки если их нет
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)

# ==================== ШАБЛОНЫ ПО УМОЛЧАНИЮ ====================
DEFAULT_SHABLON = [
    "садовыми ножницами исполосоваю сонную артерию твоей мамаши",
    "из вырезанных голов твоей родословной построю пьедестал",
    "экзартикуляционирую вульву твоей матери да бы её пробило на красный фонтан метаморфозы",
    "вывалю путем эякуляции твои кишки в ванну, и заставлю купаться тебя в этом бульоне",
    "раздербеню твои атрофированные рёбра словно гнилую ограду",
    "даже трупные черви скулят от амбре развороченной могилы твоей родни",
    "отвар из твоих квашенных костей вылью в канализацию",
    "твоя морда это адов тигель где плавится дерьмище, но я лишь вычерпаю это ведром и вылью тебе в глотачку",
    "твои узурпированные кости это меловые скрижали на которых я вырежу историю твоего падения, а из твоих переёбаных рёбер сложу алтарь своему презрению",
    "вспорю твой живот хуём вместо ножа, дабы вынуть кишечнополостные трубы и сплести из них удавку",
]

# Сохраняем шаблон по умолчанию в файл, если его нет
default_template_path = os.path.join(TEMPLATES_DIR, "main.txt")
if not os.path.exists(default_template_path):
    with open(default_template_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(DEFAULT_SHABLON))

# ==================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ====================
spam_state = {}
start_time = time.time()
tagger_chats = {}
mid = 'https://x0.at/cUQa.jpg'
name = "Ralvatron"
mh = 'https://x0.at/5-ku.mp4'
mm = 'https://x0.at/5-ku.mp4'
cmds = 'https://x0.at/Dv0D.jpg'
status_media = None

# ========== ТЕКУЩИЙ ШАБЛОН ==========
current_shablon = []
current_template_name = "main"

# Загружаем шаблон по умолчанию
def load_template(template_name):
    global current_shablon, current_template_name
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.txt")
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            current_shablon = [line.strip() for line in f.readlines() if line.strip()]
        current_template_name = template_name
        return True
    return False

# Загружаем основной шаблон при старте
load_template("main")

# ========== МЕДИА ХРАНИЛИЩЕ ==========
def get_media_path(media_id):
    """Поиск файла медиа по ID (любое расширение)"""
    pattern = os.path.join(MEDIA_DIR, f"{media_id}.*")
    files = glob.glob(pattern)
    if files:
        return files[0]
    return None

def save_media(media_id, file_data, extension):
    """Сохранение медиа файла"""
    file_path = os.path.join(MEDIA_DIR, f"{media_id}.{extension}")
    with open(file_path, 'wb') as f:
        f.write(file_data)
    return file_path

def delete_media(media_id):
    """Удаление медиа файла"""
    file_path = get_media_path(media_id)
    if file_path:
        os.remove(file_path)
        return True
    return False

def get_all_media():
    """Список всех сохранённых медиа"""
    files = glob.glob(os.path.join(MEDIA_DIR, "*.*"))
    result = []
    for f in files:
        basename = os.path.basename(f)
        name, ext = os.path.splitext(basename)
        size = os.path.getsize(f)
        result.append((name, ext[1:], size))
    return result

# ========== АВТО-ПИАР ==========
poste_list = {}
poste_blocklist = []

# ========== DETECT ==========
detect_list = {}

# ========== ПИНГ СТАТИСТИКА ==========
ping_history = []

# ==================== ТЕКСТЫ МЕНЮ ====================
menutext = """
⛧ Основное меню ⛧

<b><code>.help</code></b> — главное меню
<b><code>.menu</code></b> — спам и теггер
<b><code>.more</code></b> — дополнительные функции
<b><code>.custom</code></b> — настройки кастомизации
<b><code>.rasset</code></b> — настройки рассылки
<b><code>.times</code></b> — время работы бота
<b><code>.files</code></b> — TXT шаблоны
<b><code>.id</code></b> — ID чата/пользователя
<b><code>.ping</code></b> — пинг + аптайм
<b><code>.name</code></b> + текст — изменить имя бота
"""

menu = """
⛧ Спам и теггер ⛧

<b><code>.avt + время + реплай</code></b> — спам в чат
<b><code>.stop [chat_id]</code></b> — остановить спам
<b><code>.tagger + айди + время + реплай</code></b> — теггер
<b><code>.off [chat_id]</code></b> — остановить теггер
<b><code>.clr + время + реплай</code></b> — календарь
"""

more_text = """
✮ Дополнительные функции ✮

<b><code>.shb list</code></b> — список шаблонов фраз
<b><code>.shb load [номер]</code></b> — загрузить шаблон
<b><code>.med save [номер]</code></b> + реплай — сохранить медиа
<b><code>.med list</code></b> — список медиа
<b><code>.med send [номер]</code></b> — отправить медиа
<b><code>.med del [номер]</code></b> — удалить медиа
<b><code>.autodel + time</code></b> — автоудаление сообщений
<b><code>.scrape + Chat ID</code></b> — выгрузка списка чата
<b><code>.check + реплай</code></b> — проверка транслитерации
"""

custom_text = """
⛧ Настройки кастомизации ⛧

<b><code>.help [ссылка]</code></b> — медиа для .help
<b><code>.menu [ссылка]</code></b> — медиа для .menu
<b><code>.more [ссылка]</code></b> — медиа для .more
<b><code>.cmd [ссылка]</code></b> — медиа для .cmd
<b><code>.id [ссылка]</code></b> — медиа для .id
<b><code>.status [ссылка]</code></b> — медиа для .status
"""

rasset_text = """
⛧ Настройки рассылки ⛧

<b><code>.poste 'ссылка' минуты</code></b> — запуск рассылки
<b><code>.poste_stop</code></b> — остановить все
<b><code>.poste_stop ссылка</code></b> — остановить по ссылке
<b><code>.poste_list</code></b> — список активных рассылок
<b><code>.pblk list</code></b> — список блок-листа
<b><code>.pblk add id</code></b> — добавить в блок
<b><code>.pblk del id</code></b> — удалить из блока
<b><code>.pblk clear</code></b> — очистить блок-лист
<b><code>.pblkclear</code></b> — очистить всё
"""

times_text = """
⛧ Время работы бота ⛧

<b><code>.ping</code></b> — пинг + аптайм + статистика
<b><code>.status</code></b> — статус функций
<b><code>.zw</code></b> — остановить все функции
"""

files_text = """
⛧ TXT шаблоны ⛧

<b><code>.load + реплай на файл</code></b> — загрузить шаблон
<b><code>.file</code></b> — выгрузить текущий шаблон
"""

commands_text = """
⛧ Полный список команд ⛧

✮ Основные команды ✮
<b><code>.help</code></b> — главное меню
<b><code>.menu</code></b> — спам и теггер
<b><code>.more</code></b> — доп. функции
<b><code>.custom</code></b> — настройки кастомизации
<b><code>.rasset</code></b> — настройки рассылки
<b><code>.times</code></b> — время работы
<b><code>.files</code></b> — TXT шаблоны
<b><code>.id</code></b> — ID чата/пользователя
<b><code>.ping</code></b> — пинг + аптайм + статистика
<b><code>.name</code></b> + текст — изменить имя
<b><code>.x0 + репл</code></b> — загрузить медиа на хостинг
<b><code>.words + репл</code></b> — подсчёт слов/символов
<b><code>.load + репл</code></b> — смена шаблонов
<b><code>.file</code></b> — выгрузить шаблон

✮ Спам и теггер ✮
<b><code>.avt + время + реплай</code></b> — спам в чат
<b><code>.stop [chat_id]</code></b> — остановить спам
<b><code>.tagger + айди + время + реплай</code></b> — теггер
<b><code>.off [chat_id]</code></b> — остановить теггер
<b><code>.clr + время + реплай</code></b> — календарь

✮ Детект ✮
<b><code>.detect [@username/id]</code></b> или реплай — начать слежение
<b><code>.detectoff [@username/id]</code></b> или реплай — остановить
<b><code>.detectlist</code></b> — список активных детектов

✮ Постинг ✮
<b><code>.poste 'ссылка' минуты</code></b> — пересылка поста
<b><code>.poste_stop</code></b> — остановить все
<b><code>.poste_list</code></b> — список активных рассылок
<b><code>.pblk list/add/del/clear</code></b> — блок-лист

✮ Системные ✮
<b><code>.status</code></b> — статус работы функций
<b><code>.zw</code></b> — остановить все функции

✮ Медиа хранилище ✮
<b><code>.med save [номер]</code></b> + реплай — сохранить медиа
<b><code>.med list</code></b> — список медиа
<b><code>.med send [номер]</code></b> — отправить медиа
<b><code>.med del [номер]</code></b> — удалить медиа

✮ Шаблоны фраз ✮
<b><code>.shb list</code></b> — список шаблонов
<b><code>.shb load [номер]</code></b> — загрузить шаблон

⛧ Владелец: @misosphere
"""

# ==================== КЛАСС ЮЗЕРБОТА ====================
class Userbot:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        self.target_user = None
        self._target_timer_task = None
        self.target_chat_id_for_timer = None

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

    # ========== ПОЛУЧЕНИЕ МЕДИА ИЗ ХРАНИЛИЩА ==========
    async def get_media_from_storage(self, media_ref):
        """Проверяет, есть ли media:XXX в строке и возвращает путь к файлу и очищенную строку"""
        if not media_ref:
            return None, media_ref
        
        import re
        match = re.search(r'med:(\d+)', media_ref)
        if match:
            media_id = match.group(1)
            media_path = get_media_path(media_id)
            if media_path:
                # Удаляем med:XXX из строки
                clean_text = re.sub(r'med:\d+\s*', '', media_ref).strip()
                return media_path, clean_text
        return None, media_ref

    # ========== WATCHER ==========
    async def watcher(self, msg):
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
        parts = args.split()
        time_val = int(parts[0])
        if time_val < 3: return await msg.edit("<b>мин. задержка - 3</b>", parse_mode='html')
        
        # Проверяем на медиа из хранилища
        media_path = None
        shapka_text = ''
        for i, p in enumerate(parts[1:], 1):
            if p.startswith('med:'):
                media_path, _ = await self.get_media_from_storage(p)
            else:
                shapka_text = ' '.join(parts[1:])
                break
        
        spam_state[chat_id] = True
        await msg.edit(f'<b>включен\nвыкл: <code>.stop {chat_id}</code></b>', parse_mode='html')
        while chat_id in spam_state and spam_state[chat_id]:
            try:
                text = shapka_text + " " + choice(current_shablon) if shapka_text else choice(current_shablon)
                if media_path:
                    await msg.respond(text, file=media_path, reply_to=reply.id if reply else None)
                else:
                    await msg.respond(text, reply_to=reply.id if reply else None)
            except Exception as e:
                if "TypeNotFoundError" in str(e) or "Constructor ID" in str(e):
                    pass
                elif "FloodWaitError" in str(e):
                    await asyncio.sleep(e.seconds)
                else:
                    print(f"Спам ошибка: {e}")
            await asyncio.sleep(time_val)
        if chat_id in spam_state: del spam_state[chat_id]

    # ========== КАЛЕНДАРЬ ==========
    async def kalendar_handler(self, msg):
        args = await self.get_args(msg)
        if not args: return await msg.edit("<b>аргументы: время медиа шапка</b>", parse_mode='html')
        parts = args.split()
        time_val = int(parts[0])
        
        # Проверяем на медиа из хранилища
        media_path = None
        shapka_text = ''
        for i, p in enumerate(parts[1:], 1):
            if p.startswith('med:'):
                media_path, _ = await self.get_media_from_storage(p)
            else:
                shapka_text = ' '.join(parts[1:])
                break
        
        await msg.edit(f"{shapka_text} {choice(current_shablon)}", parse_mode='html')
        for i in range(100):
            schedule_date = datetime.now() + timedelta(minutes=time_val)
            text = shapka_text + " " + choice(current_shablon) if shapka_text else choice(current_shablon)
            if media_path:
                await msg.respond(text, file=media_path, schedule=schedule_date.timestamp())
            else:
                await msg.respond(text, schedule=schedule_date.timestamp())
            await asyncio.sleep(0)

    # ========== ТЕГГЕР ==========
    async def tagger_handler(self, msg):
        args = msg.text.split(maxsplit=1)
        if len(args) < 2: return await msg.edit("<b>аргументы: user_id время [med:номер] [текст]</b>", parse_mode='html')
        parts = args[1].split()
        if len(parts) < 2: return
        user_id = int(parts[0])
        time_val = int(parts[1])
        if time_val < 3: return await msg.edit("<b>мин. задержка - 3</b>", parse_mode='html')
        
        # Проверяем на медиа из хранилища
        media_path = None
        caption = ''
        for p in parts[2:]:
            if p.startswith('med:'):
                media_path, _ = await self.get_media_from_storage(p)
            else:
                caption = ' '.join(parts[2:])
                break
        
        reply_to_msg = await msg.get_reply_message()
        chat_id = reply_to_msg.chat_id if reply_to_msg else msg.chat_id
        tagger_chats[chat_id] = True
        await msg.edit(f'<b>включен\nвыкл: <code>.off {chat_id}</code></b>', parse_mode='html')
        while chat_id in tagger_chats:
            text = f"{caption} <a href='tg://user?id={user_id}'>{choice(current_shablon)}</a>"
            try:
                if media_path:
                    await self.client.send_file(chat_id, media_path, caption=text, parse_mode='html')
                else:
                    await self.client.send_message(chat_id, text, parse_mode='html')
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

    # ========== ЗАГРУЗКА ШАБЛОНА (старая команда) ==========
    async def load_handler(self, msg):
        global current_shablon
        if msg.is_reply:
            reply_msg = await msg.get_reply_message()
            if reply_msg.file:
                file = await reply_msg.download_media()
                with open(file, 'r', encoding='utf-8') as f:
                    current_shablon.clear()
                    current_shablon.extend([line.strip() for line in f.readlines() if line.strip()])
                os.remove(file)
                await msg.edit("Успешно!")

    # ========== ВЫГРУЗКА ШАБЛОНА ==========
    async def file_handler(self, msg):
        with open('texts.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(current_shablon))
        await self.client.send_file(msg.chat_id, 'texts.txt')
        os.remove('texts.txt')
        await msg.delete()

    # ========== PING + UPTIME + СТАТИСТИКА ==========
    async def ping_handler(self, msg):
        global ping_history
        
        bot_runtime = int(time.time() - start_time)
        uptime_str = str(timedelta(seconds=bot_runtime))
        
        # Правильный расчёт пинга
        start_ping = time.time()
        await msg.edit("<b>измеряю пинг...</b>", parse_mode='html')
        end_ping = time.time()
        ping_ms = round((end_ping - start_ping) * 1000, 2)
        
        # Добавляем в историю
        ping_history.append(ping_ms)
        if len(ping_history) > 10:  # храним последние 10 замеров
            ping_history.pop(0)
        
        # Считаем статистику
        avg_ping = round(sum(ping_history) / len(ping_history), 2) if ping_history else ping_ms
        min_ping = min(ping_history) if ping_history else ping_ms
        max_ping = max(ping_history) if ping_history else ping_ms
        
        result = f"⛧ Аптайм: {uptime_str}\n⛧ Пинг: {ping_ms} ms\n⛧ Средний: {avg_ping} ms (посл. {len(ping_history)})\n⛧ Мин / Макс: {min_ping} ms / {max_ping} ms"
        await msg.edit(result, parse_mode='html')

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

    # ========== TARGET С ТАЙМЕРОМ ==========
    async def target_handler(self, msg):
        args = await self.get_args(msg)
        if not args:
            await msg.edit("<b>укажи юзернейм или ID и время в минутах\nпример: .target @username 30</b>", parse_mode='html')
            return
        
        parts = args.strip().split()
        if len(parts) < 2:
            await msg.edit("<b>укажи время в минутах\nпример: .target @username 30</b>", parse_mode='html')
            return
        
        target_input = parts[0]
        try:
            minutes = int(parts[1])
        except ValueError:
            await msg.edit("<b>время должно быть числом (минуты)</b>", parse_mode='html')
            return
        
        if minutes < 1:
            await msg.edit("<b>минимальное время - 1 минута</b>", parse_mode='html')
            return
        
        self.target_user = target_input.strip().replace('@', '')
        target_display = target_input
        self.target_chat_id_for_timer = msg.chat_id
        
        if self._target_timer_task and not self._target_timer_task.done():
            self._target_timer_task.cancel()
        
        async def disable_target():
            await asyncio.sleep(minutes * 60)
            if self.target_user:
                display = target_display
                await self.client.send_message(
                    self.target_chat_id_for_timer,
                    f"Время вышло. Цель: {display} отключена"
                )
                self.target_user = None
                self.target_chat_id_for_timer = None
        
        self._target_timer_task = asyncio.create_task(disable_target())
        await msg.edit(f"Цель: {target_input} установлена. Автоотключение через {minutes} минут", parse_mode='html')

    async def tgoff_handler(self, msg):
        if self._target_timer_task and not self._target_timer_task.done():
            self._target_timer_task.cancel()
        self.target_user = None
        self.target_chat_id_for_timer = None
        await msg.edit("<b>Цель отключена</b>", parse_mode='html')

    # ========== SHABLON КОМАНДЫ ==========
    async def shb_handler(self, msg):
        args = await self.get_args(msg)
        if not args:
            await msg.edit("<b>использование: .shb list | .shb load [номер]</b>", parse_mode='html')
            return
        
        parts = args.split()
        cmd = parts[0].lower()
        
        if cmd == 'list':
            # Показываем список доступных шаблонов
            template_files = glob.glob(os.path.join(TEMPLATES_DIR, "*.txt"))
            result = "⛧ Доступные шаблоны:\n\n"
            for tf in template_files:
                name = os.path.basename(tf).replace('.txt', '')
                with open(tf, 'r', encoding='utf-8') as f:
                    count = len([line for line in f.readlines() if line.strip()])
                active = "✅ активен" if name == current_template_name else ""
                result += f"<b><code>{name}</code></b> — {count} фраз {active}\n"
            await msg.edit(result, parse_mode='html')
        
        elif cmd == 'load':
            if len(parts) < 2:
                await msg.edit("<b>укажи номер шаблона\nпример: .shb load 1</b>", parse_mode='html')
                return
            template_name = parts[1]
            if load_template(template_name):
                await msg.edit(f"⛧ Шаблон <b><code>{template_name}</code></b> загружен. {len(current_shablon)} фраз добавлено.", parse_mode='html')
            else:
                await msg.edit(f"⛧ Шаблон <b><code>{template_name}</code></b> не найден.", parse_mode='html')
        else:
            await msg.edit("<b>неизвестная команда. используй: list или load</b>", parse_mode='html')

    # ========== MEDIA КОМАНДЫ ==========
    async def med_handler(self, msg):
        args = await self.get_args(msg)
        if not args:
            await msg.edit("<b>использование:\n.med save [номер] + реплай\n.med list\n.med send [номер]\n.med del [номер]</b>", parse_mode='html')
            return
        
        parts = args.split()
        cmd = parts[0].lower()
        
        if cmd == 'save':
            if len(parts) < 2:
                await msg.edit("<b>укажи номер для сохранения\nпример: .med save 1 + реплай на медиа</b>", parse_mode='html')
                return
            if not msg.is_reply:
                await msg.edit("<b>нужен реплай на медиа</b>", parse_mode='html')
                return
            
            media_id = parts[1]
            reply_msg = await msg.get_reply_message()
            if not reply_msg.media:
                await msg.edit("<b>в ответе нет медиа</b>", parse_mode='html')
                return
            
            try:
                # Определяем расширение
                ext = None
                if reply_msg.photo:
                    ext = 'jpg'
                elif reply_msg.video:
                    ext = 'mp4'
                elif reply_msg.document:
                    mime = reply_msg.document.mime_type
                    if 'video' in mime:
                        ext = 'mp4'
                    elif 'image' in mime:
                        ext = 'jpg'
                    else:
                        ext = 'bin'
                elif reply_msg.gif:
                    ext = 'gif'
                else:
                    ext = 'bin'
                
                file_data = await reply_msg.download_media(bytes)
                save_media(media_id, file_data, ext)
                await msg.edit(f"⛧ Медиа сохранено как <b><code>{media_id}</code></b> (тип: {ext})", parse_mode='html')
            except Exception as e:
                await msg.edit(f"<b>ошибка: {e}</b>", parse_mode='html')
        
        elif cmd == 'list':
            media_list = get_all_media()
            if not media_list:
                await msg.edit("<b>нет сохранённых медиа</b>", parse_mode='html')
                return
            result = "⛧ Сохранённые медиа:\n\n"
            for name, ext, size in media_list:
                size_kb = round(size / 1024, 1)
                result += f"<b><code>{name}</code></b> — {ext} ({size_kb} KB)\n"
            result += f"\n<b><code>.med send [номер]</code></b> — отправить\n<b><code>.med del [номер]</code></b> — удалить"
            await msg.edit(result, parse_mode='html')
        
        elif cmd == 'send':
            if len(parts) < 2:
                await msg.edit("<b>укажи номер медиа\nпример: .med send 1</b>", parse_mode='html')
                return
            media_id = parts[1]
            media_path = get_media_path(media_id)
            if media_path:
                await self.client.send_file(msg.chat_id, media_path)
                await msg.delete()
            else:
                await msg.edit(f"<b>медиа {media_id} не найдено</b>", parse_mode='html')
        
        elif cmd == 'del':
            if len(parts) < 2:
                await msg.edit("<b>укажи номер медиа для удаления\nпример: .med del 1</b>", parse_mode='html')
                return
            media_id = parts[1]
            if delete_media(media_id):
                await msg.edit(f"⛧ Медиа <b><code>{media_id}</code></b> удалено", parse_mode='html')
            else:
                await msg.edit(f"<b>медиа {media_id} не найдено</b>", parse_mode='html')
        
        else:
            await msg.edit("<b>неизвестная команда. используй: save, list, send, del</b>", parse_mode='html')

    # ========== HELP ==========
    async def help_handler(self, msg):
        global mh, name
        me = await self.client.get_me()
        if len(msg.text.split()) > 1:
            mh = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            return await msg.edit("<b>медиа для .help установлено</b>", parse_mode='html')
        caption = menutext.format(name)
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

    # ========== MORE ==========
    async def more_handler(self, msg):
        if mm:
            try:
                await self.client.send_file(msg.chat_id, mm, caption=more_text, parse_mode='html')
                await msg.delete()
            except: await msg.edit(more_text, parse_mode='html')
        else: await msg.edit(more_text, parse_mode='html')

    # ========== CUSTOM ==========
    async def custom_handler(self, msg):
        if mm:
            try:
                await self.client.send_file(msg.chat_id, mm, caption=custom_text, parse_mode='html')
                await msg.delete()
            except: await msg.edit(custom_text, parse_mode='html')
        else: await msg.edit(custom_text, parse_mode='html')

    # ========== RASSET ==========
    async def rasset_handler(self, msg):
        if mm:
            try:
                await self.client.send_file(msg.chat_id, mm, caption=rasset_text, parse_mode='html')
                await msg.delete()
            except: await msg.edit(rasset_text, parse_mode='html')
        else: await msg.edit(rasset_text, parse_mode='html')

    # ========== TIMES ==========
    async def times_handler(self, msg):
        if mm:
            try:
                await self.client.send_file(msg.chat_id, mm, caption=times_text, parse_mode='html')
                await msg.delete()
            except: await msg.edit(times_text, parse_mode='html')
        else: await msg.edit(times_text, parse_mode='html')

    # ========== FILES ==========
    async def files_handler(self, msg):
        if mm:
            try:
                await self.client.send_file(msg.chat_id, mm, caption=files_text, parse_mode='html')
                await msg.delete()
            except: await msg.edit(files_text, parse_mode='html')
        else: await msg.edit(files_text, parse_mode='html')

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

    # ========== POST COMMANDS (исправленный - пересылает все медиа) ==========
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
        
        # Получаем сообщение и все связанные с ним (медиагруппа)
        try:
            # Получаем сообщения вокруг указанного ID (для групп)
            messages = []
            async for m in self.client.iter_messages(entity, offset_id=msg_id, reverse=True, limit=10):
                if m.id == msg_id:
                    messages.append(m)
                elif m.grouped_id and m.grouped_id == getattr(await self.client.get_messages(entity, ids=msg_id), 'grouped_id', None):
                    messages.append(m)
                else:
                    break
            
            if not messages:
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
            'message_ids': [m.id for m in messages]
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
                    # Пересылаем все сообщения из группы
                    await self.client.forward_messages(chat_id, messages=data['message_ids'], from_peer=data['entity'])
                    await asyncio.sleep(2)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    print(f"Ошибка пересылки: {e}")
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
рассылки (poste): {len(poste_list)} активных
блок-лист (pblk): {len(poste_blocklist)} чатов
цель (target): {target_info}
детекты: {sum(len(v) for v in detect_list.values())} активных
активный шаблон: {current_template_name} ({len(current_shablon)} фраз)

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
        global spam_state, tagger_chats, poste_list, detect_list
        
        spam_state.clear()
        tagger_chats.clear()
        
        for link in list(poste_list.keys()):
            poste_list[link]['running'] = False
        poste_list.clear()
        
        for chat_id, users in detect_list.items():
            for user_id, data in users.items():
                task = data.get('task')
                if task and not task.done():
                    task.cancel()
        detect_list.clear()
        
        if self._target_timer_task and not self._target_timer_task.done():
            self._target_timer_task.cancel()
        self.target_user = None
        self.target_chat_id_for_timer = None
        
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
            elif text.startswith('.shb'): await self.shb_handler(msg)
            elif text.startswith('.med'): await self.med_handler(msg)
            elif text.startswith('.help'): await self.help_handler(msg)
            elif text.startswith('.menu'): await self.menu_handler(msg)
            elif text.startswith('.more'): await self.more_handler(msg)
            elif text.startswith('.custom'): await self.custom_handler(msg)
            elif text.startswith('.rasset'): await self.rasset_handler(msg)
            elif text.startswith('.times'): await self.times_handler(msg)
            elif text.startswith('.files'): await self.files_handler(msg)
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
