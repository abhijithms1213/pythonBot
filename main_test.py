import logging
import os

from dotenv import load_dotenv
from telegram import ForceReply, Update
from telegram.ext import (Application, CommandHandler, ContextTypes, MessageHandler, filters)

load_dotenv()

GRP_ID = "-5287913183"
TELEGRAM_BOT_TOKEN_TEST = os.getenv("TELEGRAM_BOT_TOKEN_TEST")
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def grp_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    user = update.effective_user
    message = update.message.text
    chat_id = update.effective_chat.id if update.effective_chat else ""
    if not chat_id:
        return
    if update.effective_chat.id != -5287913183:
        return
    mentions = []

    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == "mention":
                mention = message[entity.offset: entity.offset + entity.length]
                mentions.append(mention)

            elif entity.type == "text_mention":
                mentioned_user = entity.user
                mentions.append(f"{mentioned_user.first_name} ({mentioned_user.id})")

    if mentions:
        logger.info(f"Mentions found: {mentions}")

    if message.startswith("Z0:"):
        logger.info(f"{user.first_name} {user.id}: starts with Z0: {message}")
    else:
        logger.info(f"{user.first_name} {user.id}: {message}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await  update.message.reply_html(rf"Hi {user.mention_html()}!", reply_markup=ForceReply(selective=True)),


def main():
    if TELEGRAM_BOT_TOKEN_TEST is None:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN_TEST).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, grp_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    # application.run_polling()


# if __name__ == "__main_test__":
main()
