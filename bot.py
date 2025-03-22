
import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from openai import OpenAI

# Завантаження змінних з .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# GPT-клієнт
client = OpenAI(api_key=OPENAI_API_KEY)

# Команди
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Жарт", "Філософ", "Поясни простіше"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привіт! Я GPT-бот. Напиши щось — я відповім 🤖", reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Напиши будь-яке повідомлення, і я дам відповідь. "
        "Можеш також натискати кнопки, щоб змінювати стиль відповіді:\n"
        "- Жарт 🃏\n- Філософ 🤔\n- Поясни простіше 👶"
    )

# Обробка повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip().lower()

    # Зміна режиму на основі натиснутої кнопки
    if user_message in ["жарт", "жартівник"]:
        context.user_data["mode"] = "жартівник"
        await update.message.reply_text("Режим: Жартівник увімкнено 😄")
        return
    elif user_message in ["філософ"]:
        context.user_data["mode"] = "філософ"
        await update.message.reply_text("Режим: Філософ 🤔")
        return
    elif user_message in ["поясни простіше", "простий"]:
        context.user_data["mode"] = "простий"
        await update.message.reply_text("Режим: Просте пояснення 👶")
        return

    # Вибір режиму (за замовчуванням — звичайний)
    mode = context.user_data.get("mode", "звичайний")

    system_prompt = {
        "звичайний": "Ти корисний асистент, що відповідає українською.",
        "жартівник": "Ти дотепний GPT, який відповідає з гумором і сарказмом.",
        "філософ": "Ти глибокий мислитель, який дає мудрі і розгорнуті відповіді.",
        "простий": "Ти пояснюєш складні речі дуже просто, як для 10-річної дитини."
    }[mode]

    # GPT-запит
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": update.message.text}
        ]
    )

    reply = completion.choices[0].message.content

    # Кнопки
    keyboard = [["Жарт", "Філософ", "Поясни простіше"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(reply, reply_markup=reply_markup)

# Запуск бота
if __name__ == "__main__":
    try:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        print("Bot pratsiuie...")
        app.run_polling()
    except Exception as e:
        print(f"Pomylka zapusku: {e}")
