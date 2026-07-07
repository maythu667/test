import sqlite3
import asyncio
import random
import time

from telethon import TelegramClient, events
from config import *

# ==========================
# BOT START
# ==========================

bot = TelegramClient(
    "group_ai_bot",
    API_ID,
    API_HASH
).start(bot_token=BOT_TOKEN)

print("✅ Bot Started")

# ==========================
# DATABASE
# ==========================

db = sqlite3.connect(
    "memory.db",
    check_same_thread=False
)

cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS memory(
id INTEGER PRIMARY KEY AUTOINCREMENT,
chat_id INTEGER,
text TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS keywords(
chat_id INTEGER,
trigger TEXT,
reply TEXT
)
""")

db.commit()

print("✅ Database Ready")

# ==========================
# BOT ONLINE
# ==========================

@bot.on(events.NewMessage(pattern="/start"))
async def start(event):

    if not event.is_private:
        return

    await event.reply(
        "🤖 AI Memory Bot Online!\n\n"
        "Add me to your group."
    )

# ==========================
# MAIN
# ==========================

async def main():

    print("🚀 Running...")

    await bot.run_until_disconnected()

bot.loop.run_until_complete(main())

import re
import time
import random

# ==========================
# MEMORY SETTINGS
# ==========================

REPLY_COOLDOWN = 20
last_reply = {}

URL_PATTERN = re.compile(r"https?://|www\.|t\.me/")
MENTION_PATTERN = re.compile(r"@\w+")

def can_learn(text):

    if not text:
        return False

    text = text.strip()

    if len(text) < 2:
        return False

    if len(text) > 150:
        return False

    if URL_PATTERN.search(text):
        return False

    if MENTION_PATTERN.search(text):
        return False

    return True

# ==========================
# MEMORY LEARN
# ==========================

@bot.on(events.NewMessage(incoming=True))
async def memory_learn(event):

    if event.is_private:
        return

    if event.sender.bot:
        return

    text = event.raw_text

    if not can_learn(text):
        return

    cursor.execute(
        "INSERT INTO memory(chat_id,text) VALUES(?,?)",
        (event.chat_id, text)
    )

    db.commit()

# ==========================
# HUMAN AUTO REPLY
# ==========================

@bot.on(events.NewMessage(incoming=True))
async def ai_reply(event):

    if event.is_private:
        return

    if event.sender.bot:
        return

    now = time.time()

    if now - last_reply.get(event.chat_id, 0) < REPLY_COOLDOWN:
        return

    rows = cursor.execute(
        """
        SELECT text
        FROM memory
        WHERE chat_id=?
        ORDER BY RANDOM()
        LIMIT 20
        """,
        (event.chat_id,)
    ).fetchall()

    if not rows:
        return

    text = event.raw_text.lower()

    best = []

    for row in rows:

        msg = row[0]

        if msg.lower() == text:
            continue

        if any(word in msg.lower() for word in text.split()):
            best.append(msg)

    if best:
        reply = random.choice(best)
    else:
        reply = random.choice(rows)[0]

    await event.reply(reply)

    last_reply[event.chat_id] = now
    
    # ==========================
# CONTEXT + KEYWORD SYSTEM
# ==========================

CONTEXT = {}
REPLY_CHANCE = 35  # 35% chance to reply

def similarity(a, b):
    a = set(a.lower().split())
    b = set(b.lower().split())

    if not a or not b:
        return 0

    return len(a & b)

# --------------------------
# Save last message
# --------------------------
@bot.on(events.NewMessage(incoming=True))
async def remember_context(event):

    if event.is_private:
        return

    if event.sender.bot:
        return

    CONTEXT[event.chat_id] = event.raw_text

# --------------------------
# AI Reply
# --------------------------
@bot.on(events.NewMessage(incoming=True))
async def smart_ai(event):

    if event.is_private:
        return

    if event.sender.bot:
        return

    # Cooldown
    now = time.time()

    if now - last_reply.get(event.chat_id, 0) < REPLY_COOLDOWN:
        return

    # Random reply chance
    if random.randint(1,100) > REPLY_CHANCE:
        return

    text = event.raw_text.lower()

    # ======================
    # KEYWORD PRIORITY
    # ======================
    rows = cursor.execute(
        "SELECT trigger,reply FROM keywords WHERE chat_id=?",
        (event.chat_id,)
    ).fetchall()

    for trigger,reply in rows:

        if trigger.lower() in text:
            await event.reply(reply)
            last_reply[event.chat_id] = now
            return

    # ======================
    # MEMORY SEARCH
    # ======================
    rows = cursor.execute(
        """
        SELECT text
        FROM memory
        WHERE chat_id=?
        """,
        (event.chat_id,)
    ).fetchall()

    if not rows:
        return

    best_score = 0
    best_reply = None

    for row in rows:

        score = similarity(text,row[0])

        if score > best_score:
            best_score = score
            best_reply = row[0]

    if best_reply:
        await event.reply(best_reply)

    else:
        await event.reply(random.choice(rows)[0])

    last_reply[event.chat_id] = now
    
    from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji, SendMessageTypingAction

# ==========================
# BOT PERSONALITY
# ==========================

EMOJIS = [
    "😊","😂","🥺","😅","🤍",
    "❤️","👍","🔥","😆","😉",
    "😎","🤭","💖","✨"
]

PREFIX = [
    "",
    "ဟား ",
    "အင်း ",
    "ဟုတ်တယ် ",
    "အော် ",
    "ဟုတ်ကဲ့ ",
]

SUFFIX = [
    "",
    " 😊",
    " 😂",
    " ❤️",
    " 🤍",
    " 😅",
]

# ==========================
# TYPING EFFECT
# ==========================

async def typing(chat_id):

    try:
        async with bot.action(chat_id, SendMessageTypingAction()):
            await asyncio.sleep(random.uniform(0.5, 1.5))
    except:
        pass

# ==========================
# MAKE HUMAN REPLY
# ==========================

def make_reply(text):

    msg = random.choice(PREFIX) + text + random.choice(SUFFIX)

    if random.randint(1,100) <= 25:
        msg += " " + random.choice(EMOJIS)

    return msg

# ==========================
# RANDOM REACTION
# ==========================

@bot.on(events.NewMessage(incoming=True))
async def auto_reaction(event):

    if event.is_private:
        return

    if event.sender.bot:
        return

    if random.randint(1,100) > 30:
        return

    try:
        await bot(
            SendReactionRequest(
                peer=event.chat_id,
                msg_id=event.message.id,
                reaction=[
                    ReactionEmoji(
                        random.choice(
                            ["👍","❤️","😂","🔥","🥰","👏","🤍"]
                        )
                    )
                ]
            )
        )
    except:
        pass
        
        from collections import deque
import time

# ==========================
# CONVERSATION MEMORY
# ==========================

conversation = {}
last_user_message = {}
recent_replies = {}

MAX_CONTEXT = 15

def get_context(chat_id):
    if chat_id not in conversation:
        conversation[chat_id] = deque(maxlen=MAX_CONTEXT)
    return conversation[chat_id]

# ==========================
# SAVE CONTEXT
# ==========================

@bot.on(events.NewMessage(incoming=True))
async def save_context(event):

    if event.is_private:
        return

    if event.sender.bot:
        return

    text = (event.raw_text or "").strip()

    if len(text) < 2:
        return

    ctx = get_context(event.chat_id)
    ctx.append(text)

    last_user_message[event.chat_id] = text

# ==========================
# DUPLICATE FILTER
# ==========================

def can_send(chat_id, reply):

    old = recent_replies.get(chat_id)

    if old == reply:
        return False

    recent_replies[chat_id] = reply
    return True

# ==========================
# SPAM FILTER
# ==========================

def clean_text(text):

    text = text.strip()

    if len(text) < 2:
        return None

    if len(text) > 150:
        return None

    if text.count("http"):
        return None

    if text.count("@"):
        return None

    if text.count("#") > 3:
        return None

    return text

# ==========================
# SMART MEMORY SEARCH
# ==========================

def search_memory(chat_id, message):

    rows = cursor.execute(
        """
        SELECT text
        FROM memory
        WHERE chat_id=?
        """,
        (chat_id,)
    ).fetchall()

    if not rows:
        return None

    message = message.lower()

    best = None
    score = 0

    for row in rows:

        txt = row[0]

        s = 0

        for word in message.split():

            if word in txt.lower():
                s += 1

        if s > score:
            score = s
            best = txt

    return best

# ==========================
# SMART REPLY
# ==========================

async def send_ai_reply(event):

    text = clean_text(event.raw_text)

    if not text:
        return

    reply = search_memory(event.chat_id, text)

    if not reply:
        return

    if not can_send(event.chat_id, reply):
        return

    await typing(event.chat_id)

    await event.reply(make_reply(reply))
    
    import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

@bot.on(events.NewMessage(pattern=r"^ai (.+)"))
async def ai_chat(event):

    prompt = event.pattern_match.group(1)

    try:
        response = model.generate_content(prompt)

        await event.reply(response.text)

    except Exception as e:
        await event.reply(f"AI Error: {e}")
        
        import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)