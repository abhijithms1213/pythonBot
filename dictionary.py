import logging

import db_management
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

batches = 'batches'
# batches
# +-----------------------------------+
# | sql                               |
# +-----------------------------------+
# | CREATE TABLE batches(             |
# | Date_id int NOT NULL PRIMARY KEY, |
# | Planning_Date int,                |
# | isPlanned BOOLEAN,                | not necessary
# | members int)                      |
# +-----------------------------------+

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text_caps = ' '.join(context.args).upper()
    print(text_caps)
    await context.bot.send_message(chat_id=update.message.chat_id, text=text_caps)
    print(f' id: {update.effective_chat.id} user: {update.message.chat} and {update.message.text}')


async def grp_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    userDictionary = {}
    zero_dev_grp_id = -5287913183
    current_id = update.message.chat.id
    if zero_dev_grp_id == current_id:
        print(f'msg:{update.message.from_user.username} {update.message.from_user.id}  and  {update.message.text} \n')
        # await  context.bot.send_message(chat_id=zero_dev_grp_id, text='ok')
    else:
        print(f'other chat :{update.message.text}')


def batchcreates(date):
    print('hai')
    db_management.dbops('check_batch', date)


async def create_batch_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    arg_text = " ".join(context.args)
    tele_uid = update.message.from_user.id
    # check if am I sending the command
    if tele_uid != 1054613006:
        await context.bot.send_message(chat_id=update.message.chat_id, text='poda podaaaa')

    print(f'args {arg_text} and {tele_uid}')
    if not arg_text:
        await  context.bot.send_message(chat_id=update.message.chat_id,
                                        text='formate will be dd-mm-yyyy')
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
