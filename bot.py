import os
import time
import json
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
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

# ========== КОМАНДИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Жарт", "Філософ", "Поясни простіше"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привіт! Я GPT-бот. Напиши щось — я відповім 🤖",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/mode — змінити режим\n/reset — скинути режим\n/stats — статистика\n/admin — тільки для власника")

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

# ========== ПОВІДОМЛЕННЯ ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    message = update.message.text.strip().lower()

    # Антиспам: 3 сек між повідомленнями
    now = time.time()
    last = context.user_data.get("last_msg", 0)
    if now - last < 3:
        await update.message.reply_text("Повільніше 😉 (чекай 3 секунди)")
        return
    context.user_data["last_msg"] = now

    # Обробка вибору кнопками
    if message in ["жарт", "жартівник"]:
        user_data[uid] = {"mode": "жартівник"}
        await update.message.reply_text("Режим: Жартівник 🤪")
        return
    elif message in ["філософ"]:
        user_data[uid] = {"mode": "філософ"}
        await update.message.reply_text("Режим: Філософ 🤔")
        return
    elif message in ["поясни простіше", "простий"]:
        user_data[uid] = {"mode": "простий"}
        await update.message.reply_text("Режим: Простий 👶")
        return

    # Логування
    log(f"[{uid}] {update.effective_user.first_name}: {message}")

    # Визначення режиму
    mode = user_data.get(uid, {}).get("mode", "звичайний")
    prompt = get_mode_prompt(mode)

    # Статистика
    user_stats[uid] = user_stats.get(uid, 0) + 1

    # GPT
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": update.message.text}
            ]
        )
        reply = completion.choices[0].message.content
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
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        print("Bot pratsiuie...")
        app.run_polling()
    except Exception as e:
        log(f"LAUNCH ERROR: {e}")