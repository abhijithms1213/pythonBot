from telegram.constants import ParseMode
import random
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

# old is below
# +------------+--------------+------------------------+-----------------------------+---------------+----------------+----------+------------+---------+
# | tele_id    | user_name    | topic                  | repository                  | user_fullname | user_firstname | batch_id | tech_stack | team_id |
# +------------+--------------+------------------------+-----------------------------+---------------+----------------+----------+------------+---------+
# | 1054613006 | @Jithuzz2255 | dbms management system | https://github.com/abhijith | Ezio          | Ezio           | 20260329 | flutter ap | 91448   |
# +------------+--------------+------------------------+-----------------------------+---------------+----------------+----------+------------+---------+

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
        is_success_status = await  execution.msg_process(msg_date, update, context, current_batch)
        if isinstance(is_success_status, list):
            if is_success_status[0] == 'error_user_exist':
                print(f'exist member {is_success_status[1]} is string {type(is_success_status[1])}')
                message = f"""
                an imposter found, <a href="tg://user?id={is_success_status[1]}">unknown_user</a>'s already exist in another grp,\nSo ignoring
                """

                await update.effective_message.reply_text(
                    message,
                    parse_mode="HTML"
                )
                return
            else:
                bot_link = f"https://t.me/{context.bot.username}?start=join"
                new_join = is_success_status[1]
                no_id_users: list = is_success_status[2]
                all_users: list = new_join + no_id_users

                topic = is_success_status[3]
                tech = is_success_status[4]
                github_repo = is_success_status[5]
                deadline = is_success_status[6]
                deadline_as_date = is_success_status[7]
                team_name = is_success_status[8]

                # 🔥 optional fun lines
                team_lines = [
                    "I gave your squad a name 😎 hope you like it!",
                    "Your crew just got an identity 🔥",
                    "Team vibes unlocked 🚀",
                ]

                solo_lines = [
                    "Looks like you're going solo 😎",
                    "Silent assassin mode activated 🥷",
                ]

                if len(all_users) == 1:
                    # 🧍 Solo — address the user directly as "you"
                    if no_id_users:
                        warning_text = f"""
                ━━━━━━━━━━━━━━━━━━━

                ⚠️ <b>Heads up!</b>

                You haven't started me yet 👀
                🚨 I can't track or notify you properly.

                💡 <b>Fix (very easy):</b>
                    => <a href="{bot_link}">Tap here to open me 🤖</a>
                    => Send <code>/start</code> or <code>/join</code>
                ⚡ Do it now… or I'll pretend you don't exist 😶
                """
                    else:
                        warning_text = ""  # no missing IDs, no warning needed

                else:
                    # 👥 Team — list missing members
                    if len(no_id_users) > 1:
                        warning_text = f"""
                ━━━━━━━━━━━━━━━━━━━

                ⚠️ <b>Heads up!</b>

                These guys didn't join me yet 👀
                👉 {no_id_users}

                🚨 I can't track or notify them properly.

                💡 <b>Fix (very easy):</b>
                    => <a href="{bot_link}">Tap here to open me 🤖</a>
                    => Send <code>/start</code> or <code>/join</code>
                ⚡ Do it now… or I'll pretend they don't exist 😶
                """
                    else:
                        warning_text = ""

                # ─── Now build the main message ───────────────────────────────────────────

                if len(all_users) == 1:
                    intro_line = random.choice(solo_lines)
                    message = f"""
                🚀 <b>Project Locked In!</b>

                😎 {intro_line}
                🏷️ I gave you a title: <b>{team_name}</b>

                🧠 <b>What you're building:</b> {topic}
                ⚙️ <b>Using:</b> {tech}

                📂 <b>Your Repo:</b>
                {github_repo}

                ⏳ <b>Deadline:</b> {deadline} days
                📅 <b>Finish by:</b> {deadline_as_date}

                ━━━━━━━━━━━━━━━━━━━

                🔥 It's all on you now... make it legendary ⚡
                """

                else:
                    intro_line = random.choice(team_lines)
                    message = f"""
                🚀 <b>Project Locked In!</b>

                😏 {intro_line}
                🏷️ Your team name is: <b>{team_name}</b>

                🧠 <b>Mission:</b> {topic}
                ⚙️ <b>Stack:</b> {tech}

                📂 <b>Repo:</b>
                {github_repo}

                ⏳ <b>Deadline:</b> {deadline} days
                📅 <b>Finish by:</b> {deadline_as_date}

                💪 Don't disappoint the name <b>{team_name}</b> 😄
                """

                full_msg = message + warning_text

                await update.effective_message.reply_text(
                    full_msg,
                    parse_mode="HTML"
                )
                return

                # means valid

        if isinstance(is_success_status, int):
            print('normal msg')
            return
        if isinstance(is_success_status, str):
            error_map = {
                "error_no_deadline": "⏳ Where is deadline?\nUse <code>/deadline 14</code>",
                "error_invalid_deadline": "🚫 Invalid deadline\nAllowed: 14, 17, 21",
                "error_no_topic": "🧠 Missing topic\nUse <code>/topic your idea</code>",
                "error_no_tech": "⚙️ Missing tech stack\nUse <code>/tech flutter, python</code>",
                "error_no_github": "📂 GitHub repo missing\nAdd a valid link",
            }
            msg = error_map.get(is_success_status, "❌ Something went wrong")

            await update.effective_message.reply_text(
                msg,
                parse_mode="HTML"
            )
            return


    elif status == 'during_project_phase':
        return_value = await  execution.project_phase(msg_date, update, context, current_batch)
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
        return

        # await  context.bot.send_message(chat_id=zero_dev_grp_id, text='ok')
    else:
        print(f'other chat :{update.message.text}')
        return


async def create_batch_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    arg_text = " ".join(context.args)
    tele_uid = update.message.from_user.id
    # check if am I sending the command
    if tele_uid != tele_user_me:
        await context.bot.send_message(chat_id=update.message.chat_id, text='poda podaaaa')
        return

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


def map_team(row):
    columns = [
        "batch_id", "team_id", "devs_id", "isExtended",
        "ExtDate", "start", "end", "deadline_as_date",
        "streak", "topic", "repository", "tech_stack", "team_name"
    ]
    return dict(zip(columns, row))


def map_user(row):
    columns = [
        "tele_id",
        "user_name",
        "user_fullname",
        "user_firstname"
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
        user = map_team(status_return_user)
        usr_first_name_ret = status[2]
        print('send any message about his record ')
        await context.bot.send_message(chat_id=update.message.chat_id, text=f'already u joined , explore our group')
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"""
        🎉 *Hooray! You're Successfully Registered* 🎉
        
        Hey {usr_first_name_ret} 👋  
        We didn’t forget you 😉
        
        ━━━━━━━━━━━━━━━━━━━
        📌 *Project Details*
        ━━━━━━━━━━━━━━━━━━━
        🎯 *Team:* {user["team_name"]}
        
        
        📚 *Topic:* {user["topic"]}
        🔗 *Repository:* {user["repository"]}
        
        🛠️ *Tech Stack:* {user["tech_stack"]}
        
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
