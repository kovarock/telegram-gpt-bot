import os
import time
import json
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, MessageHandler, filters
)
from openai import OpenAI

# ========== .ENV ==========
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ========== GPT ==========
client = OpenAI(api_key=OPENAI_API_KEY)

# ========== ЗМІННІ ==========
user_data = {}
admin_id = 898106096
user_stats = {}
LOG_FILE = "logs.txt"
DB_FILE = "analytics.db"
MONO_DONATE_LINK = "https://send.monobank.ua/jar/5TCxdr4z1P"
VIP_FILE = "vip_users.json"

# ========== ДОПОМІЖНІ ==========
def log(text):
    print(text)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def get_mode_prompt(mode):
    return {
        "звичайний": "Ти корисний асистент, що відповідає українською.",
        "жартівник": "Ти дотепний GPT, який відповідає з гумором і сарказмом.",
        "філософ": "Ти глибокий мислитель, який дає мудрі і розгорнуті відповіді.",
        "простий": "Ти пояснюєш складні речі дуже просто, як для 10-річної дитини."
    }.get(mode, "Ти корисний асистент, що відповідає українською.")

def save_to_db(user_id, name, message):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
            user_id INTEGER,
            name TEXT,
            message TEXT,
            timestamp TEXT
        )''')
        cursor.execute("INSERT INTO messages VALUES (?, ?, ?, ?)",
                       (user_id, name, message, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        log(f"DB ERROR: {e}")

def load_vips():
    if not os.path.exists(VIP_FILE): return []
    with open(VIP_FILE, "r") as f:
        return json.load(f)

def save_vips(vips):
    with open(VIP_FILE, "w") as f:
        json.dump(vips, f)

# ========== КОМАНДИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Жарт", "Філософ", "Поясни простіше"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привіт! Я GPT-бот. Напиши щось — я відповім 🤖",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/mode — змінити режим\n/reset — скинути режим\n/stats — статистика\n/donate — підтримати бота\n/premium — доступ до GPT-4\n/addvip <id> — додати VIP\n/removevip <id> — видалити VIP\n/viplist — список VIP")

async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Оберіть режим: жартівник / філософ / простий")

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {"mode": "звичайний"}
    await update.message.reply_text("Режим скинуто до стандартного")

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == admin_id:
        await update.message.reply_text("Привіт, адміне! Бот живий і здоровий 💪")
    else:
        await update.message.reply_text("Ця команда доступна тільки адміну")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = len(user_stats)
    total = sum(user_stats.values())
    await update.message.reply_text(f"Користувачів: {count}\nВсього запитів: {total}")

async def donate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Підтримати в Monobank ❤️", url=MONO_DONATE_LINK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("💛 Хочеш підтримати розвиток бота? Буду дуже вдячний за донат!", reply_markup=reply_markup)

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("💰 Підтримати в Monobank", url=MONO_DONATE_LINK),
            InlineKeyboardButton("📩 Написати автору", url="https://t.me/kovarock")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("💎 Хочеш доступ до GPT-4? Підтримай проєкт(50 грн/тиж) і напиши автору!", reply_markup=reply_markup)

async def addvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != admin_id:
        return
    try:
        uid = int(context.args[0])
        vips = load_vips()
        if uid not in vips:
            vips.append(uid)
            save_vips(vips)
            await update.message.reply_text(f"✅ Користувача {uid} додано до VIP")
        else:
            await update.message.reply_text(f"⚠️ Користувач {uid} вже є у VIP")
    except:
        await update.message.reply_text("Використання: /addvip <user_id>")

async def removevip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != admin_id:
        return
    try:
        uid = int(context.args[0])
        vips = load_vips()
        if uid in vips:
            vips.remove(uid)
            save_vips(vips)
            await update.message.reply_text(f"❌ Користувача {uid} видалено з VIP")
        else:
            await update.message.reply_text(f"Користувача {uid} немає у VIP")
    except:
        await update.message.reply_text("Використання: /removevip <user_id>")

async def viplist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != admin_id:
        return
    vips = load_vips()
    await update.message.reply_text("VIP користувачі:\n" + "\n".join(map(str, vips)))

async def limits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ /limits була викликана")

    uid = update.effective_user.id
    today = datetime.now().date().isoformat()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Створюємо таблицю, якщо ще не існує
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            user_id INTEGER,
            name TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)

    # Рахуємо кількість повідомлень за сьогодні
    cursor.execute("""
        SELECT COUNT(*) FROM messages
        WHERE user_id = ? AND DATE(timestamp) = ?
    """, (uid, today))
    count_today = cursor.fetchone()[0]

    conn.close()

    vips = load_vips()
    limit = "∞ (VIP)" if uid in vips or uid == admin_id else f"{count_today}/10"
    await update.message.reply_text(f"📊 Запитів сьогодні: {limit}")



async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    name = user.first_name
    vips = load_vips()
    status = "VIP ⭐" if uid in vips or uid == admin_id else "Звичайний користувач"

    today = datetime.now().date().isoformat()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM messages
        WHERE user_id = ? AND DATE(timestamp) = ?
    """, (uid, today))
    count_today = cursor.fetchone()[0]
    conn.close()

    text = (
        f"👤 Профіль користувача\n"
        f"Імʼя: {name}\n"
        f"ID: {uid}\n"
        f"Статус: {status}\n"
        f"Сьогоднішні запити: {count_today}/10"
        )
    
    await update.message.reply_text(text)

# ========== ПОВІДОМЛЕННЯ ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name
    message = update.message.text.strip()

    now = time.time()
    last = context.user_data.get("last_msg", 0)
    if now - last < 3:
        await update.message.reply_text("Повільніше 😉 (чекай 3 секунди)")
        return
    context.user_data["last_msg"] = now

    lower = message.lower()
    if lower in ["жарт", "жартівник"]:
        user_data[uid] = {"mode": "жартівник"}
        await update.message.reply_text("Режим: Жартівник 🤪")
        return
    elif lower in ["філософ"]:
        user_data[uid] = {"mode": "філософ"}
        await update.message.reply_text("Режим: Філософ 🤔")
        return
    elif lower in ["поясни простіше", "простий"]:
        user_data[uid] = {"mode": "простий"}
        await update.message.reply_text("Режим: Простий 👶")
        return

    log(f"[{uid}] {name}: {message}")
    save_to_db(uid, name, message)

    mode = user_data.get(uid, {}).get("mode", "звичайний")
    prompt = get_mode_prompt(mode)

    user_stats[uid] = user_stats.get(uid, 0) + 1

    vips = load_vips()
    model_name = "gpt-4o" if uid in vips or uid == admin_id else "gpt-3.5-turbo"
    # Обмеження запитів
    today = datetime.now().date().isoformat()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM messages
        WHERE user_id = ? AND DATE(timestamp) = ?
    """, (uid, today))
    count_today = cursor.fetchone()[0]
    conn.close()

    if uid not in vips and uid != admin_id and count_today >= 10:
        await update.message.reply_text("⚠️ Ви досягли ліміту 10 запитів на день. Напишіть /premium, щоб отримати більше.")
        return

    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message}
            ]
        )
        reply = completion.choices[0].message.content

        if uid not in vips and uid != admin_id:
            reply += "\n\n⚠️ Це відповідь від GPT-3.5. Для GPT-4 напиши /premium"

        keyboard = [["Жарт", "Філософ", "Поясни простіше"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(reply, reply_markup=reply_markup)
    except Exception as e:
        await update.message.reply_text("⚠️ Виникла помилка при зверненні до GPT")
        log(f"GPT ERROR: {e}")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    try:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("mode", mode_command))
        app.add_handler(CommandHandler("reset", reset_command))
        app.add_handler(CommandHandler("admin", admin_command))
        app.add_handler(CommandHandler("stats", stats_command))
        app.add_handler(CommandHandler("donate", donate_command))
        app.add_handler(CommandHandler("premium", premium_command))
        app.add_handler(CommandHandler("addvip", addvip))
        app.add_handler(CommandHandler("removevip", removevip))
        app.add_handler(CommandHandler("viplist", viplist))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(CommandHandler("limits", limits_command))
        app.add_handler(CommandHandler("profile", profile_command))


        print("Bot pratsiuie... (GPT-4 для VIP, GPT-3.5 для інших)")
        app.run_polling()
    except Exception as e:
        log(f"LAUNCH ERROR: {e}")