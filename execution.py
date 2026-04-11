from telegram import Update
from datetime import datetime, timedelta
import re
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import operator as op
from telegram.constants import MessageEntityType

import helpers
import db_management


async def mention_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mentions = []
    message = update.effective_message
    if message.entities:
        for entity in message.entities:
            if entity.type == MessageEntityType.TEXT_MENTION:
                user = entity.user  # This will be the telegram.User object
                if user:
                    await message.reply_text(f"User mentioned: {user.first_name} (ID: {user.id})")
                    print('inside normal mention')
                    mentions.append(user.id)
            elif entity.type == MessageEntityType.MENTION:
                # For regular @username mentions, you only get the text
                mention_text = message.parse_entity(entity)
                await message.reply_text(f"Username mentioned: {mention_text}")

                user = await db_management.dbops('check_is_user_already_exist_in_user_db',
                                                 mention_text)
                if user:
                    print(f'found user {user}')
                    mentions.append(f'{user}')
                else:
                    print('not found in db about user')
                    mentions.append(mention_text)

    # mentions.append(update.message.from_user.id)
    return mentions


async def msg_process(msg_date, update: Update, context: ContextTypes.DEFAULT_TYPE, current_batch):
    current_batch = current_batch
    msg = update.message.text
    split_msgs: list[str] = msg.split()
    lower_split = [s.lower() for s in split_msgs]
    lower_msg = msg.lower()

    print(f'lower is : {lower_msg}\n============================')

    deadlines = ['14', '17', '26']
    find_starting = '/new'
    find_topic = '/topic'

    github_url = 'https://github.com/'
    github_repo = None

    # ✅ detect starter dev
    is_starter_dev = bool(re.search(r'starter-dev\s*:\s*true', lower_msg))

    # ✅ extract github repo (before logic)
    for link in lower_split:
        if link.startswith(github_url):
            github_repo = link
            break

    # listing
    dev_not_joined: list = []
    dev_already_joined: list = []
    dev_currently_joined: list = []

    if op.contains(lower_msg, find_starting):

        # ✅ deadline
        deadline_match = re.search(r'/deadline\s*(\d+)', lower_msg)
        if not deadline_match:
            print('deadline not found')
            return 'error_no_deadline'

        deadline = deadline_match.group(1)
        print(f'deadline captured is {deadline}')

        if deadline not in deadlines:
            print('deadline invalid')
            return 'error_invalid_deadline'

        # ✅ topic
        if not op.contains(lower_msg, find_topic):
            print('topic not found')
            return 'error_no_topic'

        topic_match = re.search(r'/topic\s*([^\n]+)', lower_msg)
        topic = topic_match.group(1).strip() if topic_match else None

        if not topic:
            print('topic empty')
            return 'error_no_topic'

        print(f'topic is : {topic}')

        # ✅ tech
        tech_stack = re.search(r'/tech\s*([^\n]+)', lower_msg)
        if not tech_stack:
            print('tech not found')
            return 'error_no_tech'

        tech = tech_stack.group(1).strip()
        print(f'tech is : {tech}')

        # ✅ github validation
        if not github_repo:
            if is_starter_dev:
                print('starter-dev true → allowing null repo')
                github_repo = None
            else:
                print('not found github link')
                return 'error_no_github'
        else:
            print(f'valid repo: {github_repo}')

        # ✅ mentions
        mentions = await mention_check(update, context)

        # ✅ generate team_id
        team_id_attempts = 0
        while True:
            team_id = helpers.randint()
            status = await db_management.dbops('check_team_id_unique', team_id)

            team_id_attempts += 1
            if team_id_attempts >= 10:
                return 'invalid_something_went_wrong'

            if status:
                break

        print(f'team id: {team_id}')

        # ✅ generate team name
        team_name_attempts = 0
        while True:
            if len(mentions) == 1:
                team_name = helpers.get_random_solo_name()
            else:
                team_name = helpers.get_random_team_name()

            status = await db_management.dbops('check_team_name_unique', team_name)

            team_name_attempts += 1
            if team_name_attempts >= 10:
                return 'invalid_something_went_wrong'

            if status:
                break

        print(f'team name: {team_name}')

        # ✅ core info
        core_infos = {
            'topic': topic,
            'github_repo': github_repo,
            'tech': tech,
            'is_starter_dev': is_starter_dev
        }

        # ✅ add team
        team_return = await db_management.dbops(
            'add_to_team',
            [
                team_id,
                current_batch[0],
                mentions,
                int(deadline),
                current_batch[5],
                current_batch[1],
                core_infos,
                team_name,
                current_batch[3]
            ]
        )

        if team_return[0] is not True:
            imposter = team_return[1]
            print(f'user already exists: {imposter}')
            return ['error_user_exist', imposter]

        # ✅ unpack
        deadline_returned = team_return[1]
        deadline_as_formate_returned = team_return[2]
        deadline_full_returned = team_return[3]
        team_id_returned = team_return[4]

        print('team added successfully')

        # ✅ add devs
        for user_id in mentions:
            user_dict = {
                'user_tele_id': user_id,
                'deadline': int(deadline_returned),
                'deadline_full': deadline_full_returned,
                'topic': topic,
                'github_repo': github_repo,
                'tech': tech,
                'team_id': team_id_returned
            }

            return_val = await db_management.dbops(
                'add_dev_to_db',
                [user_id, user_dict, context, current_batch]
            )

            developer_id_return = return_val[1]
            status = return_val[0]

            if status == 0:
                dev_currently_joined.append(developer_id_return)

            elif status == 1:
                dev_currently_joined.append(developer_id_return)
                dev_not_joined.append(developer_id_return)

            elif status == 3:
                dev_not_joined.append(developer_id_return)
                dev_already_joined.append(developer_id_return)

            else:
                dev_already_joined.append(developer_id_return)

        print(f'not joined: {dev_not_joined}')
        print(f'already joined: {dev_already_joined}')
        print(f'new: {dev_currently_joined}')

        return [
            'valid',
            dev_currently_joined,
            dev_not_joined,
            topic,
            tech,
            github_repo,
            deadline,
            deadline_as_formate_returned,
            team_name
        ]

    else:
        print("no /new command")
        return 0


async def project_phase(msg_date, update: Update, context: ContextTypes.DEFAULT_TYPE, current_batch):
    sanitized_date = msg_date
    print(f'msg date: {msg_date}')

    # don't forget to replace below
    # sanitized_date = 20260411

    current_batch = current_batch
    user_id = update.message.from_user.id
    user_name = update.message.chat.username
    msg = update.message.text
    msg_lower = msg.lower()
    # print(f' uid: {user_id}')
    today = datetime.today().date()
    today_as_int = int(today.strftime("%Y%m%d"))
    status, isFinishedFromUser, deadline_as_date, is_extended, ext_date = await db_management.dbops(
        'check_team_under_batch',
        [current_batch[0], user_id])
    print(f'status is : {status}')
    if status is None:
        print('no user found in db so not need to record')
        return False
    else:
        user_doc = status[0]
        team_id_ret = user_doc[2]
        user_name_ret = user_doc[3]
        print(f'is finished :{isFinishedFromUser}')

        extend_msg = re.search(
            r'extend(?:\s*[:=]?\s*|\s+for\s+)(7|14)\b',
            msg_lower
        )

        if extend_msg:
            if not isFinishedFromUser:
                ext_days = int(extend_msg.group(1))

                if sanitized_date <= deadline_as_date:
                    new_ext_date = datetime.strptime(str(deadline_as_date), '%Y%m%d')
                    temp = new_ext_date + timedelta(days=ext_days)
                    ext_new_date = int(temp.strftime("%Y%m%d"))
                    ext_date = temp.date()

                    update_stat = await db_management.dbops('dev_extend_deadline',
                                                            [team_id_ret, ext_new_date, user_id])
                    if update_stat:
                        msg = f"✅ Deadline extended successfully!\n\n📅 New extended deadline: <b>{ext_date}</b>"
                        await update.message.reply_text(
                            msg,
                            parse_mode="HTML"
                        )
                        return 'done'
                    else:
                        print('already extended u before......')
                        return 'not_updated_something_wrong'
                else:
                    print('msged after deadline, but its ok we can extend with todays date, not from deadline')
                    new_ext_date = datetime.strptime(str(sanitized_date), '%Y%m%d')
                    temp = new_ext_date + timedelta(days=ext_days)
                    ext_new_date = int(temp.strftime("%Y%m%d"))
                    # batch_deadline_count = current_batch[3]
                    # batch_deadline_as_date = current_batch[5]
                    # team_deadline = status[0][8]
                    # print(f'deadlness : {batch_deadline_count} <= batch and teams => {team_deadline} ')

                    # if batch_deadline_as_date == team_deadline:
                    update_stat = await db_management.dbops('dev_extend_deadline',
                                                            [team_id_ret, ext_new_date, user_id])
                    ext_date = temp.date()
                    if update_stat:
                        msg = f"✅ Deadline extended successfully!\n\n📅 New extended deadline: <b>{ext_date}</b>"
                        await update.message.reply_text(
                            msg,
                            parse_mode="HTML"
                        )
                        return 'done'
                    else:
                        print('already extended u before')
                        return 'not_updated_something_wrong'
            else:
                print('u cant update , u finished project')
                msg = "⚠️ You can't update , u already finished project"
                await update.message.reply_text(msg)
        is_all_ok = False
        if sanitized_date <= deadline_as_date:
            if isFinishedFromUser == 1:
                return 'already_finished'
        else:
            if is_extended == 1 and sanitized_date <= ext_date:
                is_all_ok = True
            else:
                print('the msg is not under deadline and u didnt extended also')
                return 'date_after_extension'
        if not isFinishedFromUser == 1 or is_all_ok:
            print('entered recording section in project phase')
            # checks is user's data already here in logs with current date
            is_user = await db_management.dbops('daily_activity_record_check_record', [user_id, sanitized_date])
            print(f'user :{is_user} ')
            if not is_user:
                print('user is empty coz list is empty')
                match = re.search(r'update:\s*(.*)', msg_lower, re.DOTALL)
                # if user's 1st msg in that day is update: then this
                if match:
                    #
                    message = match.group(1).strip()
                    print(f'update msg: {message} and length {len(message)}')
                    status_ret = await db_management.dbops('add_daily_update_in_logs',
                                                           [sanitized_date, user_id, user_name_ret, message,
                                                            0, team_id_ret, is_extended
                                                            ])  # last 0 means first entry
                    return True

                else:
                    is_updated = await  db_management.dbops('add_activity_msg_first_entry_today',
                                                            [user_id, msg, sanitized_date, user_name_ret,
                                                             0, team_id_ret, is_extended
                                                             ])  # last 0 means first entry

                    if is_updated:
                        print('its not update msg its daily activity')
                        return True
            else:
                #  it's not first msg so already tuple added in daily_log table
                print('the else worked means user doc found in daily_logs')
                match = re.search(r'update:\s*(.*)', msg_lower, re.DOTALL)
                if match:
                    message = match.group(1).strip()
                    is_updated = await db_management.dbops('add_daily_update_in_logs',
                                                           [sanitized_date, user_id, user_name_ret, message,
                                                            1,
                                                            team_id_ret, is_extended
                                                            ])  # 0,0 is user_name last 0 means first entry
                    if is_updated:
                        print(f'it"s after first update msg: {message} and length {len(message)}')
                        return True
                else:
                    activity_status = await db_management.dbops('add_activity_msg_first_entry_today',
                                                                [user_id, msg, sanitized_date, user_name_ret,
                                                                 1, team_id_ret, is_extended
                                                                 ])  # last 0 means first entry
                    print('msg after first record it"s activity')
            return True
        else:
            print('user already finished project so not updating')
            return False
