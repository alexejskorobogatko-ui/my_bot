# -*- coding: utf-8 -*-
import os
import sys
import time
import asyncio
import threading
import glob
import re
import json
import subprocess
from random import choice
from datetime import datetime, timedelta

import requests

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

# ==================== ДАННЫЕ ДЛЯ АККАУНТОВ ====================
ACCOUNTS = [
    {
        'session': 'session1',
        'api_id': 30843796,
        'api_hash': '535bed75aaa17ed391bc11e1dac2cb21'
    },
    {
        'session': 'session2',
        'api_id': 30843796,
        'api_hash': '535bed75aaa17ed391bc11e1dac2cb21'
    }
]

# ==================== ПУТИ ДЛЯ ФАЙЛОВ ====================
TEMPLATES_DIR = "templates"
MEDIA_DIR = "media"
DATA_DIR = "data"
LOG_CHAT_FILE = "log_chat.txt"

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

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

# ========== ОБЩИЕ ДЛЯ ВСЕХ АККАУНТОВ ==========
start_time = time.time()
mid = 'https://x0.at/cUQa.jpg'
name = "Ralvatron"
mh = 'https://x0.at/5-ku.mp4'
mm = 'https://x0.at/5-ku.mp4'
cmds = 'https://x0.at/Dv0D.jpg'
status_media = None
log_chat_id = None
ping_history = []
more_media = None
custom_media = None
postecom_media = None

# ========== ЛОГ-ЧАТ ==========
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

# ========== ТЕКУЩИЙ ШАБЛОН (ОБЩИЙ) ==========
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

# ==================== ТЕКСТЫ МЕНЮ ====================
menutext = """
⛧ Основное меню ⛧

<b><code>.id</code></b> — <b>узнать ID</b>
<b><code>.ping</code></b> — <b>пинг + аптайм</b>
<b><code>.status</code></b> — <b>статус функций</b>
<b><code>.zw</code></b> — <b>остановить всё</b>
<b><code>.reload</code></b> — <b>перезапустить бота</b>
<b><code>.menu</code></b> — <b>спам и теггер</b>
<b><code>.more</code></b> — <b>дополнительные функции</b>
<b><code>.postecom</code></b> — <b>рассылка постов</b>

⛧ developer - @axilessbog
"""

menu = """
⛧ Спам команды ⛧

<b><code>.avt [время] [медиа] [текст] + реплай</code></b> — <b>спам в чат</b>
<b><code>.stop [chat_id]</code></b> — <b>остановить спам</b>
<b><code>.tagger [id] [время] [медиа] [текст] + реплай</code></b> — <b>теггер</b>
<b><code>.off [chat_id]</code></b> — <b>остановить теггер</b>
<b><code>.clr [время] [медиа] [текст] + реплай</code></b> — <b>календарь</b>
<b><code>.clroff</code></b> — <b>остановить календарь</b>
<b><code>.reply @username</code></b> — <b>включить автоответчик</b>
<b><code>.reply + реплай</code></b> — <b>включить по реплаю</b>
<b><code>.creply @username</code></b> — <b>выключить автоответчик</b>
<b><code>.creply + реплай</code></b> — <b>выключить по реплаю</b>
<b><code>.reply_list</code></b> — <b>список активных</b>
<b><code>.reply_time [id] [сек]</code></b> — <b>изменить задержку</b>
<b><code>.reply_media [id] [ссылка/none]</code></b> — <b>изменить медиа</b>

⛧ developer - @axilessbog
"""

more_text = """
⛧ Дополнительные функции ⛧

<b>⛧ Шаблоны</b>
<b><code>.shb list</code></b> — <b>список шаблонов</b>
<b><code>.shb load [название]</code></b> — <b>загрузить шаблон</b>
<b><code>.shb save + реплай на TXT</code></b> — <b>сохранить шаблон</b>
<b><code>.shb del [название]</code></b> — <b>удалить шаблон</b>
<b><code>.load + реплай на файл</code></b> — <b>загрузить шаблон из файла</b>
<b><code>.file</code></b> — <b>выгрузить текущий шаблон</b>

<b>⛧ Медиа</b>
<b><code>.med save [номер] + реплай</code></b> — <b>сохранить медиа</b>
<b><code>.med list</code></b> — <b>список медиа</b>
<b><code>.med send [номер]</code></b> — <b>отправить медиа</b>
<b><code>.med del [номер]</code></b> — <b>удалить медиа</b>

<b>⛧ Слежение</b>
<b><code>.track @username</code></b> — <b>включить слежение (1 час)</b>
<b><code>.trackoff @username</code></b> — <b>выключить слежение</b>
<b><code>.tracklist</code></b> — <b>список активных слежений</b>

<b>⛧ Поиск по чатам</b>
<b><code>.detect [текст]</code></b> — <b>поиск фразы</b>
<b><code>.detectoff [номер]</code></b> — <b>остановить поиск</b>
<b><code>.detectlist</code></b> — <b>список активных поисков</b>

<b>⛧ Инструменты</b>
<b><code>.log [ссылка/username/id]</code></b> — <b>установить лог-чат</b>
<b><code>.scrape @username</code></b> — <b>выгрузить список участников</b>
<b><code>.x0 + реплай</code></b> — <b>загрузить медиа на хостинг</b>
<b><code>.autodel [сек]</code></b> — <b>автоудаление сообщений бота</b>
<b><code>.check + реплай</code></b> — <b>проверка транслитерации</b>
<b><code>.words + реплай</code></b> — <b>подсчёт слов/символов</b>

⛧ developer - @axilessbog
"""

postecom_text = """
⛧ Рассылка постов ⛧

<b><code>.poste [ссылка] [минуты]</code></b> — <b>запустить рассылку</b>
<b><code>.poste_stop</code></b> — <b>остановить все</b>
<b><code>.poste_stop [ссылка]</code></b> — <b>остановить по ссылке</b>
<b><code>.poste_list</code></b> — <b>список активных рассылок</b>
<b><code>.pblk list/add/del/clear</code></b> — <b>блок-лист</b>
<b><code>.pblkclear</code></b> — <b>очистить блок-лист</b>

⛧ developer - @axilessbog
"""

custom_text = """
⛧ Настройки кастомизации ⛧

<b><code>.help [ссылка]</code></b> — <b>медиа для .help</b>
<b><code>.menu [ссылка]</code></b> — <b>медиа для .menu</b>
<b><code>.more [ссылка]</code></b> — <b>медиа для .more</b>
<b><code>.postecom [ссылка]</code></b> — <b>медиа для .postecom</b>
<b><code>.id [ссылка]</code></b> — <b>медиа для .id</b>
<b><code>.status [ссылка]</code></b> — <b>медиа для .status</b>

⛧ developer - @axilessbog
"""

files_text = """
⛧ TXT шаблоны ⛧

<b><code>.load + реплай на файл</code></b> — <b>загрузить шаблон</b>
<b><code>.file</code></b> — <b>выгрузить текущий шаблон</b>

⛧ developer - @axilessbog
"""

# ==================== КЛАСС ЮЗЕРБОТА ====================
class Userbot:
    def __init__(self, account_index):
        self.account_index = account_index
        self.config = ACCOUNTS[account_index]
        self.client = TelegramClient(
            self.config['session'],
            self.config['api_id'],
            self.config['api_hash']
        )
        
        # ===== ПЕРЕМЕННЫЕ =====
        self.spam_state = {}
        self.tagger_chats = {}
        self.autodel_tasks = {}
        self.target_user = None
        self._target_timer_task = None
        self.target_chat_id_for_timer = None
        self.active_calendars = {}
        
        self.autoreply_list = []
        self.autoreply_time = {}
        self.autoreply_photo = {}
        self.autoreply_spam_tracker = {}
        
        self.active_searches = {}
        self.track_list = {}
        
        self.poste_list = {}
        self.poste_blocklist = []
        
        # ===== ФАЙЛЫ ДЛЯ СОХРАНЕНИЯ =====
        acc = account_index + 1
        self.blocklist_file = os.path.join(DATA_DIR, f"poste_blocklist_{acc}.json")
        self.poste_file = os.path.join(DATA_DIR, f"poste_list_{acc}.json")
        self.track_file = os.path.join(DATA_DIR, f"track_list_{acc}.json")
        self.autoreply_file = os.path.join(DATA_DIR, f"autoreply_{acc}.json")
        self.autoreply_time_file = os.path.join(DATA_DIR, f"autoreply_time_{acc}.json")
        self.autoreply_photo_file = os.path.join(DATA_DIR, f"autoreply_photo_{acc}.json")
        self.autoreply_tracker_file = os.path.join(DATA_DIR, f"autoreply_tracker_{acc}.json")
        self.spam_file = os.path.join(DATA_DIR, f"spam_state_{acc}.json")
        self.tagger_file = os.path.join(DATA_DIR, f"tagger_chats_{acc}.json")
        
        # ===== ЗАГРУЗКА СОСТОЯНИЙ =====
        self.poste_blocklist = self.load_json(self.blocklist_file, [])
        self.poste_list = self.load_json(self.poste_file, {})
        self.track_list = self.load_json(self.track_file, {})
        self.autoreply_list = self.load_json(self.autoreply_file, [])
        self.autoreply_time = self.load_json(self.autoreply_time_file, {})
        self.autoreply_photo = self.load_json(self.autoreply_photo_file, {})
        self.autoreply_spam_tracker = self.load_json(self.autoreply_tracker_file, {})
        self.spam_state = self.load_json(self.spam_file, {})
        self.tagger_chats = self.load_json(self.tagger_file, {})

    def load_json(self, path, default):
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default
        return default

    def save_json(self, path, data):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def save_all_state(self):
        """Сохраняет все состояния"""
        self.save_json(self.blocklist_file, self.poste_blocklist)
        self.save_json(self.poste_file, self.poste_list)
        self.save_json(self.track_file, self.track_list)
        self.save_json(self.autoreply_file, self.autoreply_list)
        self.save_json(self.autoreply_time_file, self.autoreply_time)
        self.save_json(self.autoreply_photo_file, self.autoreply_photo)
        self.save_json(self.autoreply_tracker_file, self.autoreply_spam_tracker)
        self.save_json(self.spam_file, self.spam_state)
        self.save_json(self.tagger_file, self.tagger_chats)

    def save_track_list(self):
        self.save_json(self.track_file, self.track_list)

    # ========== ВОССТАНОВЛЕНИЕ АКТИВНЫХ ЗАДАЧ ==========
    async def restore_spam(self, chat_id):
        """Восстанавливает спам-цикл после перезапуска"""
        if not self.spam_state.get(chat_id):
            return
        
        while self.spam_state.get(chat_id):
            try:
                random_phrase = choice(current_shablon) if current_shablon else ""
                await self.client.send_message(chat_id, random_phrase)
            except Exception as e:
                print(f"[Аккаунт {self.account_index+1}] Ошибка восстановления спама в {chat_id}: {e}")
                break
            await asyncio.sleep(5)

    async def restore_tagger(self, chat_id):
        """Восстанавливает теггер-цикл после перезапуска"""
        if not self.tagger_chats.get(chat_id):
            return
        
        while self.tagger_chats.get(chat_id):
            try:
                random_phrase = choice(current_shablon) if current_shablon else ""
                await self.client.send_message(chat_id, random_phrase)
            except Exception as e:
                print(f"[Аккаунт {self.account_index+1}] Ошибка восстановления теггера в {chat_id}: {e}")
                break
            await asyncio.sleep(5)

    # ========== КОМАНДА .reload ==========
    async def reload_handler(self, msg):
        """Перезапускает бота с сохранением состояния"""
        await msg.edit("<b>⛧ ПЕРЕЗАПУСК ⛧</b>\n\nСохраняю состояние...", parse_mode='html')
        
        self.save_all_state()
        
        await msg.edit("<b>⛧ ПЕРЕЗАПУСК ⛧</b>\n\nПодтягиваю изменения с GitHub...", parse_mode='html')
        
        try:
            result = subprocess.run(["git", "pull"], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
            
            if "Already up to date" in result.stdout:
                await msg.edit("<b>⛧ ПЕРЕЗАПУСК ⛧</b>\n\nКод актуален.\n\nПерезапускаюсь...", parse_mode='html')
            else:
                await msg.edit(
                    f"<b>⛧ ОБНОВЛЕНИЕ ЗАГРУЖЕНО ⛧</b>\n\n"
                    f"<code>{result.stdout[:300]}</code>\n\n"
                    f"Перезапускаюсь...",
                    parse_mode='html'
                )
        except Exception as e:
            await msg.edit(f"<b>⛧ ОШИБКА GIT ⛧</b>\n\n{e}", parse_mode='html')
            return
        
        await asyncio.sleep(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)

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
        chat_ref = chat_ref.strip()
        
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
                print(f"[Аккаунт {self.account_index+1}] Ошибка вступления по ссылке: {e}")
        
        if chat_ref.lstrip('-').isdigit():
            try:
                entity = await self.client.get_entity(int(chat_ref))
                return entity.id
            except:
                pass
        
        if chat_ref.startswith('@'):
            try:
                entity = await self.client.get_entity(chat_ref)
                return entity.id
            except:
                pass
        
        try:
            entity = await self.client.get_entity(chat_ref)
            return entity.id
        except:
            pass
        
        return None

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

    async def get_media_to_send(self, media_id, media_url):
        if media_id:
            return get_media_path(media_id)
        elif media_url:
            try:
                response = requests.get(media_url, timeout=30)
                if response.status_code == 200:
                    temp_file = f"temp_media_{int(time.time())}"
                    ext = media_url.split('.')[-1].split('?')[0]
                    if len(ext) > 5:
                        ext = 'bin'
                    temp_path = os.path.join(MEDIA_DIR, f"{temp_file}.{ext}")
                    with open(temp_path, 'wb') as f:
                        f.write(response.content)
                    return temp_path
            except Exception as e:
                print(f"[Аккаунт {self.account_index+1}] Ошибка скачивания по ссылке: {e}")
        return None

    # ========== АВТООТВЕТЧИК ==========
    async def watcher(self, msg):
        if not msg.out:
            user_id = msg.sender_id
            
            if user_id in self.autoreply_list:
                current_time = time.time()
                
                if user_id not in self.autoreply_spam_tracker:
                    self.autoreply_spam_tracker[user_id] = {
                        'count': 0,
                        'last_time': current_time,
                        'last_reply_time': 0
                    }
                
                tracker = self.autoreply_spam_tracker[user_id]
                
                if current_time - tracker['last_time'] < 2:
                    tracker['count'] += 1
                else:
                    tracker['count'] = 1
                tracker['last_time'] = current_time
                
                should_reply = False
                if tracker['count'] > 3:
                    if current_time - tracker['last_reply_time'] >= 3:
                        should_reply = True
                else:
                    last_reply = self.autoreply_spam_tracker.get(user_id, {}).get('last_reply_time', 0)
                    delay = self.autoreply_time.get(user_id, 1)
                    if current_time - last_reply >= delay:
                        should_reply = True
                
                if should_reply:
                    tracker['last_reply_time'] = current_time
                    await asyncio.sleep(self.autoreply_time.get(user_id, 1))
                    text = choice(current_shablon) if current_shablon else ""
                    await msg.reply(text, file=self.autoreply_photo.get(user_id), parse_mode='html')

    # ========== АВТООТВЕТЧИК КОМАНДЫ ==========
    async def autoreply_handler(self, msg):
        args = msg.text.split()
        if len(args) < 1:
            return
        
        cmd = args[0].lower()
        
        if cmd == '.reply':
            if msg.is_reply:
                user_id = (await msg.get_reply_message()).sender_id
                if user_id not in self.autoreply_list:
                    self.autoreply_list.append(user_id)
                self.autoreply_time[user_id] = 1
                self.autoreply_photo[user_id] = None
                await msg.edit(f'<b>⛧ АВТООТВЕТЧИК ВКЛЮЧЕН ⛧</b>\n\n<b>Жертва:</b> <code>{user_id}</code>\n<b>Задержка:</b> 1 сек\n\n<b>Остановить:</b> .creply {user_id}', parse_mode='html')
                self.save_json(self.autoreply_file, self.autoreply_list)
                self.save_json(self.autoreply_time_file, self.autoreply_time)
            elif len(args) >= 2:
                target = args[1]
                try:
                    if target.lstrip('-').isdigit():
                        entity = await self.client.get_entity(int(target))
                    else:
                        if not target.startswith('@'):
                            target = '@' + target
                        entity = await self.client.get_entity(target)
                    user_id = entity.id
                    if user_id not in self.autoreply_list:
                        self.autoreply_list.append(user_id)
                    self.autoreply_time[user_id] = 1
                    self.autoreply_photo[user_id] = None
                    name = entity.first_name or entity.username or str(user_id)
                    await msg.edit(f'<b>⛧ АВТООТВЕТЧИК ВКЛЮЧЕН ⛧</b>\n\n<b>Жертва:</b> {name} (<code>{user_id}</code>)\n<b>Задержка:</b> 1 сек\n\n<b>Остановить:</b> .creply {user_id}', parse_mode='html')
                    self.save_json(self.autoreply_file, self.autoreply_list)
                    self.save_json(self.autoreply_time_file, self.autoreply_time)
                except Exception as e:
                    await msg.edit(f'<b>⛧ ОШИБКА ⛧</b>\n\nНе удалось найти пользователя: {e}', parse_mode='html')
            else:
                await msg.edit('<b>⛧ ИСПОЛЬЗОВАНИЕ ⛧</b>\n\n.reply @username\n.reply + реплай на сообщение', parse_mode='html')
        
        elif cmd == '.creply':
            if msg.is_reply:
                user_id = (await msg.get_reply_message()).sender_id
            elif len(args) >= 2:
                target = args[1]
                try:
                    if target.lstrip('-').isdigit():
                        entity = await self.client.get_entity(int(target))
                    else:
                        if not target.startswith('@'):
                            target = '@' + target
                        entity = await self.client.get_entity(target)
                    user_id = entity.id
                except:
                    user_id = int(target) if target.lstrip('-').isdigit() else None
            else:
                user_id = None
            
            if user_id and user_id in self.autoreply_list:
                self.autoreply_list.remove(user_id)
                self.autoreply_time.pop(user_id, None)
                self.autoreply_photo.pop(user_id, None)
                if user_id in self.autoreply_spam_tracker:
                    del self.autoreply_spam_tracker[user_id]
                await msg.edit(f'<b>⛧ АВТООТВЕТЧИК ВЫКЛЮЧЕН ⛧</b>\n\n<b>Жертва:</b> <code>{user_id}</code>', parse_mode='html')
                self.save_json(self.autoreply_file, self.autoreply_list)
                self.save_json(self.autoreply_time_file, self.autoreply_time)
                self.save_json(self.autoreply_photo_file, self.autoreply_photo)
                self.save_json(self.autoreply_tracker_file, self.autoreply_spam_tracker)
            else:
                await msg.edit('<b>⛧ ОШИБКА ⛧</b>\n\nАвтоответчик на этого пользователя не найден', parse_mode='html')
        
        elif cmd == '.reply_list':
            if not self.autoreply_list:
                await msg.edit('<b>⛧ НЕТ АКТИВНЫХ АВТООТВЕТЧИКОВ ⛧</b>', parse_mode='html')
                return
            
            result = "<b>⛧ АКТИВНЫЕ АВТООТВЕТЧИКИ ⛧</b>\n\n"
            for uid in self.autoreply_list:
                try:
                    entity = await self.client.get_entity(uid)
                    name = entity.first_name or entity.username or str(uid)
                    result += f"<b>Жертва:</b> {name} (<code>{uid}</code>)\n"
                    result += f"<b>Задержка:</b> {self.autoreply_time.get(uid, 1)} сек\n\n"
                except:
                    result += f"<b>Жертва:</b> <code>{uid}</code>\n"
                    result += f"<b>Задержка:</b> {self.autoreply_time.get(uid, 1)} сек\n\n"
            await msg.edit(result, parse_mode='html')
        
        elif cmd == '.reply_time' and len(args) >= 3:
            try:
                user_id = int(args[1])
                delay = int(args[2])
                if user_id in self.autoreply_list:
                    self.autoreply_time[user_id] = delay
                    await msg.edit(f'<b>⛧ ЗАДЕРЖКА ИЗМЕНЕНА ⛧</b>\n\n<b>Жертва:</b> <code>{user_id}</code>\n<b>Новая задержка:</b> {delay} сек', parse_mode='html')
                    self.save_json(self.autoreply_time_file, self.autoreply_time)
                else:
                    await msg.edit(f'<b>⛧ ОШИБКА ⛧</b>\n\nАвтоответчик на <code>{user_id}</code> не активен', parse_mode='html')
            except:
                await msg.edit('<b>⛧ ИСПОЛЬЗОВАНИЕ ⛧</b>\n\n.reply_time [id] [секунды]', parse_mode='html')
        
        elif cmd == '.reply_media' and len(args) >= 3:
            try:
                user_id = int(args[1])
                media = args[2] if 'http' in args[2] else None
                if user_id in self.autoreply_list and media:
                    self.autoreply_photo[user_id] = media
                    await msg.edit(f'<b>⛧ МЕДИА ИЗМЕНЕНО ⛧</b>\n\n<b>Жертва:</b> <code>{user_id}</code>', parse_mode='html')
                    self.save_json(self.autoreply_photo_file, self.autoreply_photo)
                else:
                    await msg.edit(f'<b>⛧ ОШИБКА ⛧</b>\n\nАвтоответчик не активен или ссылка невалидна', parse_mode='html')
            except:
                await msg.edit('<b>⛧ ИСПОЛЬЗОВАНИЕ ⛧</b>\n\n.reply_media [id] [ссылка]', parse_mode='html')

    # ========== СПАМ ==========
    async def renewal_handler(self, msg):
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
        
        self.spam_state[chat_id] = True
        await msg.edit(f'<b>⛧ СПАМ ВКЛЮЧЕН ⛧</b>\n\n<b>Чат:</b> <code>{chat_id}</code>\n\n<b>Выключить:</b> <code>.stop {chat_id}</code>', parse_mode='html')
        
        self.save_json(self.spam_file, self.spam_state)
        
        while chat_id in self.spam_state and self.spam_state[chat_id]:
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
                print(f"[Аккаунт {self.account_index+1}] Спам ошибка: {e}")
            await asyncio.sleep(time_val)
        
        if chat_id in self.spam_state:
            del self.spam_state[chat_id]
            self.save_json(self.spam_file, self.spam_state)
        
        if media_url and media_path and os.path.exists(media_path):
            try:
                os.remove(media_path)
            except:
                pass

    async def stop_handler(self, msg):
        args = await self.get_args(msg)
        chat_id = int(args.split()[0]) if args else msg.chat_id
        if chat_id in self.spam_state:
            del self.spam_state[chat_id]
            await msg.edit(f"<b>⛧ СПАМ ОСТАНОВЛЕН ⛧</b>\n\n<b>Чат:</b> <code>{chat_id}</code>", parse_mode='html')
            self.save_json(self.spam_file, self.spam_state)
        else:
            await msg.edit(f"<b>⛧ СПАМ НЕ БЫЛ АКТИВЕН ⛧</b>\n\n<b>Чат:</b> <code>{chat_id}</code>", parse_mode='html')

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
        
        self.tagger_chats[chat_id] = True
        await msg.edit(f'<b>⛧ ТЕГГЕР ВКЛЮЧЕН ⛧</b>\n\n<b>Чат:</b> <code>{chat_id}</code>\n<b>Жертва:</b> <code>{user_id}</code>\n\n<b>Выключить:</b> <code>.off {chat_id}</code>', parse_mode='html')
        
        self.save_json(self.tagger_file, self.tagger_chats)
        
        while chat_id in self.tagger_chats:
            random_phrase = choice(current_shablon) if current_shablon else ""
            if custom_text:
                base_text = f"{custom_text} {random_phrase}".strip()
            else:
                base_text = random_phrase
            
            text = f"<a href='tg://user?id={user_id}'>{base_text}</a>"
            
            try:
                if media_path:
                    await self.client.send_file(chat_id, media_path, caption=text, parse_mode='html')
                else:
                    await self.client.send_message(chat_id, text, parse_mode='html')
            except Exception as e:
                print(f"[Аккаунт {self.account_index+1}] Теггер ошибка: {e}")
            await asyncio.sleep(time_val)
        
        if chat_id in self.tagger_chats:
            del self.tagger_chats[chat_id]
            self.save_json(self.tagger_file, self.tagger_chats)
        
        if media_url and media_path and os.path.exists(media_path):
            try:
                os.remove(media_path)
            except:
                pass

    async def off_handler(self, msg):
        args = await self.get_args(msg)
        chat_id = int(args.split()[0]) if args else msg.chat_id
        if chat_id in self.tagger_chats:
            del self.tagger_chats[chat_id]
            await msg.edit(f"<b>⛧ ТЕГГЕР ОСТАНОВЛЕН ⛧</b>\n\n<b>Чат:</b> <code>{chat_id}</code>", parse_mode='html')
            self.save_json(self.tagger_file, self.tagger_chats)
        else:
            await msg.edit(f"<b>⛧ ТЕГГЕР НЕ БЫЛ АКТИВЕН ⛧</b>\n\n<b>Чат:</b> <code>{chat_id}</code>", parse_mode='html')

    # ========== СТАТУС ==========
    async def status_handler(self, msg):
        global status_media
        if len(msg.text.split()) > 1:
            status_media = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            return await msg.edit("<b>медиа для .status установлено</b>", parse_mode='html')
        
        me = await self.client.get_me()
        target_info = self.target_user if self.target_user else "не установлена"
        
        spam_text = f"{len(self.spam_state)} активных"
        if self.spam_state:
            spam_text += "\n"
            for chat_id in self.spam_state:
                try:
                    chat_entity = await self.client.get_entity(chat_id)
                    chat_name = await self.get_entity_name(chat_entity)
                    spam_text += f"\n  • {chat_name} (<code>{chat_id}</code>)"
                except:
                    spam_text += f"\n  • <code>{chat_id}</code>"
        else:
            spam_text += "\n  • нет"
        
        tagger_text = f"{len(self.tagger_chats)} активных"
        if self.tagger_chats:
            tagger_text += "\n"
            for chat_id in self.tagger_chats:
                try:
                    chat_entity = await self.client.get_entity(chat_id)
                    chat_name = await self.get_entity_name(chat_entity)
                    tagger_text += f"\n  • {chat_name} (<code>{chat_id}</code>)"
                except:
                    tagger_text += f"\n  • <code>{chat_id}</code>"
        else:
            tagger_text += "\n  • нет"
        
        aa_text = f"{len(self.autoreply_list)} активных"
        if self.autoreply_list:
            aa_text += "\n"
            for uid in self.autoreply_list:
                try:
                    entity = await self.client.get_entity(uid)
                    name = entity.first_name or entity.username or str(uid)
                    aa_text += f"\n  • {name} (<code>{uid}</code>)"
                    aa_text += f"\n    ⏱ задержка: {self.autoreply_time.get(uid, 1)} сек"
                except:
                    aa_text += f"\n  • <code>{uid}</code>"
        else:
            aa_text += "\n  • нет"
        
        poste_text = f"{len(self.poste_list)} активных" if self.poste_list else "нет"
        blocklist_text = f"{len(self.poste_blocklist)} чатов" if self.poste_blocklist else "нет"
        detect_text = f"{len(self.active_searches)} активных" if self.active_searches else "нет"
        
        track_text = ""
        if self.track_list:
            total = sum(len(users) for users in self.track_list.values())
            track_text = f"{total} активных"
            for chat_id, users in self.track_list.items():
                try:
                    chat_entity = await self.client.get_entity(chat_id)
                    chat_name = await self.get_entity_name(chat_entity)
                    track_text += f"\n  • Чат: {chat_name} (<code>{chat_id}</code>)"
                except:
                    track_text += f"\n  • Чат: <code>{chat_id}</code>"
                for user_id, data in users.items():
                    user_name = data.get('name', str(user_id))
                    username = data.get('username', '')
                    track_text += f"\n    ⤷ {user_name} {username} (<code>{user_id}</code>)"
        else:
            track_text = "нет"
        
        template_text = f"{current_template_name} ({len(current_shablon)} фраз)" if current_shablon else "не загружен"
        
        status_text = f"""
<b>⛧ СТАТУС РАБОТЫ ФУНКЦИЙ (АККАУНТ {self.account_index+1}) ⛧</b>

<b>⛧ СПАМ (avt):</b> {spam_text}

<b>⛧ ТЕГГЕР (tagger):</b> {tagger_text}

<b>⛧ АВТООТВЕТЧИК (reply):</b> {aa_text}

<b>⛧ РАССЫЛКИ (poste):</b> {poste_text}

<b>⛧ БЛОК-ЛИСТ (pblk):</b> {blocklist_text}

<b>⛧ ЦЕЛЬ (target):</b> {target_info}

<b>⛧ АКТИВНЫЕ ПОИСКИ (detect):</b> {detect_text}

<b>⛧ АКТИВНЫЕ СЛЕЖЕНИЯ (track):</b> {track_text}

<b>⛧ АКТИВНЫЙ ШАБЛОН:</b> {template_text}

<b>⛧ АККАУНТ ⛧</b>
<b>Имя:</b> {me.first_name}
<b>Юзернейм:</b> @{me.username if me.username else "нет"}
<b>Айди:</b> <code>{me.id}</code>
"""
        await self.reply_with_media(msg, status_media, status_text)

    # ========== ОСТАЛЬНЫЕ КОМАНДЫ ==========
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
            start_time_local = time.time()
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
                    print(f"[Аккаунт {self.account_index+1}] Календарь ошибка: {e}")
                await asyncio.sleep(0.5)
            
            elapsed = int(time.time() - start_time_local)
            elapsed_str = str(timedelta(seconds=elapsed))
            report = f"<b>⛧ КАЛЕНДАРЬ ЗАВЕРШЁН ⛧</b>\n\n<b>Всего сообщений:</b> {messages_sent}\n<b>Время работы:</b> {elapsed_str}\n<b>Интервал:</b> {time_val} мин"
            await msg.respond(report, parse_mode='html')
            
            if chat_id in self.active_calendars:
                del self.active_calendars[chat_id]
            
            if media_url and media_path and os.path.exists(media_path):
                try:
                    os.remove(media_path)
                except:
                    pass
        
        task = asyncio.create_task(calendar_task())
        self.active_calendars[chat_id] = task
        await msg.edit(f"<b>⛧ КАЛЕНДАРЬ ЗАПУЩЕН ⛧</b>\n\n<b>Интервал:</b> {time_val} мин\n<b>Остановить:</b> .clroff", parse_mode='html')

    async def clroff_handler(self, msg):
        chat_id = msg.chat_id
        if chat_id in self.active_calendars:
            self.active_calendars[chat_id].cancel()
            del self.active_calendars[chat_id]
            await msg.edit("<b>⛧ КАЛЕНДАРЬ ОСТАНОВЛЕН ⛧</b>", parse_mode='html')
        else:
            await msg.edit("<b>⛧ АКТИВНЫЙ КАЛЕНДАРЬ НЕ НАЙДЕН ⛧</b>", parse_mode='html')

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

    async def file_handler(self, msg):
        with open('texts.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(current_shablon))
        await self.client.send_file(msg.chat_id, 'texts.txt')
        os.remove('texts.txt')
        await msg.delete()

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
                    f"<b>⛧ ВРЕМЯ ВЫШЛО ⛧</b>\n\n<b>Цель:</b> {target_display} отключена",
                    parse_mode='html'
                )
                self.target_user = None
                self.target_chat_id_for_timer = None
        
        self._target_timer_task = asyncio.create_task(disable_target())
        await msg.edit(f"<b>⛧ ЦЕЛЬ УСТАНОВЛЕНА ⛧</b>\n\n<b>Цель:</b> {target_input}\n<b>Автоотключение через:</b> {minutes} минут", parse_mode='html')

    async def tgoff_handler(self, msg):
        if self._target_timer_task and not self._target_timer_task.done():
            self._target_timer_task.cancel()
        self.target_user = None
        self.target_chat_id_for_timer = None
        await msg.edit("<b>⛧ ЦЕЛЬ ОТКЛЮЧЕНА ⛧</b>", parse_mode='html')

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
                active = " ⛧ активен" if name == current_template_name else ""
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
            
            count = len(users)
            if count % 10 == 1 and count % 100 != 11:
                people_word = "человек"
            elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
                people_word = "человека"
            else:
                people_word = "человек"
            
            chat_name = entity.title if hasattr(entity, 'title') else args
            await self.client.send_file(msg.chat_id, filename, caption=f"<b>Список участников {chat_name}: {count} {people_word}</b>", parse_mode='html')
            os.remove(filename)
            await msg.delete()
            
        except Exception as e:
            await msg.edit(f"<b>Ошибка: {e}</b>", parse_mode='html')

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
        if chat_id in self.autodel_tasks:
            self.autodel_tasks[chat_id].cancel()
        
        async def auto_delete():
            await asyncio.sleep(delay)
            try:
                async for message in self.client.iter_messages(chat_id, from_user='me'):
                    await message.delete()
                    await asyncio.sleep(0.5)
            except Exception as e:
                print(f"[Аккаунт {self.account_index+1}] Autodel ошибка: {e}")
            finally:
                if chat_id in self.autodel_tasks:
                    del self.autodel_tasks[chat_id]
        
        task = asyncio.create_task(auto_delete())
        self.autodel_tasks[chat_id] = task
        await msg.edit(f"<b>⛧ АВТОУДАЛЕНИЕ ВКЛЮЧЕНО ⛧</b>\n\n<b>Чат:</b> <code>{chat_id}</code>\n<b>Удаление через:</b> {delay} сек", parse_mode='html')

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

    async def track_handler(self, msg):
        target_user = None
        user_id = None
        user_name = None
        username = ""
        
        if msg.is_reply:
            reply_msg = await msg.get_reply_message()
            target_user = await reply_msg.get_sender()
            if not target_user:
                await msg.edit("<b>Не удалось определить пользователя по реплаю</b>", parse_mode='html')
                return
            user_id = target_user.id
            user_name = await self.get_entity_name(target_user)
            username = f"@{target_user.username}" if target_user.username else ""
        else:
            args = await self.get_args(msg)
            if not args:
                await msg.edit("<b>использование: .track @username или .track + реплай на сообщение</b>", parse_mode='html')
                return
            
            arg = args.strip()
            try:
                if arg.lstrip('-').isdigit():
                    target_user = await self.client.get_entity(int(arg))
                else:
                    if not arg.startswith('@'):
                        arg = '@' + arg
                    target_user = await self.client.get_entity(arg)
                
                user_id = target_user.id
                user_name = await self.get_entity_name(target_user)
                username = f"@{target_user.username}" if target_user.username else ""
            except Exception as e:
                await msg.edit(f"<b>Не удалось найти пользователя: {e}</b>", parse_mode='html')
                return
        
        chat_id = msg.chat_id
        chat_entity = await msg.get_chat()
        chat_name = await self.get_entity_name(chat_entity)
        
        if chat_id in self.track_list and user_id in self.track_list[chat_id]:
            old_task = self.track_list[chat_id][user_id].get('task')
            if old_task and not old_task.done():
                old_task.cancel()
        
        async def track_wait_and_notify():
            await asyncio.sleep(3600)
            try:
                for i in range(3):
                    await self.client.send_message(
                        chat_id,
                        f"<b>⛧ Слежение ⛧</b>\n\n"
                        f"<b>Пользователь:</b> {user_name} {username}\n"
                        f"<b>Статус:</b> не писал 1 час\n\n"
                        f"<b>Слежение отключено</b>",
                        parse_mode='html'
                    )
                    if i < 2:
                        await asyncio.sleep(3)
            except Exception as e:
                print(f"[Аккаунт {self.account_index+1}] Ошибка отправки уведомления о слежении: {e}")
            
            if chat_id in self.track_list and user_id in self.track_list[chat_id]:
                del self.track_list[chat_id][user_id]
                if not self.track_list[chat_id]:
                    del self.track_list[chat_id]
                self.save_track_list()
        
        task = asyncio.create_task(track_wait_and_notify())
        
        if chat_id not in self.track_list:
            self.track_list[chat_id] = {}
        self.track_list[chat_id][user_id] = {
            'task': task,
            'name': user_name,
            'username': username,
            'chat_name': chat_name
        }
        self.save_track_list()
        
        await msg.edit(
            f"<b>⛧ Слежение установлено ⛧</b>\n\n"
            f"<b>Пользователь:</b> {user_name} {username}\n"
            f"<b>Чат:</b> {chat_name}\n"
            f"<b>Условие:</b> если не напишет 1 час — уведомлю в этом чате (3 раза)",
            parse_mode='html'
        )

    async def trackoff_handler(self, msg):
        target_id = None
        
        if msg.is_reply:
            reply_msg = await msg.get_reply_message()
            target_user = await reply_msg.get_sender()
            if target_user:
                target_id = target_user.id
        else:
            args = await self.get_args(msg)
            if args:
                arg = args.strip()
                try:
                    if arg.lstrip('-').isdigit():
                        entity = await self.client.get_entity(int(arg))
                    else:
                        if not arg.startswith('@'):
                            arg = '@' + arg
                        entity = await self.client.get_entity(arg)
                    target_id = entity.id
                except Exception as e:
                    await msg.edit(f"<b>Не удалось найти пользователя: {e}</b>", parse_mode='html')
                    return
        
        if not target_id:
            await msg.edit("<b>использование: .trackoff @username или .trackoff + реплай на сообщение</b>", parse_mode='html')
            return
        
        chat_id = msg.chat_id
        if chat_id in self.track_list and target_id in self.track_list[chat_id]:
            old_task = self.track_list[chat_id][target_id].get('task')
            if old_task and not old_task.done():
                old_task.cancel()
            user_name = self.track_list[chat_id][target_id].get('name', str(target_id))
            del self.track_list[chat_id][target_id]
            if not self.track_list[chat_id]:
                del self.track_list[chat_id]
            self.save_track_list()
            await msg.edit(f"<b>⛧ Слежение отключено для пользователя {user_name}</b>", parse_mode='html')
        else:
            await msg.edit("<b>⛧ Слежение на этого пользователя не найдено</b>", parse_mode='html')

    async def tracklist_handler(self, msg):
        if not self.track_list:
            await msg.edit("<b>⛧ Нет активных слежений</b>", parse_mode='html')
            return
        
        result = "<b>⛧ Активные слежения ⛧</b>\n\n"
        for chat_id, users in self.track_list.items():
            try:
                chat_entity = await self.client.get_entity(chat_id)
                chat_name = await self.get_entity_name(chat_entity)
            except:
                chat_name = str(chat_id)
            result += f"<b>Чат:</b> {chat_name}\n"
            for user_id, data in users.items():
                result += f"  • {data['name']} {data['username']} (ID: {user_id})\n"
            result += "\n"
        
        result += "<b>Остановить:</b> .trackoff @username или реплай"
        await msg.edit(result, parse_mode='html')

    async def detect_handler(self, msg):
        args = await self.get_args(msg)
        if not args:
            await msg.edit("<b>использование: .detect текст_для_поиска</b>", parse_mode='html')
            return
        
        phrase = args.strip()
        if len(phrase) < 3:
            await msg.edit("<b>фраза должна содержать минимум 3 символа</b>", parse_mode='html')
            return
        
        search_id = len(self.active_searches) + 1
        original_chat_id = msg.chat_id
        
        await msg.edit(f"<b>⛧ Поиск запущен ⛧</b>\n\n<b>Фраза:</b> {phrase}\n<b>Статус:</b> поиск...\n<b>ID поиска:</b> {search_id}\n\nРезультаты появятся здесь по мере нахождения.", parse_mode='html')
        
        results = []
        
        async def search_task():
            nonlocal results
            try:
                dialogs = await self.client.get_dialogs()
                for dialog in dialogs:
                    if not self.active_searches.get(search_id, {}).get('active', True):
                        break
                    
                    try:
                        async for message in self.client.iter_messages(dialog.id, limit=500, search=phrase):
                            if not self.active_searches.get(search_id, {}).get('active', True):
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
                        print(f"[Аккаунт {self.account_index+1}] Ошибка при поиске в чате {dialog.id}: {e}")
                    
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
                    print(f"[Аккаунт {self.account_index+1}] Ошибка отправки отчёта: {e}")
                
                if search_id in self.active_searches:
                    del self.active_searches[search_id]
                    
            except Exception as e:
                await msg.edit(f"<b>Ошибка при поиске: {e}</b>", parse_mode='html')
                if search_id in self.active_searches:
                    del self.active_searches[search_id]
        
        task = asyncio.create_task(search_task())
        self.active_searches[search_id] = {
            'task': task,
            'phrase': phrase,
            'chat_id': original_chat_id,
            'active': True
        }

    async def detectoff_handler(self, msg):
        args = await self.get_args(msg)
        
        if not args:
            count = 0
            for sid in list(self.active_searches.keys()):
                if self.active_searches[sid].get('active', False):
                    self.active_searches[sid]['active'] = False
                    if self.active_searches[sid].get('task'):
                        self.active_searches[sid]['task'].cancel()
                    del self.active_searches[sid]
                    count += 1
            if count > 0:
                await msg.edit(f"<b>Остановлено {count} активных поисков</b>", parse_mode='html')
            else:
                await msg.edit("<b>Нет активных поисков для остановки</b>", parse_mode='html')
            return
        
        try:
            search_id = int(args.strip())
            if search_id in self.active_searches:
                self.active_searches[search_id]['active'] = False
                if self.active_searches[search_id].get('task'):
                    self.active_searches[search_id]['task'].cancel()
                phrase = self.active_searches[search_id]['phrase']
                del self.active_searches[search_id]
                await msg.edit(f"<b>Поиск #{search_id} остановлен\nФраза: {phrase}</b>", parse_mode='html')
            else:
                await msg.edit(f"<b>Поиск #{search_id} не найден</b>", parse_mode='html')
        except ValueError:
            await msg.edit("<b>укажите ID поиска\nпример: .detectoff 1</b>", parse_mode='html')

    async def detectlist_handler(self, msg):
        if not self.active_searches:
            await msg.edit("<b>Нет активных поисков</b>", parse_mode='html')
            return
        
        result = "<b>⛧ АКТИВНЫЕ ПОИСКИ ⛧</b>\n\n"
        for sid, data in self.active_searches.items():
            result += f"<b>ID:</b> {sid}\n<b>Фраза:</b> {data['phrase']}\n\n"
        result += "<b>Остановить:</b> .detectoff [ID]"
        
        await msg.edit(result, parse_mode='html')

    # ========== МЕНЮ-ХЕНДЛЕРЫ ==========
    async def help_handler(self, msg):
        global mh
        if len(msg.text.split()) > 1:
            mh = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            return await msg.edit("<b>медиа для .help установлено</b>", parse_mode='html')
        caption = menutext
        if mh:
            try:
                await self.client.send_file(msg.chat_id, mh, caption=caption, parse_mode='html')
                await msg.delete()
            except:
                await msg.edit(caption, parse_mode='html')
        else:
            await msg.edit(caption, parse_mode='html')

    async def menu_handler(self, msg):
        global mm
        if len(msg.text.split()) > 1:
            mm = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            return await msg.edit("<b>медиа для .menu установлено</b>", parse_mode='html')
        if mm:
            try:
                await self.client.send_file(msg.chat_id, mm, caption=menu, parse_mode='html')
                await msg.delete()
            except:
                await msg.edit(menu, parse_mode='html')
        else:
            await msg.edit(menu, parse_mode='html')

    async def more_handler(self, msg):
        global more_media
        if len(msg.text.split()) > 1:
            more_media = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            return await msg.edit("<b>медиа для .more установлено</b>", parse_mode='html')
        if more_media:
            try:
                await self.client.send_file(msg.chat_id, more_media, caption=more_text, parse_mode='html')
                await msg.delete()
            except:
                await msg.edit(more_text, parse_mode='html')
        else:
            await msg.edit(more_text, parse_mode='html')

    async def postecom_handler(self, msg):
        global postecom_media
        if len(msg.text.split()) > 1:
            postecom_media = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            return await msg.edit("<b>медиа для .postecom установлено</b>", parse_mode='html')
        if postecom_media:
            try:
                await self.client.send_file(msg.chat_id, postecom_media, caption=postecom_text, parse_mode='html')
                await msg.delete()
            except:
                await msg.edit(postecom_text, parse_mode='html')
        else:
            await msg.edit(postecom_text, parse_mode='html')

    async def custom_handler(self, msg):
        global custom_media
        if len(msg.text.split()) > 1:
            custom_media = msg.text.split(maxsplit=1)[1] if msg.text.split(maxsplit=1)[1].lower() != "none" else None
            return await msg.edit("<b>медиа для .custom установлено</b>", parse_mode='html')
        if custom_media:
            try:
                await self.client.send_file(msg.chat_id, custom_media, caption=custom_text, parse_mode='html')
                await msg.delete()
            except:
                await msg.edit(custom_text, parse_mode='html')
        else:
            await msg.edit(custom_text, parse_mode='html')

    async def files_handler(self, msg):
        if mm:
            try:
                await self.client.send_file(msg.chat_id, mm, caption=files_text, parse_mode='html')
                await msg.delete()
            except:
                await msg.edit(files_text, parse_mode='html')
        else:
            await msg.edit(files_text, parse_mode='html')

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

    # ========== POST COMMANDS ==========
    async def poste_handler(self, msg):
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
        
        if link in self.poste_list:
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
            if d.entity.id in self.poste_blocklist:
                continue
            target_chats.append(d.entity.id)
        
        if not target_chats:
            return await msg.edit("<b>нет доступных чатов для рассылки</b>", parse_mode='html')
        
        start_time_poste = time.time()
        
        self.poste_list[link] = {
            'chats': target_chats,
            'interval': interval,
            'running': True,
            'entity': entity,
            'msg_id': msg_id,
            'start_time': start_time_poste,
            'original_chat': msg.chat_id
        }
        
        self.save_json(self.poste_file, self.poste_list)
        
        await msg.edit(f"<b>рассылка запущена\nссылка: {link}\nинтервал: {interval} мин\nчатов: {len(target_chats)}\nостановить: .poste_stop {link}</b>", parse_mode='html')
        asyncio.create_task(self._poste_worker(link))

    async def _poste_worker(self, link):
        global log_chat_id
        
        while self.poste_list.get(link, {}).get('running', False):
            data = self.poste_list[link]
            original_chat = data['original_chat']
            interval_minutes = data['interval']
            success = 0
            fail = 0
            
            for chat_id in data['chats']:
                if not self.poste_list.get(link, {}).get('running', False):
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
                            print(f"[Аккаунт {self.account_index+1}] Не удалось отправить лог: {log_err}")
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                    try:
                        await self.client.forward_messages(chat_id, messages=data['msg_id'], from_peer=data['entity'])
                        success += 1
                    except Exception:
                        fail += 1
                except Exception as e:
                    fail += 1
                    if log_chat_id:
                        try:
                            chat_entity = await self.client.get_entity(chat_id)
                            chat_name = chat_entity.title if hasattr(chat_entity, 'title') else "Личный чат"
                            log_msg = f"<b>⛧ ОШИБКА РАССЫЛКИ ⛧</b>\n\n<b>Пост:</b> {link}\n<b>Чат:</b> {chat_name} ({chat_id})\n<b>Ошибка:</b> {str(e)}"
                            await self.client.send_message(int(log_chat_id), log_msg, parse_mode='html')
                        except Exception:
                            pass
                await asyncio.sleep(2)
            
            elapsed = int(time.time() - data['start_time'])
            elapsed_str = str(timedelta(seconds=elapsed))
            report = f"<b>⛧ ОТЧЁТ О РАССЫЛКЕ ⛧</b>\n\n<b>Успешно:</b> {success}\n<b>Неудачно:</b> {fail}\n<b>Времени прошло:</b> {elapsed_str}\n<b>Ссылка:</b> {link}\n\nПовтор через {interval_minutes} мин..."
            
            try:
                await self.client.send_message(original_chat, report, parse_mode='html')
            except Exception as e:
                print(f"[Аккаунт {self.account_index+1}] Не удалось отправить отчёт: {e}")
            
            if link in self.poste_list:
                self.poste_list[link]['start_time'] = time.time()
                self.save_json(self.poste_file, self.poste_list)
            
            await asyncio.sleep(interval_minutes * 60)
        
        if link in self.poste_list:
            original_chat = self.poste_list[link].get('original_chat')
            if original_chat:
                try:
                    await self.client.send_message(original_chat, f"<b>⛧ РАССЫЛКА ОСТАНОВЛЕНА ⛧</b>\n\n<b>Ссылка:</b> {link}", parse_mode='html')
                except:
                    pass
            del self.poste_list[link]
            self.save_json(self.poste_file, self.poste_list)

    async def poste_stop_handler(self, msg):
        args = await self.get_args(msg)
        if not args:
            for link in list(self.poste_list.keys()):
                self.poste_list[link]['running'] = False
            self.poste_list.clear()
            self.save_json(self.poste_file, self.poste_list)
            return await msg.edit("<b>все рассылки остановлены</b>", parse_mode='html')
        link = args.strip()
        if link in self.poste_list:
            self.poste_list[link]['running'] = False
            del self.poste_list[link]
            self.save_json(self.poste_file, self.poste_list)
            await msg.edit(f"<b>рассылка для {link} остановлена</b>", parse_mode='html')
        else:
            await msg.edit(f"<b>рассылка для {link} не найдена</b>", parse_mode='html')

    async def poste_list_handler(self, msg):
        if not self.poste_list:
            return await msg.edit("<b>активных рассылок нет</b>", parse_mode='html')
        lines = []
        for link, data in self.poste_list.items():
            lines.append(f"ссылка: {link}\n  чатов: {len(data['chats'])} интервал: {data['interval']} мин")
        await msg.edit("<b>активные рассылки:</b>\n" + "\n".join(lines), parse_mode='html')

    async def pblk_handler(self, msg):
        args = await self.get_args(msg)
        if not args:
            return await msg.edit("<b>использование: .pblk list|add id|del id|clear</b>", parse_mode='html')
        parts = args.split()
        action = parts[0].lower()
        
        if action == 'list':
            if not self.poste_blocklist:
                return await msg.edit("<b>блок-лист пуст</b>", parse_mode='html')
            lines = []
            for cid in self.poste_blocklist:
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
                if chat_id not in self.poste_blocklist:
                    self.poste_blocklist.append(chat_id)
                await msg.edit(f"<b>чат {chat_id} добавлен в блок-лист</b>", parse_mode='html')
                self.save_json(self.blocklist_file, self.poste_blocklist)
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
                if chat_id in self.poste_blocklist:
                    self.poste_blocklist.remove(chat_id)
                await msg.edit(f"<b>чат {chat_id} удалён из блок-листа</b>", parse_mode='html')
                self.save_json(self.blocklist_file, self.poste_blocklist)
            except Exception as e:
                await msg.edit(f"<b>ошибка: {e}</b>", parse_mode='html')
        
        elif action == 'clear':
            self.poste_blocklist.clear()
            self.save_json(self.blocklist_file, self.poste_blocklist)
            await msg.edit("<b>блок-лист очищен</b>", parse_mode='html')
        
        else:
            await msg.edit("<b>неизвестное действие. доступно: list, add, del, clear</b>", parse_mode='html')

    async def pblkclear_handler(self, msg):
        self.poste_blocklist.clear()
        self.save_json(self.blocklist_file, self.poste_blocklist)
        await msg.edit("<b>блок-лист полностью очищен</b>", parse_mode='html')

    async def zw_handler(self, msg):
        self.spam_state.clear()
        self.tagger_chats.clear()
        
        for link in list(self.poste_list.keys()):
            self.poste_list[link]['running'] = False
        self.poste_list.clear()
        
        for sid in list(self.active_searches.keys()):
            if self.active_searches[sid].get('active', False):
                self.active_searches[sid]['active'] = False
                if self.active_searches[sid].get('task'):
                    self.active_searches[sid]['task'].cancel()
            del self.active_searches[sid]
        
        for chat_id, task in list(self.active_calendars.items()):
            task.cancel()
        self.active_calendars.clear()
        
        for chat_id, users in list(self.track_list.items()):
            for user_id, data in list(users.items()):
                task = data.get('task')
                if task and not task.done():
                    task.cancel()
        self.track_list.clear()
        self.save_track_list()
        
        if self._target_timer_task and not self._target_timer_task.done():
            self._target_timer_task.cancel()
        self.target_user = None
        self.target_chat_id_for_timer = None
        
        self.save_all_state()
        
        await msg.edit("<b>все функции остановлены</b>", parse_mode='html')

    async def run(self):
        await self.client.start()
        print(f"[Аккаунт {self.account_index+1}] Бот запущен! ({self.client.session.filename})", flush=True)
        me = await self.client.get_me()
        print(f"[Аккаунт {self.account_index+1}] Имя: {me.first_name} (@{me.username})", flush=True)
        print(f"[Аккаунт {self.account_index+1}] Команды загружены. Ожидание сообщений...", flush=True)

        @self.client.on(events.NewMessage)
        async def handler(event):
            msg = event.message
            text = msg.text or ""
            
            if not msg.out:
                await self.watcher(msg)
                
                if self.target_user and not msg.out:
                    sender = await msg.get_sender()
                    if sender and (sender.username == self.target_user or str(sender.id) == self.target_user):
                        try:
                            await msg.delete()
                        except:
                            pass
                
                chat_id = msg.chat_id
                if chat_id in self.track_list:
                    user_id = msg.sender_id
                    if user_id in self.track_list[chat_id]:
                        old_task = self.track_list[chat_id][user_id].get('task')
                        if old_task and not old_task.done():
                            old_task.cancel()
                        
                        user_name = self.track_list[chat_id][user_id].get('name', str(user_id))
                        username = self.track_list[chat_id][user_id].get('username', '')
                        chat_entity = await msg.get_chat()
                        chat_name = await self.get_entity_name(chat_entity)
                        
                        async def track_wait_and_notify():
                            await asyncio.sleep(3600)
                            try:
                                for i in range(3):
                                    await self.client.send_message(
                                        chat_id,
                                        f"<b>⛧ Слежение ⛧</b>\n\n"
                                        f"<b>Пользователь:</b> {user_name} {username}\n"
                                        f"<b>Статус:</b> не писал 1 час\n\n"
                                        f"<b>Слежение отключено</b>",
                                        parse_mode='html'
                                    )
                                    if i < 2:
                                        await asyncio.sleep(3)
                            except Exception as e:
                                print(f"[Аккаунт {self.account_index+1}] Ошибка отправки уведомления о слежении: {e}")
                            
                            if chat_id in self.track_list and user_id in self.track_list[chat_id]:
                                del self.track_list[chat_id][user_id]
                                if not self.track_list[chat_id]:
                                    del self.track_list[chat_id]
                                self.save_track_list()
                        
                        new_task = asyncio.create_task(track_wait_and_notify())
                        self.track_list[chat_id][user_id]['task'] = new_task
                return
            
            if not text:
                return
            
            print(f"[Аккаунт {self.account_index+1}] Команда: {text[:100]}", flush=True)
            
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
            elif text.startswith('.track') and not text.startswith('.trackoff') and not text.startswith('.tracklist'): await self.track_handler(msg)
            elif text.startswith('.trackoff'): await self.trackoff_handler(msg)
            elif text.startswith('.tracklist'): await self.tracklist_handler(msg)
            elif text.startswith('.detect ') and not text.startswith('.detectoff') and not text.startswith('.detectlist'): await self.detect_handler(msg)
            elif text.startswith('.detectoff'): await self.detectoff_handler(msg)
            elif text.startswith('.detectlist'): await self.detectlist_handler(msg)
            elif text.startswith('.help'): await self.help_handler(msg)
            elif text.startswith('.menu'): await self.menu_handler(msg)
            elif text.startswith('.more'): await self.more_handler(msg)
            elif text.startswith('.custom'): await self.custom_handler(msg)
            elif text.startswith('.files'): await self.files_handler(msg)
            elif text.startswith('.postecom'): await self.postecom_handler(msg)
            elif text.startswith('.x0'): await self.x0_handler(msg)
            elif text.startswith('.poste ') and not text.startswith('.poste_stop') and not text.startswith('.poste_list'): await self.poste_handler(msg)
            elif text.startswith('.poste_stop'): await self.poste_stop_handler(msg)
            elif text.startswith('.poste_list'): await self.poste_list_handler(msg)
            elif text.startswith('.pblk '): await self.pblk_handler(msg)
            elif text.startswith('.pblkclear'): await self.pblkclear_handler(msg)
            elif text.startswith('.status'): await self.status_handler(msg)
            elif text.startswith('.zw'): await self.zw_handler(msg)
            elif text.startswith('.reply') or text.startswith('.creply') or text.startswith('.reply_list') or text.startswith('.reply_time') or text.startswith('.reply_media'):
                await self.autoreply_handler(msg)
            elif text.startswith('.reload'): await self.reload_handler(msg)
            else:
                print(f"[Аккаунт {self.account_index+1}] Неизвестная команда: {text[:50]}", flush=True)

        await self.client.run_until_disconnected()


# ==================== ЗАПУСК ВСЕХ АККАУНТОВ ====================
async def main():
    """Запускает все аккаунты из списка ACCOUNTS"""
    bots = []
    for i in range(len(ACCOUNTS)):
        bot = Userbot(i)
        bots.append(bot)
        asyncio.create_task(bot.run())
    
    # Keep the main loop running
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    # Запуск веб-сервера для Render в отдельном потоке
    threading.Thread(target=run_web, daemon=True).start()
    # Запуск основного цикла
    asyncio.run(main())
