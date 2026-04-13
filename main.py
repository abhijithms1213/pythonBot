from datetime import datetime
import production_bool
# if update.message.text == 'weekly_report':
#     await schedule_py.weekly_report(context)
# if update.message.text == 'clear_all':
#     await schedule_py.lets_clean_all(context, update)
# if update.message.text == 'attention_msg':
#     await schedule_py.attention_msgs(context)
# if update.message.text == 'daily_update':
#     await schedule_py.daily_update(context)
# if update.message.text == 'notify_devs':
#     await schedule_py.notify_devs_to_update(context)

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

is_production = production_bool.is_production()

# zero_dev_grp_id = -5287913183
commitio_grp_id = -5287913183
commitio_test_grp_id = -5251179553

grp_id: int
if is_production:
    grp_id = commitio_grp_id
else:
    grp_id = commitio_test_grp_id

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
TELEGRAM_BOT_TOKEN_COMMITIO = os.getenv("TELEGRAM_BOT_TOKEN_COMMITIO")

district = {
    "brand": "Ford",
    "model": "Mustang",
    "year": 1964,
    "type": str
}

print(district)


async def format_msgs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args

    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ Usage:\n"
            "<code>/format_msgs html your_text</code>\n"
            "<code>/format_msgs markdown your_text</code>",
            parse_mode="HTML"
        )
        return

    mode = args[0].lower()
    content = " ".join(args[1:])

    try:
        if mode == "html":
            await update.message.reply_text(
                content,
                parse_mode="HTML",
                disable_web_page_preview=True
            )

        elif mode == "markdown":
            await update.message.reply_text(
                content,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )

        elif mode == "md2":
            await update.message.reply_text(
                content,
                parse_mode="MarkdownV2",
                disable_web_page_preview=True
            )

        else:
            await update.message.reply_text(
                "❌ Invalid mode.\nUse: <code>html</code>, <code>markdown</code>, or <code>md2</code>",
                parse_mode="HTML"
            )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Formatting error:\n<code>{str(e)}</code>",
            parse_mode="HTML"
        )


async def batch_creates(date, context, update):
    status = await db_management.dbops('check_batch', [date, update, context])
    if status == 'added_new_batch':
        await  context.bot.send_message(chat_id=update.message.chat_id,
                                        text='remember not start a batch on month ends , need 2 day gap')
    if status == 'running':
        await  context.bot.send_message(chat_id=update.message.chat_id,
                                        text='running a batch currently')


async def team_decl_call(is_success_status, update, context):
    # 🔹 If not list → handle string errors here
    if isinstance(is_success_status, str):
        error_map = {
            "error_no_deadline": "⏳ <b>Missing deadline</b>\nUse <code>/deadline 14 or 17 or 26</code>",
            "error_invalid_deadline": "🚫 <b>Invalid deadline</b>\nAllowed: 14, 17, 26",
            "error_no_topic": "🧠 <b>Missing topic</b>\nUse <code>/topic your idea</code>",
            "error_no_tech": "⚙️ <b>Missing tech stack</b>\nUse <code>/tech flutter, python</code>",
            "error_no_github": (
                "📂 <b>GitHub repo missing</b>\n"
                "Add a valid link\n\n"
                "💡 <b>New to Git?</b>\n"
                "<i>If you're a Starter, you can skip this by adding:</i>\n"
                "<code>starter-dev: true</code>\n"
            ),
            "invalid_something_went_wrong": "❌ Something went wrong while creating the team. Try again."
        }

        msg = error_map.get(is_success_status, "❌ Unexpected error occurred")

        await update.effective_message.reply_text(
            msg,
            parse_mode="HTML"
        )
        return

    # 🔹 Ignore non-list non-string
    if not isinstance(is_success_status, list):
        return

    # ───────────────── ERROR CASE ───────────────── #
    if is_success_status[0] == 'error_user_exist':
        user = is_success_status[1]

        user_tag = (
            user if isinstance(user, str) and user.startswith("@")
            else f'<a href="tg://user?id={user}">dev</a>'
        )

        await update.effective_message.reply_text(
            f"⚠️ <b>Imposter detected!</b>\n\n{user_tag} is already in another group.",
            parse_mode="HTML"
        )
        return

    # 🔹 If it's not valid → safety fallback
    if is_success_status[0] != 'valid':
        await update.effective_message.reply_text(
            "❌ Something went wrong. Please try again.",
            parse_mode="HTML"
        )
        return

    # ───────────────── DATA EXTRACTION ───────────────── #
    bot_link = f"https://t.me/{context.bot.username}?start=join"

    new_join = is_success_status[1]
    no_id_users = is_success_status[2]
    all_users = list(set(new_join + no_id_users))

    topic = is_success_status[3]
    tech = is_success_status[4]
    github_repo = is_success_status[5]
    deadline = is_success_status[6]
    deadline_as_date = is_success_status[7]
    team_name = is_success_status[8]

    # ───────────────── RANDOM LINES ───────────────── #
    team_lines = [
        "Your crew just got an identity 🔥",
        "Team vibes unlocked 🚀",
        "Let’s build something amazing together 💪"
    ]

    solo_lines = [
        "Looks like you're going solo 😎",
        "Silent assassin mode activated 🥷"
    ]

    # ───────────────── WARNING SECTION ───────────────── #
    warning_text = ""

    if len(all_users) == 1:
        if no_id_users:
            warning_text = (
                "⚠️ <b>Heads up!</b>\n\n"
                "You haven't started me yet 👀\n"
                "🚨 I can't track you properly.\n\n"
                "💡 <b>Fix:</b>\n"
                "👉 simply say <b>hi</b> / <b>hello</b> in this group\n"
                f"👉 Or <a href=\"{bot_link}\">Open bot</a> and send <code>/start</code>\n"
            )

    else:
        if no_id_users:
            missing = "\n".join(f"• {u}" for u in no_id_users)

            warning_text = (
                "⚠️ <b>Heads up!</b>\n\n"
                "These members didn't join yet 👀\n"
                f"{missing}\n\n"
                "🚨 I can't track them properly.\n\n"
                "💡 <b>Fix:</b>\n"
                "👉 simply say <b>hi</b> / <b>hello</b> in this group\n"
                f"👉 Or <a href=\"{bot_link}\">Open bot</a> and send <code>/start</code>\n"
            )

    # ───────────────── MAIN MESSAGE ───────────────── #

    if len(all_users) == 1:
        intro = random.choice(solo_lines)

        message = (
            "🚀 <b>Project Locked In!</b>\n\n"

            f"😎 {intro}\n"
            f"🏷️ <b>{team_name}</b>\n\n"

            f"🧠 <b>What you're building:</b> {topic}\n\n"
            f"⚙️ <b>Tech Stack:</b> {tech}\n\n"

            f"📂 <b>Repository:</b> "
            f"<a href=\"{github_repo}\">Open Repo 🔗</a>\n\n"

            f"⏳ <b>Deadline:</b> {deadline} days\n"
            f"📅 <b>Finish by:</b> {deadline_as_date}"
        )

    else:
        intro = random.choice(team_lines)

        message = (
            "🚀 <b>Project Locked In!</b>\n\n"

            f"😎 {intro}\n"
            f"🏷️ <b>{team_name}</b>\n\n"

            f"🧠 <b>What you're building:</b> {topic}\n\n"
            f"⚙️ <b>Tech Stack:</b> {tech}\n\n"

            f"📂 <b>Repository:</b> "
            f"<a href=\"{github_repo}\">Open Repo 🔗</a>\n\n"

            f"⏳ <b>Deadline:</b> {deadline} days\n"
            f"📅 <b>Finish by:</b> {deadline_as_date}"

        )

    # ───────────────── FINAL OUTPUT ───────────────── #

    full_msg = message + ("\n\n" + warning_text if warning_text else "")

    await update.effective_message.reply_text(
        full_msg,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


# HARDCODED
# sanitized_date = 20260520


async def check_msg(msg_date, update, context):
    date_to_string = str(msg_date)
    date_only = date_to_string[:10]
    print(f"[INFO] msg date extracted: {date_only}")

    extracted = int(date_only.replace('-', ''))

    # HARDCODED
    # extracted = sanitized_date  # override for testing
    print(f'\nextracted date: {extracted}\n\n')

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

        ext_bool = team_details[3]

        # 🔹 Not extended
        if not ext_bool:
            print("[INFO] Team is not extended → ignore")
            return

        ext_date = team_details[4]

        print(f"[DEBUG] ext_date: {ext_date}, msg_date is: {extracted}")

        # 🔹 Deadline passed
        if extracted > ext_date:
            print("[WARN] Deadline already over")
            return

        # 🔹 Valid extended user → update log
        print("[INFO] Updating extended dev log...")

        return_value = await helpers_py.update_for_extended_devs(
            extracted,
            update,
            dev_data[5],
            dev_data[1], ext_bool, context
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

                    print(f'team detail:{team_details} and batch is {current_batch}')
                    team_batch_id = team_details[0]
                    current_batch_id = current_batch[0]
                    if team_batch_id != current_batch_id:  # if this dev is from prev batch then not equal
                        ext_bool = team_details[3]

                        if ext_bool:
                            ext_date = team_details[4]
                            print(f"[DEBUG] ext_date: {ext_date}, msg_date is: {extracted}")
                            # 🔹 Deadline passed
                            if extracted <= ext_date:
                                print("[INFO] Updating extended dev log...")
                                result = await helpers_py.update_for_extended_devs(
                                    extracted,
                                    update,
                                    dev_data[5],
                                    dev_data[1], ext_bool, context
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
            await team_decl_call(is_success_status, update, context)


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
                    team_batch_id = team_details[0]
                    current_batch_id = current_batch[0]
                    if team_batch_id != current_batch_id:  # if this dev is from prev batch then not equal
                        ext_bool = team_details[3]
                        if ext_bool:
                            ext_date = team_details[4]
                            print(f"[DEBUG] ext_date: {ext_date}, msg_date is: {extracted}")
                            # 🔹 Deadline passed
                            if extracted <= ext_date:
                                print("[INFO] Updating extended dev log...")

                                result = await helpers_py.update_for_extended_devs(
                                    extracted,
                                    update,
                                    dev_data[5],
                                    dev_data[1], ext_bool, context
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
        else:
            print('update done dev from not this batch')

    elif status == 'clean_up_day':
        print('today is clean up day')
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
                    team_batch_id = team_details[0]
                    current_batch_id = current_batch[0]
                    if team_batch_id != current_batch_id or team_batch_id == current_batch_id:
                        ext_bool = team_details[3]
                        if ext_bool:
                            ext_date = team_details[4]
                            print(f"[DEBUG] ext_date: {ext_date}, msg_date is: {extracted}")
                            # 🔹 Deadline passed
                            if extracted <= ext_date:
                                print("[INFO] Updating extended dev log...")

                                result = await helpers_py.update_for_extended_devs(
                                    extracted,
                                    update,
                                    dev_data[5],
                                    dev_data[1], ext_bool, context
                                )

                                if result:
                                    print("[SUCCESS] Extended update done")
                                else:
                                    print("[ERROR] Extended update failed")

                            else:
                                print("[WARN] Extended deadline over")


async def grp_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_id = update.message.chat.id

    if grp_id == current_id:
        print(
            f'args:{update.message.text} user: name: {update.message.from_user.username} id:{update.message.from_user.id}\nxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        user = update.message.from_user
        is_user_updated = await db_management.dbops('update_dev_detail_if_found',
                                                    [update.message.from_user.id, user])
        user_status = is_user_updated[0]
        if user_status:
            print(f'found user didnt updated @ , now updated {is_user_updated[1]}')

        if update.message.text == 'weekly_report':
            tele_uid = update.message.from_user.id
            # check if am I sending the command
            if tele_uid != tele_user_me:
                return
            print('weekly report called')
            await schedule_py.weekly_report(context)
            return
        if update.message.text == 'clear_all':

            tele_uid = update.message.from_user.id
            # check if am I sending the command
            if tele_uid != tele_user_me:
                return
            await schedule_py.lets_clean_all(context, update)
            return
        if update.message.text == 'attention_msg':
            tele_uid = update.message.from_user.id
            # check if am I sending the command
            if tele_uid != tele_user_me:
                return
            await schedule_py.attention_msgs(context)
            return

        if update.message.text == 'daily_update':
            tele_uid = update.message.from_user.id
            # check if am I sending the command
            if tele_uid != tele_user_me:
                return
            await schedule_py.daily_update(context)
            return

        if update.message.text == 'notify_devs':
            tele_uid = update.message.from_user.id
            # check if am I sending the command
            if tele_uid != tele_user_me:
                return
            await schedule_py.notify_devs_to_update(context)
            return
        if update.message.text == 'mention':
            tele_uid = update.message.from_user.id
            # check if am I sending the command
            if tele_uid != tele_user_me:
                return
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
                chat_id=grp_id,
                text=message_text,
                parse_mode=ParseMode.HTML
            )
            return
        await check_msg(update.message.date, update, context)
        return

        # await  context.bot.send_message(chat_id=zero_dev_grp_id, text='ok')
    else:

        current_id = update.message.chat.id
        print(f'other chat :{update.message.text} and {current_id}')
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
    # ✅ Get actual user (NOT chat)
    user = update.message.from_user

    user_id = user.id
    user_name = user.username
    user_fullname = user.full_name
    user_first_name = user.first_name

    # DB check
    status = await db_management.dbops(
        'check_is_user_already_present_and_update_if_yes',
        [user_id, context]
    )

    status_msg = status[0]
    status_return_user = status[1]

    # ✅ Case 1: New user
    if status_msg is False:
        print('Adding new user to DB')

        add_status = await db_management.dbops(
            'add_new_user_to_db',
            [user_id, user_name, user_fullname, user_first_name]
        )

        if add_status:
            await update.message.reply_text(
                '🎉 Hooray! You joined 🚀\nStart your dev journey now!'
            )

    # ✅ Case 2: Already exists
    elif status_msg == 'exist':
        print('User already exists')

        await update.message.reply_text(
            '⚠️ You already joined. Explore the group and keep building 💪'
        )

    # ✅ Case 3: Updated old user (username matched, ID updated)
    elif status_msg == 'updated':
        data = status_return_user

        team = map_team(data["team"])

        await update.message.reply_text(
            f"""
    🎉 *Welcome Back!* 🎉

    Hey {data["first_name"]} 👋  

    ━━━━━━━━━━━━━━━━━━━
    📌 *Project Details*
    ━━━━━━━━━━━━━━━━━━━
    🎯 *Team:* {team["team_name"]}

    📚 *Topic:* {team["topic"]}
    🔗 *Repository:* {team["repository"]}

    🛠️ *Tech Stack:* {team["tech_stack"]}

    ━━━━━━━━━━━━━━━━━━━
    💪 Stay consistent. Build daily. Win big.
    ━━━━━━━━━━━━━━━━━━━
            """,
            parse_mode="Markdown"
        )


async def finished_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_id = update.message.chat.id

    if not grp_id == current_id:
        return

    args = context.args

    # ❌ If no args OR not "true"
    if not args or args[0].lower() != "true":
        await update.message.reply_text(
            "⚠️ <b>Confirmation required</b>\n\n"
            "If you accidentally tapped, I ignored it 👍\n\n"
            "If you really finished your project:\n"
            "<code>/finished_project true</code>",
            parse_mode="HTML"
        )
        return
    date = str(update.message.date)
    date = date[:10]
    sanitized_date = int(f'{date}'.replace('-', ''))
    # sanitized_date = 20260425  # override for testing

    print(f'date : {date} sani : {sanitized_date}')
    print(f'msg date in finished_section: {sanitized_date}')
    status = await db_management.dbops('check_is_msg_under_planning_phase', [sanitized_date, update, context])

    if status[0] == 'no_batches_currently':
        print('no batch')
        dev_details = await db_management.dbops('get_one_dev_details',
                                                [update.message.from_user.id])
        if not dev_details[0]:
            print("❌ Dev not found in database")

        else:
            dev_data = dev_details[1][0]

            if not dev_data[5]:  # team_id
                print(f"⚠️ Dev {dev_data[0]} is not assigned to any team")

            else:
                team_details = await db_management.dbops(
                    'get_team_details_based_team_id',
                    [dev_data[5]]
                )

                if not team_details:
                    print(f"❌ No team found for team_id: {dev_data[5]}")

                else:
                    ext_bool = team_details[3]

                    if not ext_bool:
                        print(f"ℹ️ Team {dev_data[5]} is not extended (normal batch user)")

                    else:
                        print(f"✅ Extended user detected for team {dev_data[5]}")
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
                                    github_repo = team_details[10]
                                    await update.message.reply_text(
                                        f"🎉 <b>Congratulations!</b>\n\n"
                                        f"✅ Project marked as completed\n"
                                        f"⭐ Total Points: <b>{total_points}</b>\n\n"
                                        f"🔗 <b>Project Repository:</b>\n"
                                        f"{github_repo}\n\n"
                                        f"💼 <b>Next Step:</b>\n"
                                        f"Share your project on <b>LinkedIn</b> and showcase your work 🚀\n\n"
                                        f"👀 <b>Team:</b> Don’t forget to check out this project and support! 🔥\n\n"
                                        f"👏 Great work! Keep building!",
                                        parse_mode="HTML",
                                        disable_web_page_preview=True
                                    )
                                    print("updated your status and also team isFinished true")
                                else:
                                    print('not updated teams isFinish but user update done')
                            else:
                                print('already u finished before')
                        else:
                            print('not found in db about user')

    elif status[0] == 'during_planning_phase':
        batch_details = status[1]
        print('planning')
        print(f'batch from during planning phase: {batch_details[0]} , ')
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
                    team_batch_id = team_details[0]
                    current_batch_id = batch_details[0]
                    print(
                        f'worked batch miss match found team batch id: {team_batch_id} and current batch:{current_batch_id}')
                    if team_batch_id != current_batch_id:
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
                                        github_repo = team_details[10]
                                        await update.message.reply_text(
                                            f"🎉 <b>Congratulations!</b>\n\n"
                                            f"✅ Project marked as completed\n"
                                            f"⭐ Total Points: <b>{total_points}</b>\n\n"
                                            f"🔗 <b>Project Repository:</b>\n"
                                            f"{github_repo}\n\n"
                                            f"💼 <b>Next Step:</b>\n"
                                            f"Share your project on <b>LinkedIn</b> and showcase your work 🚀\n\n"
                                            f"👀 <b>Team:</b> Don’t forget to check out this project and support! 🔥\n\n"
                                            f"👏 Great work! Keep building!",
                                            parse_mode="HTML",
                                            disable_web_page_preview=True
                                        )
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
                #
                # team_details = await db_management.dbops('get_team_details_based_team_id',
                #                                          [team_id])
                # team_deadline = team_details[7]
                # if sanitized_date <= team_deadline:
                #     print(f'found user {user} fini_status: {is_finished} team:{team_id}')
                #     print('not finished so we are going to update')
                #     status = await db_management.dbops('updating_user_project_finish_and_clean_up',
                #                                        [update.message.from_user.id, team_id, streak, total_points,
                #                                         user_name])
                #     if status:
                #         print("updated your status and also team isFinished true")
                #     else:
                #         print('not updated teams but user update done')
                # else:
                #     print('u trying to finish after deadline , we ignoring, in clean up time we consider as finished')
                #
                print(f'found user {user} fini_status: {is_finished} team:{team_id}')
                print('not finished so we are going to update')
                team_details = await db_management.dbops('get_team_details_based_team_id',
                                                         [team_id])
                if team_details:
                    status = await db_management.dbops('updating_user_project_finish_and_clean_up',
                                                       [update.message.from_user.id, team_id, streak, total_points,
                                                        user_name])
                    if status:
                        github_repo = team_details[10]
                        await update.message.reply_text(
                            f"🎉 <b>Congratulations!</b>\n\n"
                            f"✅ Project marked as completed\n"
                            f"⭐ Total Points: <b>{total_points}</b>\n\n"
                            f"🔗 <b>Project Repository:</b>\n"
                            f"{github_repo}\n\n"
                            f"💼 <b>Next Step:</b>\n"
                            f"Share your project on <b>LinkedIn</b> and showcase your work 🚀\n\n"
                            f"👀 <b>Team:</b> Don’t forget to check out this project and support! 🔥\n\n"
                            f"👏 Great work! Keep building!",
                            parse_mode="HTML",
                            disable_web_page_preview=True
                        )
                        print("updated your status and also team isFinished true")
                    else:
                        print('not updated teams but user update done')
            else:
                print('already u finished before')
        else:
            print('not found in db about user')

    elif status[0] == 'clean_up_day':
        print('if u from current batch then ,  cannot finish a project within clean up day')
        batch_details = status[1]
        print(f'batch from clean_up day : {batch_details[0]} , ')
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
                    team_batch_id = team_details[0]
                    current_batch_id = batch_details[0]
                    print(
                        f'team batch id: {team_batch_id} and current batch:{current_batch_id} for compare')
                    if team_batch_id != current_batch_id:
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
    else:
        print('avoid this run , in clean up day ni8 11:50 do call method clean up, b4 ending this clean up day')


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    command = update.message.text.split()[0].lower()

    # ───────────────── MAIN ───────────────── #
    if command == "/help":
        text = (
            "🚀 <b>Commitio Help Center</b>\n\n"

            "Choose a section 👇\n\n"

            "📘 <b>/help_basic</b>\n"
            "→ Quick start guide\n\n"

            "📖 <b>/full_guidance</b>\n"
            "→ Complete system walkthrough\n\n"

            "⚙️ <b>/help_commands</b>\n"
            "→ All commands list\n\n"

            "🧠 <b>/help_advanced</b>\n"
            "→ Rules, points & system\n\n"

            "💡 Tip:\n"
            "Start with <b>/help_basic</b>, then explore <b>/full_guidance</b>"
        )

    # ───────────────── BASIC ───────────────── #
    elif command == "/help_basic":
        text = (
            "📘 <b>Quick Start Guide</b>\n\n"

            "🧠 <b>Create Team (During Planning Phase)</b>\n\n"
            "<code>@mention_me /new \n/deadline 14 \n/topic your idea \n/tech mern stack \nhttps://github.com/repo \n@dev mentions</code>\n\n"

            "💡 New to Git? Skip repo with:\n"
            "<code>starter-dev: true</code>\n\n"

            "📅 <b>Daily Update</b>\n"
            "<code>update: what you built</code>\n\n"

            "🏁 <b>Finish</b>\n"
            "<code>/finished_project true</code>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "⏳ <b>Deadline Extension</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "If needed, you can extend your deadline:\n\n"
            "<code>extend 7</code> or <code>extend 14</code>\n\n"

            "⚠️ Rules:\n\n"
            "• Only <b>one extension</b> allowed\n"
            "• Extension reduces your 1 point ❌\n\n"

            "━━━━━━━━━━━━━━━━━━━\n"
        )
    # ───────────────── COMMANDS ───────────────── #
    elif command == "/help_commands":
        text = (
            "⚙️ <b>Commands Reference</b>\n\n"

            "━━━━━━━━━━━━━━━━━━━\n"
            "🧠 <b>Core Commands</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "<code>@mention_me /new</code> → Create a new team\n"
            "<code>/finished_project</code> → Mark project as completed\n\n"

            "━━━━━━━━━━━━━━━━━━━\n"
            "📘 <b>Help & Guides</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "<code>/help</code> → Open help center\n"
            "<code>/help_basic</code> → Quick start guide\n"
            "<code>/full_guidance</code> → Complete system walkthrough\n"
            "<code>/help_advanced</code> → Rules & points system\n"
            "<code>/help_commands</code> → View all commands\n"
            "<code>/grp_rules</code> → View group rules & guidelines\n\n"

            "━━━━━━━━━━━━━━━━━━━\n"
            "💬 <b>Community</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "<code>/feedback</code> → Submit feedback or suggestions\n\n"

            "━━━━━━━━━━━━━━━━━━━\n"
        )

    # ───────────────── ADVANCED ───────────────── #
    elif command == "/help_advanced":
        text = (
            "🧠 <b>Advanced System Overview</b>\n\n"

            "━━━━━━━━━━━━━━━━━━━\n"
            "📦 <b>Batch Lifecycle</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "Each batch follows 3 phases:\n\n"
            "• <b>Planning Phase</b> → Create teams\n"
            "• <b>Project Phase</b> → Build & send updates\n"
            "• <b>Clean-up Day</b> → Final wrap-up\n\n"

            "⚠️ Teams can only be created during Planning Phase\n\n"

            "━━━━━━━━━━━━━━━━━━━\n"
            "🏆 <b>Points & Progress</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "Your performance is tracked through:\n\n"
            "• <b>Daily Updates</b> → Earn points\n"
            "• <b>Consistency</b> → Builds streak\n"
            "• <b>Project Completion</b> → Bonus reward\n"
            "• <b>Missing updates</b> → Affects streak ⚠️\n\n"

            "━━━━━━━━━━━━━━━━━━━\n"

        )

    elif command == "/full_guidance":
        text = (
            "📘 <b>Complete Guide — How This System Works</b>\n\n"

            "━━━━━━━━━━━━━━━━━━━\n"
            "🧠 <b>1. Create a Team (During Planning Phase)</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"

            "Use this format:\n\n"

            "<code>@mention_me /new \n/deadline 14 \n/topic your idea \n/tech MERN stack\nhttps://github.com/repo \n@dev</code>\n\n"

            "📌 <b>Explanation:</b>\n\n"
            "• <b>/deadline</b> → Project duration (14 / 17 / 26 days)\n"
            "• <b>/topic</b> → What you're building\n"
            "• <b>/tech</b> → Tools / languages used\n"
            "• <b>GitHub</b> → Your project repo\n"
            "• <b>@dev</b> → Teammates (optional)\n\n"

            "💡 <b>Starter Dev Option</b>\n"
            "If you're new and still learning Git, you can skip adding a repo using:\n"
            "<code>starter-dev: true</code>\n\n"

            "━━━━━━━━━━━━━━━━━━━\n"
            "📅 <b>2. Daily Updates (Consistency)</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"

            "<code>eg: update: built login page</code>\n\n"

            "• First update → daily log\n"
            "• More messages → group activity\n"
            "• No update → affects streak ⚠️\n\n"

            "━━━━━━━━━━━━━━━━━━━\n"
            "⏳ <b>3. Project Phase</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"

            "• Build daily\n"
            "• Stay consistent → earn points\n\n"

            "━━━━━━━━━━━━━━━━━━━\n"
            "🏁 <b>4. Finish</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"

            "<code>/finished_project true</code>\n\n"

            "⚠️ Confirmation required to avoid mistakes\n\n"

            "━━━━━━━━━━━━━━━━━━━\n"
            "💡 <b>Goal</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"

            "• Build real projects\n"
            "• Stay consistent\n"
            "• Improve through execution\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
        )
    else:
        text = "❌ Unknown command"

    await update.effective_message.reply_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


def format_date(date_int):
    return datetime.strptime(str(date_int), "%Y%m%d").strftime("%Y-%m-%d")


async def batch_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    getstatus = await db_management.dbops('get_current_batch', '')

    print(f'batch :{getstatus[0]}')
    if not getstatus:
        await update.message.reply_text(
            "❌ <b>No active batch right now</b>",
            parse_mode="HTML"
        )
        return

    batch = getstatus

    # unpack (based on your table)
    batch_id = batch[0]
    planning_date = batch[1]
    deadline_days = batch[3]
    is_extended = batch[4]
    deadline_date = batch[5]
    project_start = batch[6]
    cleanup_day = batch[7]

    # format extension
    ext_text = "✅ Yes" if is_extended else "❌ No"

    message = (
        "📦 <b>Current Batch Details</b>\n\n"

        "━━━━━━━━━━━━━━━━━━━\n"
        f"⭐ <b>Batch Started :</b> {format_date(batch_id)}\n"
        f"🗓️ <b>Planning End Date:</b> {format_date(planning_date)}\n\n"

        "🚀 <b>Phases</b>\n\n"
        f"• Project Start → {format_date(project_start)}\n"
        f"• Batch Deadline → {format_date(deadline_date)}\n"
        f"• Clean-up Day → {format_date(cleanup_day)}\n\n"

        f"⏳ <b>Duration:</b> {deadline_days} days\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
    )

    await update.message.reply_text(
        message,
        parse_mode="HTML"
    )


async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "👋 <b>Hi Devs</b>\n\n"

        "Welcome aboard 🚀\n\n"

        "This community is about <b>learning by building</b>, staying consistent, and growing together as developers.\n\n"

        "<blockquote>You’ll work on real projects, collaborate with others, and build habits that actually matter ⚡</blockquote>\n\n"

        "🔥 <b>Let’s begin this journey together</b>\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎮 <b>Game-Based Learning System</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "We use a <b>points + streak + deadline</b> system to make learning:\n"
        "👉 <i>fun</i>\n"
        "👉 <i>competitive</i>\n"
        "👉 <i>consistent</i>\n\n"

        "🚀 <b>START HERE</b>\n\n"
        "Pick a project (from pool or your own)\n"
        "Choose a deadline → <code>14 / 17 / 26 days</code>\n"
        "Do this daily:\n"
        "<blockquote>"
        "Share your progress\n"
        "</blockquote>\n"

        "📊 <i>Points system depends on your chosen deadline (explained below)</i>\n\n"
        "🎯 <b>Goal:</b> Reach <code>60 points</code>\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 <b>Points System (Based on Deadline)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "🔹 <b>17 Days (Default)</b>\n"
        "Daily update → <code>2 points</code>\n"
        "Daily activity → <code>1 point</code>\n"
        "👉 Max: <b><code>3 points/day</code></b>\n\n"

        "🔹 <b>14 Days</b>\n"
        "Daily progress → <code>2 points</code>\n"
        "Group activity → <code>2 points</code>\n"
        "👉 Max: <b><code>4 points/day</code></b>\n\n"

        "🔹 <b>26 Days</b>\n"
        "Daily progress → <code>1 point</code>\n"
        "Daily activity → <code>1 point</code>\n"
        "👉 Max: <b><code>2 points/day</code></b>\n\n"

        "🔥 <b>Streak Bonus</b>\n"
        "<code>6 consecutive days/week → +2 points</code>\n\n"
        "<i>Stay consistent to earn bonus points</i>\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Projects — How to Start?</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "🔹 <b>Project Pool ✴️</b>\n\n"

        "<i>Project Pool is a curated collection of projects designed for different skill levels.</i>\n\n"
        "<i>It helps you pick the right project based on your current level and start building immediately.</i>\n\n"

        "<blockquote>"
        "Beginner → Advanced projects available\n"
        "Focused on strong fundamentals and real-world concepts"
        "</blockquote>\n\n"

        "✔ Beginners can pick directly\n"
        "✔ Teams can be formed using polls\n\n"

        "🧠 <b>Best Approach (Recommended)</b>\n"
        "<blockquote>"
        "1️⃣ Pick a project\n"
        "2️⃣ Improve or tweak the idea\n"
        "3️⃣ Create a poll:\n\n"
        "Interested ✅\n"
        "Interested with tweaks ⚠️\n"
        "Not interested 🚫\n\n"
        "4️⃣ Form a team\n"
        "5️⃣ Discuss\n"
        "6️⃣ Finalize & announce"
        "</blockquote>\n\n"

        "🔥 Leads to <b>strong, real-world projects</b>\n\n"

        "🔁 <b>Have Your Own Idea?</b>\n"
        "<blockquote>"
        "Create the same poll\n"
        "Gather interested developers\n"
        "Start building"
        "</blockquote>\n\n"

        "👤 <b>Solo Option</b>\n"
        "<i>Just announce your project — No poll needed</i>\n\n"

        "✔ Perfect for <b>independent learning</b>\n\n"

        "🟢 <b>Beginners</b>\n\n"

        "You can start even if you're new 🚀\n\n"

        "<blockquote>"
        "Use starter programming resources\n"
        "Learn Git alongside"
        "</blockquote>\n\n"

        "👉 <i>Follow same rules: updates + consistency</i>\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⏱️ <b>Deadlines</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "Choose what fits you:\n\n"
        "<code>14 Days</code> → Fast-paced ⚡\n"
        "<code>17 Days</code> → Balanced (Default) 🎯\n"
        "<code>26 Days</code> → Flexible 🧠\n\n"

        "🎯 All paths lead to <b><code>60 points</code></b>\n\n"

        "⏳ Extension allowed → <b><code>–1 point penalty</code></b>\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👥 <b>Team vs Individual</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "✔ Team → <i>more ideas, faster growth</i>\n"
        "✔ Solo → <i>full control, focused learning</i>\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 <b>Completion</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "<blockquote><b><i>"
        "Reach 60 points\n"
        "Build real projects\n"
        "Develop consistency\n"
        "Unlock achievement badges 🏆"
        "</i></b></blockquote>\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ <b>Important Rules</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "• <b>Declare deadline</b> before starting\n"
        "• <b>GitHub repo required</b> (<i>optional for starters</i>)\n"
        "• <b>Keep team discussions</b> in separate chats\n"
        "• <b>Daily points</b> shared <i>next day</i>\n"
        "• <b>Check tech stack</b> before teaming up\n"
        "• <b>Respect everyone</b> 🤝\n\n"

        "<i>For more clarification, type</i> <code>/help</code> 🚀\n\n"
        "🔥 <b><i>Build consistently. Ship real projects. Grow together.</i></b>"
    )

    await update.message.reply_text(text, parse_mode="HTML")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text_caps = ' '.join(context.args).upper()
    print(text_caps)
    await context.bot.send_message(chat_id=update.message.chat_id, text=text_caps)
    print(f' id: {update.effective_chat.id} user: {update.message.chat} and {update.message.text}')


async def submit_dev_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Extract data
    msg_date = datetime.now().isoformat()
    dev_id = update.effective_user.id
    dev_name = update.effective_user.first_name

    # Get full message after command
    query_txt = " ".join(context.args)

    if not query_txt:
        await update.effective_message.reply_text(
            "⚠️ Please provide your suggestion or report.\nExample: /feedback add more points"
        )
        return

    args = [msg_date, dev_id, dev_name, query_txt]

    # Call DB function
    result = await db_management.dbops('dev_suggestions_add', args)

    if result:
        await update.effective_message.reply_text(
            "✅ Feedback submitted successfully!",
            parse_mode="HTML"
        )
    else:
        await update.effective_message.reply_text(
            "❌ Failed to submit feedback. Try again later.",
            parse_mode="HTML"
        )


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📜 <b>Commitio Group Rules</b>\n\n"

        "━━━━━━━━━━━━━━━━━━━\n"
        "🤝 <b>Respect First</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "• Respect all developers\n"
        "• No toxic behavior or harassment ❌\n\n"

        "━━━━━━━━━━━━━━━━━━━\n"
        "💬 <b>Keep It Relevant</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "• Discussions should be mostly tech-related\n"
        "• Avoid unnecessary or off-topic chats\n\n"

        "━━━━━━━━━━━━━━━━━━━\n"
        "🚫 <b>No Bad Language</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "• No abusive or offensive words\n"
        "• Keep communication clean & professional\n\n"

        "━━━━━━━━━━━━━━━━━━━\n"
        "📢 <b>No Spam</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "• No promotions / ads\n"
        "• No irrelevant links\n\n"

        "━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <b>Stay Productive</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "• Focus on building & learning\n"
        "• Share progress, not noise\n\n"

        "━━━━━━━━━━━━━━━━━━━\n"
        "🎯 <b>Goal</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Build together. Grow together. 🚀"
    )

    await update.effective_message.reply_text(
        text,
        parse_mode="HTML"
    )


def pybot():
    print(f'production : {is_production}')
    if is_production:
        if TELEGRAM_BOT_TOKEN_COMMITIO is None:
            raise ValueError("TELEGRAM_BOT_TOKEN_COMMITIO is not set")
        token = TELEGRAM_BOT_TOKEN_COMMITIO
    else:
        if TELEGRAM_BOT_TOKEN_TEST is None:
            raise ValueError("TELEGRAM_BOT_TOKEN_TEST is not set")
        # token = TELEGRAM_BOT_TOKEN_TEST
        token = TELEGRAM_BOT_TOKEN_COMMITIO

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("join", join_grp))
    application.add_handler(CommandHandler("grp", create_batch_group))
    application.add_handler(CommandHandler("finished_project", finished_project))
    application.add_handler(CommandHandler("batch_details", batch_details))

    grp_msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), grp_msg)
    application.add_handler(grp_msg_handler)

    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("help_basic", help))
    application.add_handler(CommandHandler("help_commands", help))
    application.add_handler(CommandHandler("help_advanced", help))
    application.add_handler(CommandHandler("full_guidance", help))
    application.add_handler(CommandHandler("grp_rules", rules))
    application.add_handler(CommandHandler("formate_msgs", format_msgs))
    application.add_handler(CommandHandler("guide", guide))
    application.add_handler(CommandHandler("feedback", submit_dev_feedback))

    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        print("🛑 Bot stopped cleanly")


pybot()
