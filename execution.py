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
    deadlines = ['14', '17', '21']
    # deadlines = ['14', '17', '21', '14d', '21d', '17d']
    find_starting = '/new'
    find_topic = '/topic'
    # explicitly find GitHub repo link & mentions
    github_url = 'https://github.com/'
    github_repo: str
    # listing out users whoever joined, clear list after this whole message
    dev_not_joined: list = []
    dev_already_joined: list = []
    dev_currently_joined: list = []

    if op.contains(lower_msg, find_starting):
        deadline_match = re.search(r'/deadline\s*(\d+)', lower_msg)
        if deadline_match:
            deadline = deadline_match.group(1)
            print(f'deadlin captured is {deadline}')
            if deadline not in deadlines:
                print('deadline found as invalid')
                return 'invalid'
            if op.contains(lower_msg, find_topic):
                # topic = str(re.findall('"([^"]*)"', lower_msg)).replace("'", "").replace('[', '').replace(']', '')
                topic = re.search(r'/topic\s*([^\n]+)', lower_msg).group(1).strip()
                if not topic:
                    print(f'topic not found')
                    return 'invalid'
                else:
                    print(f'topic is : {topic}')
                    tech_stack = re.search(r'/tech\s*([^\n]+)', lower_msg)
                    if tech_stack:
                        tech = tech_stack.group(1).strip()
                        print(f'tech is : {tech}')
                        for link in lower_split:
                            if link.startswith(github_url):
                                github_repo = link
                                print(f'its all set and valid repo is {github_repo}')
                                #  get mentions from the message
                                mentions = await mention_check(update, context)

                                #  didn't need this , because we already confirmed batch found that's why this method exec.
                                # current_batch = await db_management.dbops('get_current_batch', '')
                                # print(f'batch status : {current_batch}')
                                # if current_batch is None:
                                #     return 'invalid'
                                # else:

                                # check if current deadline is under batch's deadline else update batch's deadline also
                                batch_deadline = current_batch[3]
                                deadline = int(deadline)
                                if deadline > batch_deadline:
                                    print('found deadline is greater than batch')
                                    updated_deadline = await db_management.dbops('update_deadline_of_batch',
                                                                                 deadline)
                                    if not updated_deadline:
                                        print('not updated any issues?')
                                        updated_deadline = deadline
                                else:
                                    print('deadline is under')
                                    updated_deadline = deadline

                                # adding team id
                                while True:
                                    team_id = helpers.randint()
                                    print(f'team id is ::"":: {team_id}')
                                    status = await db_management.dbops('check_team_id_unique',
                                                                       team_id)
                                    if status:
                                        break

                                batch_start = str(current_batch[0])  # e.g. 20260327
                                date_obj = datetime.strptime(batch_start, "%Y%m%d")

                                deadline_date = date_obj + timedelta(days=int(updated_deadline))

                                deadline_full = deadline_date.strftime("%Y%m%d")  # 20260410
                                print(f"deadline full : {deadline_full}")
                                print(
                                    f'batch info : {current_batch[0]} and deadline: {current_batch[3]}')  # i currently at this pos.

                                for user_id in mentions:
                                    user_dict = {'user_tele_id': user_id,
                                                 'deadline': int(updated_deadline),
                                                 'deadline_full': current_batch[5],
                                                 'topic': topic,
                                                 'github_repo': github_repo,
                                                 'tech': tech,
                                                 'team_id': team_id
                                                 }
                                    return_val = await db_management.dbops('add_dev_to_db',
                                                                           [user_id, user_dict, context, current_batch])
                                    # team rest

                                    team_return = await db_management.dbops('add_to_team',
                                                                            [team_id, current_batch[0], mentions])
                                    if team_return:
                                        print('successfully added all users in team table')

                                    print(f'result is {return_val}')
                                    developer_id_return = return_val[1]
                                    status = return_val[0]
                                    # 0 means we returned telegram_id and added to db fully ,
                                    # 1 is username returned, and we added details to db but  must join dev using bot,
                                    # 2 is already found he is joined in ths batch so not going to add
                                    # 3 means didn't joined even after warnings
                                    if status == 0:
                                        dev_currently_joined.append(developer_id_return)
                                        print(
                                            'status means new user add entire new user with details or updated our old dev')
                                        # add_user(user_id)
                                    elif status == 1:
                                        dev_currently_joined.append(developer_id_return)
                                        print('added user with user_name @ , so highly recommended to join')
                                    elif status == 3:
                                        dev_not_joined.append(developer_id_return)
                                        dev_already_joined.append(developer_id_return)
                                        print('found user didnt updated in /join')
                                    else:
                                        dev_already_joined.append(developer_id_return)
                                        print("found user so now don't update")

                                # clear list after all msg sent
                                print(
                                    f'devs not: {dev_not_joined} & already joined {dev_already_joined} & new joined: {dev_currently_joined}')
                                dev_not_joined.clear()
                                dev_already_joined.clear()
                                dev_currently_joined.clear()
                                print('all lists cleared')
                                return 'valid'
                            else:
                                continue
                    else:
                        print('tech stack not found')
                        return 'invalid'

                print('not found github link')
                return 'invalid'
            else:
                print('topic not found')
                return 'invalid'
        else:
            print('deadline not found')
            return 'invalid'
    else:
        print("didn't found starter")
        return 'invalid'


async def project_phase(msg_date, update: Update, context: ContextTypes.DEFAULT_TYPE, current_batch):
    current_batch = current_batch
    user_id = update.message.from_user.id
    user_name = update.message.chat.username
    msg = update.message.text.lower()
    # print(f' uid: {user_id}')
    status = await db_management.dbops('check_user_under_batch', [current_batch[0], user_id])
    # print(f'status is : {status}')
    if status is None:
        print('no user found in db so not need to record')
        return False
    else:
        additional_points = 0
        is_user = await db_management.dbops('daily_activity_record_check_record', [user_id])
        print(f'user :{is_user} ')
        if not is_user:
            print('no user found in db so not need to record')
            match = re.search(r'update:\s*(.*)', msg, re.DOTALL)
            # if user's 1st msg in that day is update: then this
            if match:
                message = match.group(1).strip()
                print(f'update msg: {message} and length {len(message)}')
                is_user = await db_management.dbops('add_daily_update_in_logs', [msg_date, user_id, status[0][0]])
                if is_user:
                    print('worked ')

            else:
                print('its not update msg its daily activity')
            return False
        else:
            print('last else worked')
            match = re.search(r'update:\s*(.*)', msg, re.DOTALL)
            if match:
                message = match.group(1).strip()
                print(f'update msg: {message} and length {len(message)}')
            return True
