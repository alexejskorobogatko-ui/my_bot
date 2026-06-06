# -*- coding: utf-8 -*-
import os
import sys
import time
import asyncio
import threading
import glob
import re
from random import choice
from datetime import datetime, timedelta

import requests
import g4f

from flask import Flask
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, RPCError
from telethon.tl.functions.channels import GetParticipantsRequest, JoinChannelRequest
from telethon.tl.types import ChannelParticipantsSearch, MessageEntityMentionName
from telethon.tl.functions.messages import ImportChatInviteRequest

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
LOG_CHAT_FILE = "log_chat.txt"
GPT_CHATS_FILE = "gpt_chats.txt"

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

default_template_path = os.path.join(TEMPLATES_DIR, "main.txt")
if not os.path.exists(default_template_path):
    with open(default_template_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(DEFAULT_SHABLON))

# ==================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ====================
spam_state = {}
start_time = time.time()
tagger_chats = {}
autodel_tasks = {}
mid = 'https://x0.at/cUQa.jpg'
name = "Ralvatron"
mh = 'https://x0.at/5-ku.mp4'
mm = 'https://x0.at/5-ku.mp4'
cmds = 'https://x0.at/Dv0D.jpg'
status_media = None

# ========== ЛОГ-ЧАТ ==========
log_chat_id = None

def load_log_chat():
    global log_chat_id
    if os.path.exists(LOG_CHAT_FILE):
        try:
            with open(LOG_CHAT_FILE, 'r') as f:
                chat_ref = f.read().strip()
                if chat_ref:
                    log_chat_id = chat_ref
        except:
            pass

def save_log_chat(chat_ref):
    with open(LOG_CHAT_FILE, 'w') as f:
        f.write(chat_ref)

load_log_chat()

# ========== АКТИВНЫЕ ПОИСКИ .DETECT ==========
active_searches = {}

# ========== РЕЖИМ НЕЙРОСЕТИ (GPT) ==========
gpt_enabled_chats = set()

def load_gpt_chats():
    global gpt_enabled_chats
    if os.path.exists(GPT_CHATS_FILE):
        try:
            with open(GPT_CHATS_FILE, 'r') as f:
                for line in f:
                    chat_id = line.strip()
                    if chat_id:
                        gpt_enabled_chats.add(int(chat_id))
        except:
            pass

def save_gpt_chat(chat_id):
    with open(GPT_CHATS_FILE, 'a') as f:
        f.write(f"{chat_id}\n")

def remove_gpt_chat(chat_id):
    if os.path.exists(GPT_CHATS_FILE):
        with open(GPT_CHATS_FILE, 'r') as f:
            lines = f.readlines()
        with open(GPT_CHATS_FILE, 'w') as f:
            for line in lines:
                if line.strip() != str(chat_id):
                    f.write(line)

load_gpt_chats()

# ========== ТЕКУЩИЙ ШАБЛОН ==========
current_shablon = []
current_template_name = "main"

def load_template(template_name):
    global current_shablon, current_template_name
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.txt")
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            current_shablon = [line.strip() for line in f.readlines() if line.strip()]
        current_template_name = template_name
        return True
    return False

def save_template(template_name, content):
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.txt")
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return True

def delete_template(template_name):
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.txt")
    if os.path.exists(template_path):
        os.remove(template_path)
        return True
    return False

def get_all_templates():
    files = glob.glob(os.path.join(TEMPLATES_DIR, "*.txt"))
    result = []
    for f in files:
        name = os.path.basename(f).replace('.txt', '')
        with open(f, 'r', encoding='utf-8') as tf:
            count = len([line for line in tf.readlines() if line.strip()])
        result.append((name, count))
    return result

load_template("main")

# ========== МЕДИА ХРАНИЛИЩЕ ==========
def get_media_path(media_id):
    pattern = os.path.join(MEDIA_DIR, f"{media_id}.*")
    files = glob.glob(pattern)
    if files:
        return files[0]
    return None

def save_media(media_id, file_data, extension):
    file_path = os.path.join(MEDIA_DIR, f"{media_id}.{extension}")
    with open(file_path, 'wb') as f:
        f.write(file_data)
    return file_path

def delete_media(media_id):
    file_path = get_media_path(media_id)
    if file_path:
        os.remove(file_path)
        return True
    return False

def get_all_media():
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
"""

menu = """
⛧ Спам и теггер ⛧

<b><code>.avt + время + реплай</code></b> — спам в чат
<b><code>.stop [chat_id]</code></b> — остановить спам
<b><code>.tagger + айди + время + реплай</code></b> — теггер
<b><code>.off [chat_id]</code></b> — остановить теггер
<b><code>.clr + время + реплай</code></b> — календарь
<b><code>.clroff</code></b> — остановить календарь
"""

more_text = """
✮ Дополнительные функции ✮

<b><code>.shb list</code></b> — список шаблонов фраз
<b><code>.shb load [название]</code></b> — загрузить шаблон
<b><code>.shb save</code></b> + реплай на TXT — сохранить шаблон
<b><code>.shb del [название]</code></b> — удалить шаблон
<b><code>.med save [номер]</code></b> + реплай — сохранить медиа
<b><code>.med list</code></b> — список медиа
<b><code>.med send [номер]</code></b> — отправить медиа
<b><code>.med del [номер]</code></b> — удалить медиа
<b><code>.autodel + время</code></b> — автоудаление сообщений бота
<b><code>.scrape + Chat ID</code></b> — выгрузка списка чата
<b><code>.check + реплай</code></b> — проверка транслитерации
<b><code>.log [ссылка/username/id]</code></b> — установить лог-чат для ошибок
<b><code>.detect [текст]</code></b> — поиск фразы во всех чатах
<b><code>.detectoff [номер]</code></b> — остановить поиск
<b><code>.detectlist</code></b> — список активных поисков
<b><code>.gpt + реплай</code></b> — включить режим нейросети в чате
<b><code>.gptoff</code></b> — выключить режим нейросети
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
<b><code>.clroff</code></b> — остановить календарь

✮ Поиск по чатам ✮
<b><code>.detect [текст]</code></b> — поиск фразы во всех чатах
<b><code>.detectoff [номер]</code></b> — остановить поиск
<b><code>.detectlist</code></b> — список активных поисков

✮ Постинг ✮
<b><code>.poste 'ссылка' минуты</code></b> — пересылка поста
<b><code>.poste_stop</code></b> — остановить все
<b><code>.poste_list</code></b> — список активных рассылок
<b><code>.pblk list/add/del/clear</code></b> — блок-лист
<b><code>.log [ссылка/username/id]</code></b> — лог-чат для ошибок

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
<b><code>.shb load [название]</code></b> — загрузить шаблон
<b><code>.shb save</code></b> + реплай на TXT — сохранить шаблон
<b><code>.shb del [название]</code></b> — удалить шаблон

✮ Нейросеть ✮
<b><code>.gpt + реплай</code></b> — включить режим нейросети в чате
<b><code>.gptoff</code></b> — выключить режим нейросети

⛧ Владелец: @misosphere
"""

# ==================== КЛАСС ЮЗЕРБОТА ====================
class Userbot:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        self.target_user = None
        self._target_timer_task = None
        self.target_chat_id_for_timer = None
        self.active_calendars = {}

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

    async def resolve_log_chat(self, chat_ref):
        """Преобразует username, ID или ссылку-приглашение в chat_id"""
        chat_ref = chat_ref.strip()
        
        # Если это ссылка-приглашение
        if 't.me/joinchat' in chat_ref or 't.me/+-' in chat_ref or 't.me/+' in chat_ref:
            try:
                if 't.me/joinchat/' in chat_ref:
                    hash_part = chat_ref.split('t.me/joinchat/')[-1].split('?')[0]
                elif 't.me/+-' in chat_ref:
                    hash_part = chat_ref.split('t.me/+-')[-1].split('?')[0]
                else:
                    hash_part = chat_ref.split('t.me/+')[-1].split('?')[0]
                
                updates = await self.client(ImportChatInviteRequest(hash_part))
                if updates.chats:
                    chat_id = updates.chats[0].id
                    return chat_id
            except Exception as e:
                print(f"Ошибка вступления по ссылке: {e}")
        
        # Если это ID (начинается с -100 или просто число)
        if chat_ref.lstrip('-').isdigit():
            try:
                entity = await self.client.get_entity(int(chat_ref))
                return entity.id
            except:
                pass
        
        # Если это username
        if chat_ref.startswith('@'):
            try:
                entity = await self.client.get_entity(chat_ref)
                return entity.id
            except:
                pass
        
        # Пробуем получить как есть
        try:
            entity = await self.client.get_entity(chat_ref)
            return entity.id
        except:
            pass
        
        return None

    # ========== ПАРСИНГ MED: И ТЕКСТА ==========
    def parse_media_and_text(self, args_list):
        media_id = None
        media_url = None
        text_parts = []
        for arg in args_list:
            if arg.startswith('med:'):
                try:
                    media_id = arg.split(':')[1]
                except:
                    pass
            elif arg.startswith('http://') or arg.startswith('https://'):
                media_url = arg
            else:
                text_parts.append(arg)
        return media_id, media_url, ' '.join(text_parts)

    # ========== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ МЕДИА ==========
    async def get_media_to_send(self, media_id, media_url):
        """Возвращает путь к файлу для отправки"""
        if media_id:
            return get_media_path(media_id)
        elif media_url:
            # Скачиваем по ссылке
            try:
                response = requests.get(media_url, timeout=30)
                if response.status_code == 200:
                    # Сохраняем во временный файл
                    temp_file = f"temp_media_{int(time.time())}"
                    ext = media_url.split('.')[-1].split('?')[0]
                    if len(ext) > 5:
                        ext = 'bin'
                    temp_path = os.path.join(MEDIA_DIR, f"{temp_file}.{ext}")
                    with open(temp_path, 'wb') as f:
                        f.write(response.content)
                    return temp_path
            except Exception as e:
                print(f"Ошибка скачивания по ссылке: {e}")
        return None

    # ========== СПАМ ==========
    async def renewal_handler(self, msg):
        global spam_state
        args = await self.get_args(msg)
        if not args:
            await msg.edit("<b>аргументы не указаны. Пример: .avt 5 med:1 ебал твою мать</b>", parse_mode='html')
            return
        
        parts = args.split()
        try:
            time_val = int(parts[0])
        except ValueError:
            await msg.edit("<b>первый аргумент должен быть числом (секунды)</b>", parse_mode='html')
            return
        if time_val < 3:
            await msg.edit("<b>мин. задержка - 3 секунды</b>", parse_mode='html')
            return
        
        media_id, media_url, custom_text = self.parse_media_and_text(parts[1:])
        media_path = await self.get_media_to_send(media_id, media_url)
        
        reply = await msg.get_reply_message()
        chat_id = msg.chat_id
        
        spam_state[chat_id] = True
        await msg.edit(f'<b>Спам включен\nВыкл: <code>.stop {chat_id}</code></b>', parse_mode='html')
        
        while chat_id in spam_state and spam_state[chat_id]:
            try:
                random_phrase = choice(current_shablon) if current_shablon else ""
                if custom_text:
                    send_text = f"{custom_text} {random_phrase}".strip()
                else:
                    send_text = random_phrase
                
                if media_path:
                    await msg.respond(send_text, file=media_path, reply_to=reply.id if reply else None)
                else:
                    await msg.respond(send_text, reply_to=reply.id if reply else None)
            except Exception as e:
                print(f"Спам ошибка: {e}")
            await asyncio.sleep(time_val)
        
        if chat_id in spam_state:
            del spam_state[chat_id]
        
        # Удаляем временный файл
        if media_url and media_path and os.path.exists(media_path):
            try:
                os.remove(media_path)
            except:
                pass

    # ========== КАЛЕНДАРЬ ==========
    async def kalendar_handler(self, msg):
        args = await self.get_args(msg)
        if not args:
            await msg.edit("<b>аргументы: время [med:номер] [текст]\nПример: .clr 10 med:1 ебал твою мать</b>", parse_mode='html')
            return
        
        parts = args.split()
        try:
            time_val = int(parts[0])
        except ValueError:
            await msg.edit("<b>первый аргумент должен быть числом (минуты)</b>", parse_mode='html')
            return
        
        if time_val < 1:
            await msg.edit("<b>интервал не может быть меньше 1 минуты</b>", parse_mode='html')
            return
        
        media_id, media_url, custom_text = self.parse_media_and_text(parts[1:])
        media_path = await self.get_media_to_send(media_id, media_url)
        
        random_phrase = choice(current_shablon) if current_shablon else ""
        if custom_text:
            send_text = f"{custom_text} {random_phrase}".strip()
        else:
            send_text = random_phrase
        
        chat_id = msg.chat_id
        
        if chat_id in self.active_calendars:
            self.active_calendars[chat_id].cancel()
        
        async def calendar_task():
            start_time = time.time()
            messages_sent = 0
            total_messages = 100
            
            if media_path:
                await msg.respond(send_text, file=media_path)
            else:
                await msg.respond(send_text)
            messages_sent += 1
            
            for i in range(total_messages - 1):
                if chat_id not in self.active_calendars:
                    break
                schedule_date = datetime.now() + timedelta(minutes=time_val)
                try:
                    if media_path:
                        await msg.respond(send_text, file=media_path, schedule=schedule_date.timestamp())
                    else:
                        await msg.respond(send_text, schedule=schedule_date.timestamp())
                    messages_sent += 1
                except Exception as e:
                    print(f"Календарь ошибка: {e}")
                await asyncio.sleep(0.5)
            
            elapsed = int(time.time() - start_time)
            elapsed_str = str(timedelta(seconds=elapsed))
            report = f"<b>⛧ КАЛЕНДАРЬ ЗАВЕРШЁН ⛧</b>\n\n<b>Всего сообщений:</b> {messages_sent}\n<b>Время работы:</b> {elapsed_str}\n<b>Интервал:</b> {time_val} мин"
            await msg.respond(report, parse_mode='html')
            
            if chat_id in self.active_calendars:
                del self.active_calendars[chat_id]
            
            # Удаляем временный файл
            if media_url and media_path and os.path.exists(media_path):
                try:
                    os.remove(media_path)
                except:
                    pass
        
        task = asyncio.create_task(calendar_task())
        self.active_calendars[chat_id] = task
        await msg.edit(f"<b>Календарь запущен\nИнтервал: {time_val} мин\nОстановить: .clroff</b>", parse_mode='html')

    async def clroff_handler(self, msg):
        chat_id = msg.chat_id
        if chat_id in self.active_calendars:
            self.active_calendars[chat_id].cancel()
            del self.active_calendars[chat_id]
            await msg.edit("<b>Календарь остановлен</b>", parse_mode='html')
        else:
            await msg.edit("<b>Активный календарь не найден</b>", parse_mode='html')

    # ========== ТЕГГЕР ==========
    async def tagger_handler(self, msg):
        args = await self.get_args(msg)
        if not args:
            await msg.edit("<b>аргументы: user_id время [med:номер] [текст]\nПример: .tagger 123456789 5 med:1 ебал твою мать</b>", parse_mode='html')
            return
        
        parts = args.split()
        if len(parts) < 2:
            await msg.edit("<b>укажи user_id и время</b>", parse_mode='html')
            return
        
        try:
            user_id = int(parts[0])
            time_val = int(parts[1])
        except ValueError:
            await msg.edit("<b>user_id и время должны быть числами</b>", parse_mode='html')
            return
        
        if time_val < 3:
            await msg.edit("<b>мин. задержка - 3 секунды</b>", parse_mode='html')
            return
        
        media_id, media_url, custom_text = self.parse_media_and_text(parts[2:])
        media_path = await self.get_media_to_send(media_id, media_url)
        
        reply_to_msg = await msg.get_reply_message()
        chat_id = reply_to_msg.chat_id if reply_to_msg else msg.chat_id
        
        tagger_chats[chat_id] = True
        await msg.edit(f'<b>Теггер включен\nВыкл: <code>.off {chat_id}</code></b>', parse_mode='html')
        
        while chat_id in tagger_chats:
            random_phrase = choice(current_shablon) if current_shablon else ""
            if custom_text:
                base_text = f"{custom_text} {random_phrase}".strip()
            else:
                base_text = random_phrase
            text = f"{base_text} <a href='tg://user?id={user_id}'>{choice(current_shablon)}</a>"
            try:
                if media_path:
                    await self.client.send_file(chat_id, media_path, caption=text, parse_mode='html')
                else:
                    await self.client.send_message(chat_id, text, parse_mode='html')
            except Exception as e:
                print(f"Теггер ошибка: {e}")
            await asyncio.sleep(time_val)
        
        if chat_id in tagger_chats:
            del tagger_chats[chat_id]
        
        # Удаляем временный файл
        if media_url and media_path and os.path.exists(media_path):
            try:
                os.remove(media_path)
            except:
                pass

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
            result = f"<b>результат:</b>\n<b>слов:</b> {total_words}\n<b>символов:</b> {total_chars}\n<b>строк:</b> {total_lines}"
            await msg.edit(result, parse_mode='html')
        else:
            await msg.edit("<b>нужен реплай на сообщение</b>", parse_mode='html')

    # ========== ЗАГРУЗКА ШАБЛОНА ==========
    async def load_handler(self, msg):
        global current_shablon, current_template_name
        if msg.is_reply:
            reply_msg = await msg.get_reply_message()
            if reply_msg.file:
                file = await reply_msg.download_media()
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        current_shablon.clear()
                        current_shablon.extend([line.strip() for line in f.readlines() if line.strip()])
                    current_template_name = "loaded_from_file"
                    await msg.edit("<b>Шаблон успешно загружен!</b>", parse_mode='html')
                except Exception as e:
                    await msg.edit(f"<b>Ошибка при загрузке: {e}</b>", parse_mode='html')
                finally:
                    os.remove(file)
            else:
                await msg.edit("<b>В ответе нет файла</b>", parse_mode='html')
        else:
            await msg.edit("<b>Сделай реплай на текстовый файл с шаблоном</b>", parse_mode='html')

    # ========== ВЫГРУЗКА ШАБЛОНА ==========
    async def file_handler(self, msg):
        with open('texts.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(current_shablon))
        await self.client.send_file(msg.chat_id, 'texts.txt')
        os.remove('texts.txt')
        await msg.delete()

    # ========== PING ==========
    async def ping_handler(self, msg):
        global ping_history
        bot_runtime = int(time.time() - start_time)
        uptime_str = str(timedelta(seconds=bot_runtime))
        
        start_ping = time.time()
        await msg.edit("<b>измеряю пинг...</b>", parse_mode='html')
        end_ping = time.time()
        ping_ms = round((end_ping - start_ping) * 1000, 2)
        
        ping_history.append(ping_ms)
        if len(ping_history) > 10:
            ping_history.pop(0)
        
        avg_ping = round(sum(ping_history) / len(ping_history), 2) if ping_history else ping_ms
        min_ping = min(ping_history) if ping_history else ping_ms
        max_ping = max(ping_history) if ping_history else ping_ms
        
        result = f"<b>⛧ Аптайм:</b> {uptime_str}\n<b>⛧ Пинг:</b> {ping_ms} ms\n<b>⛧ Средний:</b> {avg_ping} ms (посл. {len(ping_history)})\n<b>⛧ Мин / Макс:</b> {min_ping} ms / {max_ping} ms"
        await msg.edit(result, parse_mode='html')

    # ========== ОСТАНОВКА СПАМА И ТЕГГЕРА ==========
    async def stop_handler(self, msg):
        global spam_state
        args = await self.get_args(msg)
        chat_id = int(args.split()[0]) if args else msg.chat_id
        if chat_id in spam_state:
            del spam_state[chat_id]
            await msg.edit(f"<b>Спам в чате <code>{chat_id}</code> остановлен</b>", parse_mode='html')
        else:
            await msg.edit(f"<b>Спам в чате <code>{chat_id}</code> не был активен</b>", parse_mode='html')

    async def off_handler(self, msg):
        global tagger_chats
        args = await self.get_args(msg)
        chat_id = int(args.split()[0]) if args else msg.chat_id
        if chat_id in tagger_chats:
            del tagger_chats[chat_id]
            await msg.edit(f"<b>Теггер в чате <code>{chat_id}</code> остановлен</b>", parse_mode='html')
        else:
            await msg.edit(f"<b>Теггер в чате <code>{chat_id}</code> не был активен</b>", parse_mode='html')

    # ========== TARGET ==========
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
                await self.client.send_message(
                    self.target_chat_id_for_timer,
                    f"<b>Время вышло. Цель: {target_display} отключена</b>",
                    parse_mode='html'
                )
                self.target_user = None
                self.target_chat_id_for_timer = None
        
        self._target_timer_task = asyncio.create_task(disable_target())
        await msg.edit(f"<b>Цель: {target_input} установлена. Автоотключение через {minutes} минут</b>", parse_mode='html')

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
            await msg.edit("<b>использование:\n.shb list\n.shb load [название]\n.shb save + реплай на TXT\n.shb del [название]</b>", parse_mode='html')
            return
        
        parts = args.split()
        cmd = parts[0].lower()
        
        if cmd == 'list':
            templates = get_all_templates()
            if not templates:
                await msg.edit("<b>Нет сохранённых шаблонов</b>", parse_mode='html')
                return
            result = "<b>⛧ Доступные шаблоны:</b>\n\n"
            for name, count in templates:
                active = " ✅ активен" if name == current_template_name else ""
                result += f"<b><code>{name}</code></b> — {count} фраз{active}\n"
            await msg.edit(result, parse_mode='html')
        
        elif cmd == 'load':
            if len(parts) < 2:
                await msg.edit("<b>укажи название шаблона\nпример: .shb load main</b>", parse_mode='html')
                return
            template_name = parts[1]
            if load_template(template_name):
                await msg.edit(f"<b>⛧ Шаблон <code>{template_name}</code> загружен. {len(current_shablon)} фраз добавлено.</b>", parse_mode='html')
            else:
                await msg.edit(f"<b>⛧ Шаблон <code>{template_name}</code> не найден.</b>", parse_mode='html')
        
        elif cmd == 'save':
            if not msg.is_reply:
                await msg.edit("<b>нужен реплай на текстовый файл (.txt)</b>", parse_mode='html')
                return
            reply_msg = await msg.get_reply_message()
            if not reply_msg.file:
                await msg.edit("<b>в ответе нет файла</b>", parse_mode='html')
                return
            
            if len(parts) >= 2:
                template_name = parts[1]
            else:
                template_name = os.path.splitext(os.path.basename(reply_msg.file.name))[0] if reply_msg.file.name else "new_template"
            
            file_path = await reply_msg.download_media()
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                save_template(template_name, content)
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                await msg.edit(f"<b>⛧ Шаблон <code>{template_name}</code> сохранён. {len(lines)} фраз.</b>", parse_mode='html')
            except Exception as e:
                await msg.edit(f"<b>Ошибка при сохранении: {e}</b>", parse_mode='html')
            finally:
                os.remove(file_path)
        
        elif cmd == 'del':
            if len(parts) < 2:
                await msg.edit("<b>укажи название шаблона для удаления\nпример: .shb del main</b>", parse_mode='html')
                return
            template_name = parts[1]
            if template_name == "main":
                await msg.edit("<b>Нельзя удалить основной шаблон 'main'</b>", parse_mode='html')
                return
            if delete_template(template_name):
                await msg.edit(f"<b>⛧ Шаблон <code>{template_name}</code> удалён.</b>", parse_mode='html')
            else:
                await msg.edit(f"<b>⛧ Шаблон <code>{template_name}</code> не найден.</b>", parse_mode='html')
        
        else:
            await msg.edit("<b>неизвестная команда. используй: list, load, save, del</b>", parse_mode='html')

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
                await msg.edit(f"<b>⛧ Медиа сохранено как <code>{media_id}</code> (тип: {ext})</b>", parse_mode='html')
            except Exception as e:
                await msg.edit(f"<b>ошибка: {e}</b>", parse_mode='html')
        
        elif cmd == 'list':
            media_list = get_all_media()
            if not media_list:
                await msg.edit("<b>нет сохранённых медиа</b>", parse_mode='html')
                return
            result = "<b>⛧ Сохранённые медиа:</b>\n\n"
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
                await msg.edit(f"<b>⛧ Медиа <code>{media_id}</code> удалено</b>", parse_mode='html')
            else:
                await msg.edit(f"<b>медиа {media_id} не найдено</b>", parse_mode='html')
        
        else:
            await msg.edit("<b>неизвестная команда. используй: save, list, send, del</b>", parse_mode='html')

    # ========== SCRAPE ==========
    async def scrape_handler(self, msg):
        args = await self.get_args(msg)
        if not args:
            await msg.edit("<b>использование: .scrape @username или .scrape chat_id</b>", parse_mode='html')
            return
        
        try:
            entity = await self.client.get_entity(args)
            if not entity:
                await msg.edit("<b>Не удалось найти чат</b>", parse_mode='html')
                return
            
            await msg.edit("<b>Собираю список участников, подожди...</b>", parse_mode='html')
            
            users = []
            async for user in self.client.iter_participants(entity):
                if user.username:
                    users.append(f"@{user.username}")
                elif user.first_name:
                    users.append(f"{user.first_name} {user.last_name or ''} (ID: {user.id})")
                else:
                    users.append(f"ID: {user.id}")
            
            if not users:
                await msg.edit("<b>Не удалось получить список участников (возможно, чат приватный)</b>", parse_mode='html')
                return
            
            filename = f"scrape_{entity.id}_{int(time.time())}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(users))
            
            await self.client.send_file(msg.chat_id, filename, caption=f"<b>Список участников {entity.title if hasattr(entity, 'title') else args}: {len(users)} человек</b>")
            os.remove(filename)
            await msg.delete()
            
        except Exception as e:
            await msg.edit(f"<b>Ошибка: {e}</b>", parse_mode='html')

    # ========== AUTODEL ==========
    async def autodel_handler(self, msg):
        args = await self.get_args(msg)
        if not args:
            await msg.edit("<b>использование: .autodel + время в секундах</b>", parse_mode='html')
            return
        
        try:
            delay = int(args)
        except ValueError:
            await msg.edit("<b>время должно быть числом (секунды)</b>", parse_mode='html')
            return
        
        if delay < 5:
            await msg.edit("<b>минимальная задержка - 5 секунд</b>", parse_mode='html')
            return
        
        chat_id = msg.chat_id
        if chat_id in autodel_tasks:
            autodel_tasks[chat_id].cancel()
        
        async def auto_delete():
            await asyncio.sleep(delay)
            try:
                async for message in self.client.iter_messages(chat_id, from_user='me'):
                    await message.delete()
                    await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Autodel ошибка: {e}")
            finally:
                if chat_id in autodel_tasks:
                    del autodel_tasks[chat_id]
        
        task = asyncio.create_task(auto_delete())
        autodel_tasks[chat_id] = task
        await msg.edit(f"<b>Автоудаление сообщений включено. Все сообщения бота в этом чате будут удалены через {delay} сек.</b>", parse_mode='html')

    # ========== CHECK ==========
    async def check_handler(self, msg):
        if not msg.is_reply:
            await msg.edit("<b>нужен реплай на текст для проверки транслитерации</b>", parse_mode='html')
            return
        
        reply_msg = await msg.get_reply_message()
        text = reply_msg.text
        if not text:
            await msg.edit("<b>в сообщении нет текста</b>", parse_mode='html')
            return
        
        cyrillic = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
        has_cyrillic = any(c in cyrillic for c in text.lower())
        
        if has_cyrillic:
            await msg.edit("<b>Текст написан кириллицей. Транслитерации нет.</b>", parse_mode='html')
        else:
            await msg.edit("<b>Текст на латинице, похож на английский.</b>", parse_mode='html')

    # ========== LOG ==========
    async def log_handler(self, msg):
        global log_chat_id
        args = await self.get_args(msg)
        
        if not args:
            if log_chat_id:
                try:
                    entity = await self.client.get_entity(log_chat_id)
                    chat_name = entity.title if hasattr(entity, 'title') else entity.first_name
                    await msg.edit(f"<b>⛧ Текущий лог-чат ⛧</b>\n\n<b>Чат:</b> {chat_name} ({log_chat_id})", parse_mode='html')
                except:
                    await msg.edit(f"<b>⛧ Текущий лог-чат ⛧</b>\n\n<b>Сохранённый ID:</b> {log_chat_id}", parse_mode='html')
            else:
                await msg.edit("<b>Лог-чат не установлен\nУстановите: .log @username или .log chat_id или .log ссылка</b>", parse_mode='html')
            return
        
        chat_ref = args.strip()
        chat_id = await self.resolve_log_chat(chat_ref)
        
        if chat_id:
            log_chat_id = str(chat_id)
            save_log_chat(log_chat_id)
            try:
                entity = await self.client.get_entity(chat_id)
                chat_name = entity.title if hasattr(entity, 'title') else entity.first_name
                await msg.edit(f"<b>⛧ Лог ошибок установлен ⛧</b>\n\n<b>Чат для логов:</b> {chat_name} ({chat_id})", parse_mode='html')
            except:
                await msg.edit(f"<b>⛧ Лог ошибок установлен ⛧</b>\n\n<b>Чат для логов:</b> {chat_id}", parse_mode='html')
        else:
            await msg.edit("<b>⛧ Ошибка установки лог-чата ⛧</b>\n\n<b>Причина:</b> Не удалось найти чат. Убедитесь, что ваш аккаунт является участником этого чата, и попробуйте снова.", parse_mode='html')

    # ========== НЕЙРОСЕТЬ (GPT) ==========
    async def gpt_handler(self, msg):
        global gpt_enabled_chats
        
        # Проверяем, есть ли реплай (для включения)
        if msg.is_reply:
            chat_id = msg.chat_id
            if chat_id not in gpt_enabled_chats:
                gpt_enabled_chats.add(chat_id)
                save_gpt_chat(chat_id)
                await msg.edit("<b>⛧ Режим нейросети включён ⛧</b>\n\nТеперь бот будет отвечать на все сообщения в этом чате через нейросеть.\n\n<b>Выключить:</b> .gptoff", parse_mode='html')
            else:
                await msg.edit("<b>Режим нейросети уже включён в этом чате</b>", parse_mode='html')
        else:
            await msg.edit("<b>Сделай реплай на любое сообщение, чтобы включить режим нейросети\nПример: .gpt + реплай</b>", parse_mode='html')

    async def gptoff_handler(self, msg):
        global gpt_enabled_chats
        chat_id = msg.chat_id
        if chat_id in gpt_enabled_chats:
            gpt_enabled_chats.discard(chat_id)
            remove_gpt_chat(chat_id)
            await msg.edit("<b>⛧ Режим нейросети выключен ⛧</b>", parse_mode='html')
        else:
            await msg.edit("<b>Режим нейросети не был включён в этом чате</b>", parse_mode='html')

    async def gpt_respond(self, msg):
        """Отвечает на сообщение через нейросеть"""
        chat_id = msg.chat_id
        if chat_id not in gpt_enabled_chats:
            return
        
        user_text = msg.text
        if not user_text or user_text.startswith('.'):
            return
        
        # Показываем, что бот печатает
        async with self.client.action(chat_id, 'typing'):
            try:
                # Генерируем ответ через g4f
                response = g4f.ChatCompletion.create(
                    model=g4f.models.gpt_4o_mini,
                    messages=[{"role": "user", "content": user_text}]
                )
                if response and len(response) > 0:
                    # Обрезаем слишком длинные ответы
                    if len(response) > 4000:
                        response = response[:4000] + "..."
                    await msg.reply(response, parse_mode='html')
                else:
                    await msg.reply("<b>Не удалось получить ответ от нейросети</b>", parse_mode='html')
            except Exception as e:
                print(f"GPT ошибка: {e}")
                await msg.reply(f"<b>Ошибка нейросети: {e}</b>", parse_mode='html')

    # ========== DETECT (ПОИСК ПО ВСЕМ ЧАТАМ) ==========
    async def detect_handler(self, msg):
        args = await self.get_args(msg)
        if not args:
            await msg.edit("<b>использование: .detect текст_для_поиска</b>", parse_mode='html')
            return
        
        phrase = args.strip()
        if len(phrase) < 3:
            await msg.edit("<b>фраза должна содержать минимум 3 символа</b>", parse_mode='html')
            return
        
        search_id = len(active_searches) + 1
        original_chat_id = msg.chat_id
        
        await msg.edit(f"<b>⛧ Поиск запущен ⛧</b>\n\n<b>Фраза:</b> {phrase}\n<b>Статус:</b> поиск...\n<b>ID поиска:</b> {search_id}\n\nРезультаты появятся здесь по мере нахождения.", parse_mode='html')
        
        results = []
        
        async def search_task():
            nonlocal results
            try:
                dialogs = await self.client.get_dialogs()
                for dialog in dialogs:
                    if not active_searches.get(search_id, {}).get('active', True):
                        break
                    
                    try:
                        async for message in self.client.iter_messages(dialog.id, limit=500, search=phrase):
                            if not active_searches.get(search_id, {}).get('active', True):
                                break
                            
                            if message.text and phrase.lower() in message.text.lower():
                                chat_title = dialog.title or "Личный чат"
                                chat_id = dialog.id
                                sender = await message.get_sender()
                                sender_name = sender.first_name if sender else "Unknown"
                                sender_username = f"@{sender.username}" if sender and sender.username else ""
                                message_link = f"https://t.me/c/{str(chat_id)[4:]}/{message.id}" if str(chat_id).startswith('-100') else f"https://t.me/{dialog.entity.username}/{message.id}" if dialog.entity.username else None
                                
                                result = {
                                    'chat_title': chat_title,
                                    'chat_id': chat_id,
                                    'sender_name': sender_name,
                                    'sender_username': sender_username,
                                    'text': message.text[:200],
                                    'link': message_link
                                }
                                results.append(result)
                                
                                if len(results) >= 15:
                                    break
                            
                            await asyncio.sleep(0.1)
                    except Exception as e:
                        print(f"Ошибка при поиске в чате {dialog.id}: {e}")
                    
                    if len(results) >= 15:
                        break
                    
                    await asyncio.sleep(0.5)
                
                report = f"<b>⛧ РЕЗУЛЬТАТ ПОИСКА ⛧</b>\n\n<b>Фраза:</b> {phrase}\n"
                
                if results:
                    report += f"\n<b>Найдено в чатах ({len(results)}):</b>\n\n"
                    for i, res in enumerate(results, 1):
                        report += f"{i}. <b>Чат:</b> {res['chat_title']} (ID: {res['chat_id']})\n"
                        report += f"   <b>Автор:</b> {res['sender_name']} {res['sender_username']}\n"
                        report += f"   <b>Текст:</b> {res['text']}\n"
                        if res['link']:
                            report += f"   <b>Ссылка:</b> {res['link']}\n"
                        report += "\n"
                else:
                    report += f"\n<b>Результат:</b> не найдено ни одного совпадения\n"
                
                try:
                    await msg.edit(report, parse_mode='html')
                except Exception as e:
                    print(f"Ошибка отправки отчёта: {e}")
                
                if search_id in active_searches:
                    del active_searches[search_id]
                    
            except Exception as e:
                await msg.edit(f"<b>Ошибка при поиске: {e}</b>", parse_mode='html')
                if search_id in active_searches:
                    del active_searches[search_id]
        
        task = asyncio.create_task(search_task())
        active_searches[search_id] = {
            'task': task,
            'phrase': phrase,
            'chat_id': original_chat_id,
            'active': True
        }

    async def detectoff_handler(self, msg):
        args = await self.get_args(msg)
        
        if not args:
            count = 0
            for sid in list(active_searches.keys()):
                if active_searches[sid].get('active', False):
                    active_searches[sid]['active'] = False
                    if active_searches[sid].get('task'):
                        active_searches[sid]['task'].cancel()
                    del active_searches[sid]
                    count += 1
            if count > 0:
                await msg.edit(f"<b>Остановлено {count} активных поисков</b>", parse_mode='html')
            else:
                await msg.edit("<b>Нет активных поисков для остановки</b>", parse_mode='html')
            return
        
        try:
            search_id = int(args.strip())
            if search_id in active_searches:
                active_searches[search_id]['active'] = False
                if active_searches[search_id].get('task'):
                    active_searches[search_id]['task'].cancel()
                phrase = active_searches[search_id]['phrase']
                del active_searches[search_id]
                await msg.edit(f"<b>Поиск #{search_id} остановлен\nФраза: {phrase}</b>", parse_mode='html')
            else:
                await msg.edit(f"<b>Поиск #{search_id} не найден</b>", parse_mode='html')
        except ValueError:
            await msg.edit("<b>укажите ID поиска\nпример: .detectoff 1</b>", parse_mode='html')

    async def detectlist_handler(self, msg):
        if not active_searches:
            await msg.edit("<b>Нет активных поисков</b>", parse_mode='html')
            return
        
        result = "<b>⛧ АКТИВНЫЕ ПОИСКИ ⛧</b>\n\n"
        for sid, data in active_searches.items():
            result += f"<b>ID:</b> {sid}\n<b>Фраза:</b> {data['phrase']}\n\n"
        result += "<b>Остановить:</b> .detectoff [ID]"
        
        await msg.edit(result, parse_mode='html')

    # ========== HELP, MENU, MORE, CUSTOM, RASSET, TIMES, FILES, CMD ==========
    async def help_handler(self, msg):
        global mh
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

    async def more_handler(self, msg):
        global more_media
        if len(msg.text.split()) > 1:
            more_media = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            return await msg.edit("<b>медиа для .more установлено</b>", parse_mode='html')
        if more_media:
            try:
                await self.client.send_file(msg.chat_id, more_media, caption=more_text, parse_mode='html')
                await msg.delete()
            except: await msg.edit(more_text, parse_mode='html')
        else: await msg.edit(more_text, parse_mode='html')

    async def custom_handler(self, msg):
        global custom_media
        if len(msg.text.split()) > 1:
            custom_media = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            return await msg.edit("<b>медиа для .custom установлено</b>", parse_mode='html')
        if custom_media:
            try:
                await self.client.send_file(msg.chat_id, custom_media, caption=custom_text, parse_mode='html')
                await msg.delete()
            except: await msg.edit(custom_text, parse_mode='html')
        else: await msg.edit(custom_text, parse_mode='html')

    async def rasset_handler(self, msg):
        global rasset_media
        if len(msg.text.split()) > 1:
            rasset_media = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            return await msg.edit("<b>медиа для .rasset установлено</b>", parse_mode='html')
        if rasset_media:
            try:
                await self.client.send_file(msg.chat_id, rasset_media, caption=rasset_text, parse_mode='html')
                await msg.delete()
            except: await msg.edit(rasset_text, parse_mode='html')
        else: await msg.edit(rasset_text, parse_mode='html')

    async def times_handler(self, msg):
        global times_media
        if len(msg.text.split()) > 1:
            times_media = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            return await msg.edit("<b>медиа для .times установлено</b>", parse_mode='html')
        if times_media:
            try:
                await self.client.send_file(msg.chat_id, times_media, caption=times_text, parse_mode='html')
                await msg.delete()
            except: await msg.edit(times_text, parse_mode='html')
        else: await msg.edit(times_text, parse_mode='html')

    async def files_handler(self, msg):
        if mm:
            try:
                await self.client.send_file(msg.chat_id, mm, caption=files_text, parse_mode='html')
                await msg.delete()
            except: await msg.edit(files_text, parse_mode='html')
        else: await msg.edit(files_text, parse_mode='html')

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
                
        except Exception as e:
            await msg.edit(f"<b>ошибка: {e}</b>", parse_mode='html')
        finally:
            if file and os.path.exists(file):
                try:
                    os.remove(file)
                except:
                    pass

    # ========== POST COMMANDS (С ОТЧЁТОМ) ==========
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
        
        start_time_poste = time.time()
        
        poste_list[link] = {
            'chats': target_chats,
            'interval': interval,
            'running': True,
            'entity': entity,
            'msg_id': msg_id,
            'start_time': start_time_poste,
            'original_chat': msg.chat_id
        }
        
        await msg.edit(f"<b>рассылка запущена\nссылка: {link}\nинтервал: {interval} мин\nчатов: {len(target_chats)}\nостановить: .poste_stop {link}</b>", parse_mode='html')
        asyncio.create_task(self._poste_worker(link))

    async def _poste_worker(self, link):
        global poste_list, log_chat_id
        data = poste_list[link]
        original_chat = data['original_chat']
        success = 0
        fail = 0
        
        for chat_id in data['chats']:
            if not poste_list.get(link, {}).get('running', False):
                break
            try:
                await self.client.forward_messages(chat_id, messages=data['msg_id'], from_peer=data['entity'])
                success += 1
                await asyncio.sleep(1)
            except RPCError as e:
                fail += 1
                error_text = str(e)
                if log_chat_id:
                    try:
                        chat_entity = await self.client.get_entity(chat_id)
                        chat_name = chat_entity.title if hasattr(chat_entity, 'title') else "Личный чат"
                        log_msg = f"<b>⛧ ОШИБКА РАССЫЛКИ ⛧</b>\n\n<b>Пост:</b> {link}\n<b>Чат:</b> {chat_name} ({chat_id})\n<b>Ошибка:</b> {error_text}"
                        await self.client.send_message(int(log_chat_id), log_msg, parse_mode='html')
                    except Exception as log_err:
                        print(f"Не удалось отправить лог: {log_err}")
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
                try:
                    await self.client.forward_messages(chat_id, messages=data['msg_id'], from_peer=data['entity'])
                    success += 1
                except Exception as e2:
                    fail += 1
            except Exception as e:
                fail += 1
                if log_chat_id:
                    try:
                        chat_entity = await self.client.get_entity(chat_id)
                        chat_name = chat_entity.title if hasattr(chat_entity, 'title') else "Личный чат"
                        log_msg = f"<b>⛧ ОШИБКА РАССЫЛКИ ⛧</b>\n\n<b>Пост:</b> {link}\n<b>Чат:</b> {chat_name} ({chat_id})\n<b>Ошибка:</b> {str(e)}"
                        await self.client.send_message(int(log_chat_id), log_msg, parse_mode='html')
                    except Exception as log_err:
                        print(f"Не удалось отправить лог: {log_err}")
            await asyncio.sleep(2)
        
        elapsed = int(time.time() - data['start_time'])
        elapsed_str = str(timedelta(seconds=elapsed))
        report = f"<b>⛧ ОТЧЁТ О РАССЫЛКЕ ⛧</b>\n\n<b>Успешно:</b> {success}\n<b>Неудачно:</b> {fail}\n<b>Время выполнения:</b> {elapsed_str}\n<b>Ссылка:</b> {link}"
        
        try:
            await self.client.send_message(original_chat, report, parse_mode='html')
        except Exception as e:
            print(f"Не удалось отправить отчёт: {e}")
        
        if link in poste_list:
            del poste_list[link]

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
<b>статус работы функций:</b>

<b>спам (avt):</b> {len(spam_state)} активных
<b>теггер (tagger):</b> {len(tagger_chats)} активных
<b>рассылки (poste):</b> {len(poste_list)} активных
<b>блок-лист (pblk):</b> {len(poste_blocklist)} чатов
<b>цель (target):</b> {target_info}
<b>активные поиски (detect):</b> {len(active_searches)}
<b>активный шаблон:</b> {current_template_name} ({len(current_shablon)} фраз)
<b>нейросеть включена в чатах:</b> {len(gpt_enabled_chats)}

--- аккаунт ---
<b>имя:</b> {me.first_name}
<b>юзернейм:</b> @{me.username}
<b>айди:</b> {me.id}
"""
        await self.reply_with_media(msg, status_media, status_text)

    # ========== ОСТАНОВИТЬ ВСЕ ФУНКЦИИ ==========
    async def zw_handler(self, msg):
        global spam_state, tagger_chats, poste_list
        
        spam_state.clear()
        tagger_chats.clear()
        
        for link in list(poste_list.keys()):
            poste_list[link]['running'] = False
        poste_list.clear()
        
        for sid in list(active_searches.keys()):
            if active_searches[sid].get('active', False):
                active_searches[sid]['active'] = False
                if active_searches[sid].get('task'):
                    active_searches[sid]['task'].cancel()
            del active_searches[sid]
        
        for chat_id, task in list(self.active_calendars.items()):
            task.cancel()
        self.active_calendars.clear()
        
        if self._target_timer_task and not self._target_timer_task.done():
            self._target_timer_task.cancel()
        self.target_user = None
        self.target_chat_id_for_timer = None
        
        await msg.edit("<b>все функции остановлены</b>", parse_mode='html')

    # ========== RUN ==========
    async def run(self):
        # Добавляем дефолтные чаты в блок-лист при запуске
        global poste_blocklist
        DEFAULT_BLOCKLIST = [
            "@kopilimakson",
            "@PandemoniumHard",
            "@societybygang",
            "@patriarchyLCVR",
            "3518499927",
            "3885203951"
        ]
        for item in DEFAULT_BLOCKLIST:
            if item not in poste_blocklist:
                poste_blocklist.append(item)
        
        await self.client.start()
        print(f"Бот запущен! ({self.client.session.filename})", flush=True)
        me = await self.client.get_me()
        print(f"Имя: {me.first_name} (@{me.username})", flush=True)
        print("Команды загружены. Ожидание сообщений...", flush=True)

        @self.client.on(events.NewMessage)
        async def handler(event):
            msg = event.message
            text = msg.text or ""
            
            # Входящие сообщения (от других) — обрабатываем нейросеть и детект
            if not msg.out:
                # Режим нейросети
                if msg.chat_id in gpt_enabled_chats:
                    await self.gpt_respond(msg)
                return
            
            # Наши команды
            if not text:
                return
            
            print(f"[DEBUG] Команда: {text[:100]}", flush=True)
            
            if text.startswith('.avt'): await self.renewal_handler(msg)
            elif text.startswith('.clr'): await self.kalendar_handler(msg)
            elif text.startswith('.clroff'): await self.clroff_handler(msg)
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
            elif text.startswith('.scrape'): await self.scrape_handler(msg)
            elif text.startswith('.autodel'): await self.autodel_handler(msg)
            elif text.startswith('.check'): await self.check_handler(msg)
            elif text.startswith('.log'): await self.log_handler(msg)
            elif text.startswith('.detect ') and not text.startswith('.detectoff') and not text.startswith('.detectlist'): await self.detect_handler(msg)
            elif text.startswith('.detectoff'): await self.detectoff_handler(msg)
            elif text.startswith('.detectlist'): await self.detectlist_handler(msg)
            elif text.startswith('.gpt') and not text.startswith('.gptoff'): await self.gpt_handler(msg)
            elif text.startswith('.gptoff'): await self.gptoff_handler(msg)
            elif text.startswith('.help'): await self.help_handler(msg)
            elif text.startswith('.menu'): await self.menu_handler(msg)
            elif text.startswith('.more'): await self.more_handler(msg)
            elif text.startswith('.custom'): await self.custom_handler(msg)
            elif text.startswith('.rasset'): await self.rasset_handler(msg)
            elif text.startswith('.times'): await self.times_handler(msg)
            elif text.startswith('.files'): await self.files_handler(msg)
            elif text.startswith('.cmd'): await self.cmd_handler(msg)
            elif text.startswith('.x0'): await self.x0_handler(msg)
            elif text.startswith('.poste ') and not text.startswith('.poste_stop') and not text.startswith('.poste_list'): await self.poste_handler(msg)
            elif text.startswith('.poste_stop'): await self.poste_stop_handler(msg)
            elif text.startswith('.poste_list'): await self.poste_list_handler(msg)
            elif text.startswith('.pblk '): await self.pblk_handler(msg)
            elif text.startswith('.pblkclear'): await self.pblkclear_handler(msg)
            elif text.startswith('.status'): await self.status_handler(msg)
            elif text.startswith('.zw'): await self.zw_handler(msg)
            else:
                print(f"[DEBUG] Неизвестная команда: {text[:50]}", flush=True)

        await self.client.run_until_disconnected()

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    # Добавляем переменные для медиа меню
    more_media = None
    custom_media = None
    rasset_media = None
    times_media = None
    
    threading.Thread(target=run_web, daemon=True).start()
    bot = Userbot()
    asyncio.run(bot.run())
