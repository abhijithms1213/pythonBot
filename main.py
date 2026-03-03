import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          MessageHandler, filters)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def vivi_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id if update.effective_chat else ""
    if not chat_id:
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text="Hello, I am Vivi!",
    )


async def vivi_greet_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id if update.effective_chat else ""
    if not chat_id:
        return

    user_message = update.message.text if update.message else ""
    if not user_message:
        return

    username = update.effective_user.first_name if update.effective_user else ""
    if not username:
        return

    vivi_reply = ""
    if user_message.lower() == "hi":
        vivi_reply = f"Hi, {username}!"

    if not vivi_reply:
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text=vivi_reply,
    )


async def cmd_caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return
    text_caps = " ".join(context.args).upper()

    chat_id = update.effective_chat.id if update.effective_chat else ""
    if not chat_id:
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text=text_caps,
    )


if __name__ == "__main__":
    if TELEGRAM_BOT_TOKEN is None:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set")

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    start_handler = CommandHandler("start", vivi_intro)
    application.add_handler(start_handler)

    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), vivi_greet_member)
    application.add_handler(echo_handler)

    caps_handler = CommandHandler("caps", cmd_caps)
    application.add_handler(caps_handler)

    application.run_polling()
