import logging
import os
import random
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# =============================================
# НАЛАШТУВАННЯ — змінюй тут
# =============================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Встановлюється через змінну середовища (Railway)

# ID або username юзера якого коверкаємо
TARGET_USER_ID = 1175961985  # замінити на реальний ID

# =============================================
# ПРАВИЛА КОВЕРКАННЯ ТЕКСТУ
# =============================================

LETTER_REPLACEMENTS = {
    "ж": "з",
    "ш": "шь",
    "щ": "щь",
    "р": "л",
    "б": "п",
    "в": "ф",
    "г": "г",
    "д": "т",
    "х": "ф",

    "уже": "узе",
    "вже": "взе",
    "дістав": "дістявь",
    "дістала": "дістяла",
    "сказав": "сказавь",
    "сказала": "скязаля",
    "пішов": "пішоль",
    "пішла": "пішля",
    "Іван": "Твій Господар а не Іван по перше",
    "Ваня": "Твій Господар а не Ваня по перше",
    "Банку знаєш": "Баньку знаєсь",
}

SUFFIXES = [
    ", Сєрєнький, закинь 50 грн на банку",
    ", та нє друже, це з тебе поповнення банки",
    ", ти шо мєрзавчєка дав?",
    ", бо поїдеш в Лозову на 2 роки",
    ", 100 грн на банку, чекаю",
    ", Сєрий, з тебе штраф 20 грн",
    ", чекаю тебе на Балохаусі",
]

WATCHED_USERNAMES = {"vanesique", "xxinstein", "vakulabiceps", "Damarkus22", "S1DAR", "Sidar"}

VOICE_FILES = [
    "sho_zaschi.ogg",
    "chuyesh.ogg",
    "dvakharkivchanina.ogg",
    "gomony.ogg",
]

REPLY_RESPONSES = [
    "Май повагу, ти з кепом розмовляєш",
    "Ти шось поплутав друже, закинь но 50 грн на банку",
    "Ще раз і попиздуєш в аренду до фаленів",
    "20 грн на баночку хопчику, Бало зафіксуй",
    "Нє братику, це так не працює, баночку знаєш",
]

# =============================================
# ЛОГІКА КОВЕРКАННЯ
# =============================================

PROB = 0.3

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

_suffix_queue: list = []
_reply_queue: list = []
_voice_queue: list = []

def next_suffix() -> str:
    global _suffix_queue
    if not _suffix_queue:
        _suffix_queue = SUFFIXES[:]
        random.shuffle(_suffix_queue)
    return _suffix_queue.pop()


def next_reply_response() -> str:
    global _reply_queue
    if not _reply_queue:
        _reply_queue = REPLY_RESPONSES[:]
        random.shuffle(_reply_queue)
    return _reply_queue.pop()


def next_voice() -> str:
    global _voice_queue
    if not _voice_queue:
        _voice_queue = VOICE_FILES[:]
        random.shuffle(_voice_queue)
    return _voice_queue.pop()


def mangle_text(text: str) -> str:
    result = text
    for original, replacement in LETTER_REPLACEMENTS.items():
        if random.random() < PROB:
            pattern = re.compile(re.escape(original), re.IGNORECASE)
            result = pattern.sub(replacement, result)
    result = result.rstrip() + next_suffix()
    return result


# =============================================
# ОБРОБНИК ПОВІДОМЛЕНЬ
# =============================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    user = message.from_user
    if not user:
        return

    mentioned_watched = any(
        f"@{uname.lower()}" in message.text.lower()
        for uname in WATCHED_USERNAMES
    )
    replied_to_watched = (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.username
        and message.reply_to_message.from_user.username in WATCHED_USERNAMES
    )

    if mentioned_watched or replied_to_watched:
        voice_file = next_voice()
        voice_path = os.path.join(os.path.dirname(__file__), voice_file)
        logging.info(f"[{user.username or user.id}] triggered voice → {voice_file}")
        with open(voice_path, "rb") as vf:
            await message.reply_voice(vf)
        return

    if (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.is_bot
    ):
        response = next_reply_response()
        logging.info(f"[{user.username or user.id}] replied to bot → sending: {response}")
        await message.reply_text(response)
        return

    if user.id != TARGET_USER_ID:
        return

    if random.random() >= PROB:
        return

    original_text = message.text
    mangled = mangle_text(original_text)

    logging.info(f"[{user.username or user.id}] Original: {original_text}")
    logging.info(f"[{user.username or user.id}] Mangled:  {mangled}")

    await message.reply_text(mangled)


# =============================================
# ЗАПУСК
# =============================================

if __name__ == "__main__":
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не встановлено! Додай змінну середовища BOT_TOKEN.")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущений! Ctrl+C для зупинки.")
    app.run_polling()
