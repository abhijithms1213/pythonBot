from datetime import datetime

from telegram.constants import ParseMode
import random
import execution
import db_management
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import os
import schedule as schedule_py

import helpers as helpers_py

load_dotenv()
tele_user_me = int(os.getenv("TELEGRAM_USER_ME"))

zero_dev_grp_id = -5287913183

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
    status = await db_management.dbops('check_batch', [date, update, context])
    if status == 'added_new_batch':
        await  context.bot.send_message(chat_id=update.message.chat_id,
                                        text='remember not start a batch on month ends , need 2 day gap')
    if status == 'running':
        await  context.bot.send_message(chat_id=update.message.chat_id,
                                        text='running a batch currently')


async def check_msg(msg_date, update, context):
    date_to_string = str(msg_date)
    date_only = date_to_string[:10]
    # print(f"[INFO] msg date extracted: {date_only}")

    extracted = int(date_only.replace('-', ''))
    extracted = 20260422  # override for testing
    print(f' extracted date: {extracted}')

    ret_status = await db_management.dbops(
        'check_is_msg_under_planning_phase',
        [extracted, update, context]
    )

    status = ret_status[0]
    current_batch = ret_status[1]

    print(f"[DEBUG] status: {status}, batch: {current_batch}")

    # 🔹 CASE 1: No active batch
    if status == 'no_batches_currently':
        print("[INFO] No active batch found")

        dev_details = await db_management.dbops(
            'get_one_dev_details',
            [update.message.from_user.id]
        )

        if not dev_details[0]:
            print("[WARN] Dev not found in DB")
            return

        dev_data = dev_details[1][0]
        print(f"[DEBUG] Dev data: {dev_data}")

        # 🔹 No team
        if not dev_data[5]:
            print("[INFO] Dev not assigned to any team")
            return

        # 🔹 Get team details
        team_details = await db_management.dbops(
            'get_team_details_based_team_id',
            [dev_data[5]]
        )

        if not team_details:
            print("[ERROR] Invalid team reference")
            return

        print(f"[DEBUG] Team details: {team_details}")

        ext_bool = team_details[3]

        # 🔹 Not extended
        if not ext_bool:
            print("[INFO] Team is not extended → ignore")
            return

        ext_date = team_details[4]
        today = int(datetime.now().strftime("%Y%m%d"))

        print(f"[DEBUG] ext_date: {ext_date}, today: {today}")

        # 🔹 Deadline passed
        if ext_date < today:
            print("[WARN] Deadline already over")
            return

        # 🔹 Valid extended user → update log
        print("[INFO] Updating extended dev log...")

        return_value = helpers_py.update_for_extended_devs(
            msg_date,
            update,
            dev_data[5],
            dev_data[1]
        )

        if return_value:
            print("[SUCCESS] Update recorded successfully")
        else:
            print("[ERROR] Failed to update extended dev log")

        return

    if status == 'during_planning_phase':
        print("[INFO] During planning phase")

        extended_handled = False  # 🔥 FLAG

        dev_details = await db_management.dbops(
            'get_one_dev_details',
            [update.message.from_user.id]
        )

        if dev_details[0]:
            dev_data = dev_details[1][0]

            if dev_data[5]:  # has team
                team_details = await db_management.dbops(
                    'get_team_details_based_team_id',
                    [dev_data[5]]
                )

                if team_details:
                    ext_bool = team_details[3]

                    if ext_bool:
                        ext_date = team_details[4]
                        today = int(datetime.now().strftime("%Y%m%d"))

                        print(f"[DEBUG] ext_date: {ext_date}, today: {today}")

                        if ext_date >= today:
                            print("[INFO] Updating extended dev log...")

                            result = helpers_py.update_for_extended_devs(
                                msg_date,
                                update,
                                dev_data[5],
                                dev_data[1]
                            )

                            if result:
                                print("[SUCCESS] Extended update done")
                                extended_handled = True
                            else:
                                print("[ERROR] Extended update failed")

                        else:
                            print("[WARN] Extended deadline over")

        # 🔥 IMPORTANT: Continue normal flow if NOT handled
        if not extended_handled:
            print("[INFO] Proceeding to normal planning flow")

            #  get the return valid / invalid status then send message for each
            is_success_status = await execution.msg_process(
                msg_date, update, context, current_batch
            )
            if isinstance(is_success_status, list):
                if is_success_status[0] == 'error_user_exist':
                    user = is_success_status[1]

                    if isinstance(user, str) and user.startswith("@"):
                        user_tag = user
                    else:
                        user_tag = f'<a href="tg://user?id={user}">dev</a>'

                    message = f"""
                An imposter found, {user_tag} is already in another group,
                so ignoring.
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
                    all_users: list = list(set(new_join + no_id_users))

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

                    print(f'all users are {all_users}and {no_id_users}')
                    if len(all_users) == 1:
                        # 🧍 Solo — address the user directly as "you"
                        if no_id_users:
                            print('solo no id warning')
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
                            print('solo else warning')
                            warning_text = ""  # no missing IDs, no warning needed

                    else:
                        # 👥 Team — list missing members
                        if len(no_id_users) >= 1:
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
                            print('team else warning')
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
    
                  📂 <b>Your Repo:</b> <a href="{github_repo}">Open Repo 🔗</a>
    
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
                        parse_mode="HTML",
                        disable_web_page_preview=True
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
        print("[INFO] During project phase")
        extended_handled = False  # 🔥 FLAG

        dev_details = await db_management.dbops(
            'get_one_dev_details',
            [update.message.from_user.id]
        )

        if dev_details[0]:
            dev_data = dev_details[1][0]

            if dev_data[5]:  # has team
                team_details = await db_management.dbops(
                    'get_team_details_based_team_id',
                    [dev_data[5]]
                )

                if team_details:
                    ext_bool = team_details[3]

                    if ext_bool:
                        ext_date = team_details[4]
                        today = int(datetime.now().strftime("%Y%m%d"))

                        print(f"[DEBUG] ext_date: {ext_date}, today: {today}")

                        if ext_date >= today:
                            print("[INFO] Updating extended dev log...")

                            result = helpers_py.update_for_extended_devs(
                                msg_date,
                                update,
                                dev_data[5],
                                dev_data[1]
                            )

                            if result:
                                print("[SUCCESS] Extended update done")
                                extended_handled = True
                            else:
                                print("[ERROR] Extended update failed")

                        else:
                            print("[WARN] Extended deadline over")

        # 🔥 IMPORTANT: Continue normal flow if NOT handled
        if not extended_handled:
            dev_details = await db_management.dbops(
                'get_one_dev_details',
                [update.message.from_user.id]
            )
            if dev_details[0]:
                if isinstance(dev_details[1][0][5], int) and dev_details[1][0][5]:
                    return_value = await  execution.project_phase(extracted, update, context, current_batch)
                    if isinstance(return_value, bool) and return_value == True:
                        print('true returned')
                    else:
                        print('false returned')
                else:
                    print(f'team is :{dev_details[1][0][5]}')
                    print('user found but team id is null , not registered in project phase')
            else:
                print('not found this user in db')
                return


async def grp_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(
        f'args:{update.message.text} user: name: {update.message.from_user.username} id:{update.message.from_user.id}\nxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
    current_id = update.message.chat.id
    if zero_dev_grp_id == current_id:
        chat_usr = await context.bot.get_chat(chat_id=update.message.from_user.id)
        is_user_updated = await db_management.dbops('update_dev_detail_if_found',
                                                    [update.message.from_user.id, chat_usr])
        user_status = is_user_updated[0]
        if user_status:
            print(f'found user didnt updated @ , now updated {is_user_updated[1]}')

        if update.message.text == 'clear_all':
            await schedule_py.lets_clean_all(context, update)
            return
        if update.message.text == 'attention_msg':
            await schedule_py.attention_msgs(context)
            return

        if update.message.text == 'daily_update':
            await schedule_py.daily_update(context)
            return
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


# async def common_str(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     date = str(update.message.date)
#     date = date[:10]
#     sanitized_date = int(f'{date}'.replace('-', ''))
#     print(f'date : {date} sani : {sanitized_date}')
#     status = await db_management.dbops('check_is_msg_under_planning_phase', sanitized_date)
#
#     if status[0] == 'no_batches_currently':
#         print('no batch')
#     elif status[0] == 'during_planning_phase':
#         print('planning')
#     elif status[0] == 'during_project_phase':
#         print('project')
#     elif status[0] == 'after_deadline':
#         print('after'

async def finished_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    date = str(update.message.date)
    date = date[:10]
    sanitized_date = int(f'{date}'.replace('-', ''))
    # sanitized_date = 20260416  # override for testing
    # print(f'date : {date} sani : {sanitized_date}')
    status = await db_management.dbops('check_is_msg_under_planning_phase', [sanitized_date, update, context])

    if status[0] == 'no_batches_currently':
        print('no batch')
        dev_details = await db_management.dbops('get_one_dev_details',
                                                [update.message.from_user.id])
        if not dev_details[0]:
            print('not work')
        else:
            dev_data = dev_details[1][0]
            if not dev_data[5]:  # get team id
                print('not work')
            else:
                team_details = await db_management.dbops('get_team_details_based_team_id',
                                                         [dev_data[5]])
                if not team_details:
                    print('not work')
                else:
                    ext_bool = team_details[3]
                    if not ext_bool:  # means dev not from prev batches user, means: old user ok with new batch ,
                        print('not work')
                    else:
                        user, is_finished, team_id, streak, total_points, user_name = await db_management.dbops(
                            'check_is_user_already_exist_in_user_db',
                            update.message.from_user.id)
                        if user:
                            if not is_finished:
                                print(f'found user {user} fini_status: {is_finished} team:{team_id}')
                                print('not finished i found')
                                status = await db_management.dbops('updating_user_project_finish_and_clean_up',
                                                                   [update.message.from_user.id, team_id, streak,
                                                                    total_points, user_name])
                                if status:
                                    print("updated your status and also team isFinished true")
                                else:
                                    print('not updated teams isFinish but user update done')
                            else:
                                print('already u finished before')
                        else:
                            print('not found in db about user')

    elif status[0] == 'during_planning_phase':
        print('planning')
        dev_details = await db_management.dbops('get_one_dev_details',
                                                [update.message.from_user.id])
        if not dev_details[0]:
            print('not work')
        else:
            dev_data = dev_details[1][0]
            if not dev_data[5]:  # get team id
                print('not work')
            else:
                team_details = await db_management.dbops('get_team_details_based_team_id',
                                                         [dev_data[5]])
                if not team_details:
                    print('not work')
                else:
                    ext_bool = team_details[3]
                    if not ext_bool:  # means dev not from prev batches user, means: old user ok with new batch ,
                        print('not work')
                    else:
                        user, is_finished, team_id, streak, total_points, user_name = await db_management.dbops(
                            'check_is_user_already_exist_in_user_db',
                            update.message.from_user.id)
                        if user:
                            if not is_finished:
                                print(f'found user {user} fini_status: {is_finished} team:{team_id}')
                                print('not finished i found')
                                status = await db_management.dbops('updating_user_project_finish_and_clean_up',
                                                                   [update.message.from_user.id, team_id, streak,
                                                                    total_points, user_name])
                                if status:
                                    print("updated your status and also team isFinished true")
                                else:
                                    print('not updated teams isFinish but user update done')
                            else:
                                print('already u finished before')
                        else:
                            print('not found in db about user')

    elif status[0] == 'during_project_phase':
        print('project')
        user, is_finished, team_id, streak, total_points, user_name = await db_management.dbops(
            'check_is_user_already_exist_in_user_db',
            update.message.from_user.id)
        if user:
            if not is_finished:
                print(f'found user {user} fini_status: {is_finished} team:{team_id}')
                print('not finished so we are going to update')
                status = await db_management.dbops('updating_user_project_finish_and_clean_up',
                                                   [update.message.from_user.id, team_id, streak, total_points,
                                                    user_name])
                if status:
                    print("updated your status and also team isFinished true")
                else:
                    print('not updated teams but user update done')
            else:
                print('already u finished before')
        else:
            print('not found in db about user')

    else:
        print('after')


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
    application.add_handler(CommandHandler("finished_project", finished_project))
    grp_msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), grp_msg)
    application.add_handler(grp_msg_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


pybot()
