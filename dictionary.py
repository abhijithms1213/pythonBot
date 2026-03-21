import logging
from xml.etree.ElementTree import tostring

import db_management
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import os

load_dotenv()
tele_user_me = int(os.getenv("TELEGRAM_USER_ME"))

batches = 'batches'
# batches
# +-----------------------------------------------------+
# | sql                                                 |
# +-----------------------------------------------------+
# | CREATE TABLE batches(                               |
# | Date_id int NOT NULL PRIMARY KEY,                   |
# | Planning_Date int, isCurrent BOOLEAN, deadline int) |
# +-----------------------------------------------------++

dev_ids = 'dev'
# +----------------------------------------------------------+
# | sql                                                      |
# +----------------------------------------------------------+
# | CREATE TABLE "dev_ids"(                                  |
# | batch_id_date int ,                                      |
# | tele_id int,                                             |
# | FOREIGN KEY (batch_id_date) REFERENCES batches (Date_id) |
# | )                                                        |
# +----------------------------------------------------------+

team_ids = 'teamid'
# +-----------------------------------------------------+
# | sql                                                 |
# +-----------------------------------------------------+
# | CREATE TABLE team_ids(                              |
# | batch_id int,                                       |
# | team_id_docs int,                                   |
# | FOREIGN KEY (batch_id) REFERENCES batches (Date_id) |
# | )                                                   |
# +-----------------------------------------------------+


# from dotenv import load_dotenv
# load_dotenv()

# or this way it can be done
import dotenv

dotenv.load_dotenv()
import os

TELEGRAM_BOT_TOKEN_TEST = os.getenv("TELEGRAM_BOT_TOKEN_TEST")

district = {
    "brand": "Ford",
    "model": "Mustang",
    "year": 1964
}

print(district)


def batchcreates(date):
    db_management.dbops('check_batch', date)


def checkMsg(msg_date):
    date_to_string = str(msg_date)
    date_only = date_to_string[:10]
    print(f'msg date: {date_only}')
    extracted = date_only.replace('-', '')
    to_int = int(extracted)
    db_management.dbops('check_is_msg_under_planning_phase', to_int)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text_caps = ' '.join(context.args).upper()
    print(text_caps)
    await context.bot.send_message(chat_id=update.message.chat_id, text=text_caps)
    print(f' id: {update.effective_chat.id} user: {update.message.chat} and {update.message.text}')


async def grp_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    zero_dev_grp_id = -5287913183
    current_id = update.message.chat.id
    if zero_dev_grp_id == current_id:
        print(
            f'msg:{update.message.from_user.username} {update.message.from_user.id}  and  {update.message.text} {update.message.date}\n')
        checkMsg(update.message.date)

        # await  context.bot.send_message(chat_id=zero_dev_grp_id, text='ok')
    else:
        print(f'other chat :{update.message.text}')


async def create_batch_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    arg_text = " ".join(context.args)
    tele_uid = update.message.from_user.id
    # check if am I sending the command
    if tele_uid != tele_user_me:
        await context.bot.send_message(chat_id=update.message.chat_id, text='poda podaaaa')

    print(f'args {arg_text} and {tele_uid}')
    if not arg_text:
        await  context.bot.send_message(chat_id=update.message.chat_id,
                                        text='formate will be yyyy-mm-dd')
        return

    await  context.bot.send_message(chat_id=update.message.chat_id,
                                    text='remember not start a batch on month ends , need 2 day gap')
    batchcreates(arg_text)
    # if tuple found in table  with matching date(id) then not need to add


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print('hai')


def pybot():
    if TELEGRAM_BOT_TOKEN_TEST is None:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN_TEST).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("grp", create_batch_group))
    grp_msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), grp_msg)
    application.add_handler(grp_msg_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


pybot()
