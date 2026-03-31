from telegram.constants import ParseMode

import execution
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
    "year": 1964,
    "type": str
}

print(district)


async def batch_creates(date, context, update):
    status = await db_management.dbops('check_batch', date)
    if status == 'added_new_batch':
        await  context.bot.send_message(chat_id=update.message.chat_id,
                                        text='remember not start a batch on month ends , need 2 day gap')
    if status == 'running':
        await  context.bot.send_message(chat_id=update.message.chat_id,
                                        text='running a batch currently')


async def check_msg(msg_date, update, context):
    date_to_string = str(msg_date)
    date_only = date_to_string[:10]
    print(f'msg date: {date_only}')
    extracted = int(date_only.replace('-', ''))
    ret_status = await db_management.dbops('check_is_msg_under_planning_phase', extracted)
    status = ret_status[0]
    current_batch = ret_status[1]
    if status == 'during_planning_phase':
        #  get the return valid / invalid status then send message for each
        await  execution.msg_process(msg_date, update, context,current_batch)
    elif status == 'during_project_phase':
        return_value = await  execution.project_phase(msg_date, update, context,current_batch)
        if return_value:
            print('true returned')
        else:
            print('false returned')


async def grp_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(
        f'args:{update.message.text} user: name: {update.message.from_user.username} id:{update.message.from_user.id}')
    zero_dev_grp_id = -5287913183
    current_id = update.message.chat.id
    if zero_dev_grp_id == current_id:
        #  check mention working or not
        if update.message.text == 'mention':
            chat_id = update.effective_chat.id

            # user_id_no_username = 1536580544  # aleena
            user_id = 656166832  # Replace with a user ID who does not : aravind
            chat_usr = await context.bot.get_chat(chat_id=user_id)
            first_name = chat_usr.first_name
            print(f'first name:{first_name} id: {user_id}')

            # Construct the message using HTML parse mode
            message_text = f'Hello <a href="tg://user?id={user_id}">{first_name}</a> 👋'
            # Send the message with HTML parse mode
            await context.bot.send_message(
                chat_id=zero_dev_grp_id,
                text=message_text,
                parse_mode=ParseMode.HTML
            )
            return
        await check_msg(update.message.date, update, context)

        # await  context.bot.send_message(chat_id=zero_dev_grp_id, text='ok')
    else:
        print(f'other chat :{update.message.text}')


async def create_batch_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    arg_text = " ".join(context.args)
    tele_uid = update.message.from_user.id
    # check if am I sending the command
    if tele_uid != tele_user_me:
        await context.bot.send_message(chat_id=update.message.chat_id, text='poda podaaaa')

    if arg_text == 'clear' and arg_text != '':
        await db_management.dbops('clear_batch', '')
        await  context.bot.send_message(chat_id=update.message.chat_id,
                                        text='all db cleared')
        return
    print(f'args {arg_text} and {tele_uid}')
    if not arg_text:
        await  context.bot.send_message(chat_id=update.message.chat_id,
                                        text='formate will be yyyy-mm-dd')
        return

    await  batch_creates(arg_text, context, update)
    # if tuple found in table  with matching date(id) then not need to add


def map_user(row):
    columns = [
        "tele_id", "user_name", "topic", "repository", "isExtended", "ExtDate",
        "start", "end", "user_fullname", "user_firstname", "batch_id",
        "tech_stack", "deadline_as_date", "team_id"
    ]
    return dict(zip(columns, row))


async def join_grp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.chat.id
    user_name = update.message.chat.username
    user_fullname = update.message.chat.full_name
    user_first_name = update.message.chat.first_name
    status = await db_management.dbops('check_is_user_already_present_and_update_if_yes', [user_id, context])
    status_msg = status[0]
    status_return_user = status[1]
    if status_msg is False:
        print('to add to db ')
        status = await db_management.dbops('add_new_user_to_db', [user_id, user_name, user_fullname, user_first_name])
        if status:
            await context.bot.send_message(chat_id=update.message.chat_id,
                                           text='hooray u joined in our group , go and start your dev journey')
    elif status_msg == 'exist':
        print('found user so not need to add anymore send a already added warning')
        await context.bot.send_message(chat_id=update.message.chat_id, text=f'already u joined , explore our group')
    elif status_msg == 'updated_old':
        user = map_user(status_return_user)
        print('send any message about his record ')
        await context.bot.send_message(chat_id=update.message.chat_id, text=f'already u joined , explore our group')
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"""
        🎉 *Hooray! You're Successfully Registered* 🎉
        
        Hey {user["user_name"]} 👋  
        We didn’t forget you 😉
        
        ━━━━━━━━━━━━━━━━━━━
        📌 *Project Details*
        ━━━━━━━━━━━━━━━━━━━
        📚 *Topic:* {user["topic"]}
        🔗 *Repository:* {user["repository"]}
        
        🛠️ *Tech Stack:* {user["tech_stack"]}
        
        🚀 *Start Date:* {user["start"]}
        ⏳ *Deadline (days):* {user["end"]}
        
        ━━━━━━━━━━━━━━━━━━━
        💪 Stay consistent. Build daily. Win big.
        ━━━━━━━━━━━━━━━━━━━
        """,
            parse_mode="Markdown"
        )


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print('hai')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text_caps = ' '.join(context.args).upper()
    print(text_caps)
    await context.bot.send_message(chat_id=update.message.chat_id, text=text_caps)
    print(f' id: {update.effective_chat.id} user: {update.message.chat} and {update.message.text}')


def pybot():
    if TELEGRAM_BOT_TOKEN_TEST is None:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN_TEST).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("join", join_grp))
    application.add_handler(CommandHandler("grp", create_batch_group))
    grp_msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), grp_msg)
    application.add_handler(grp_msg_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


pybot()
