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
                return 'error_invalid_deadline'
            if op.contains(lower_msg, find_topic):
                # topic = str(re.findall('"([^"]*)"', lower_msg)).replace("'", "").replace('[', '').replace(']', '')
                topic = re.search(r'/topic\s*([^\n]+)', lower_msg).group(1).strip()
                if not topic:
                    print(f'topic not found')
                    return 'error_no_topic'
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

                                # adding team id
                                team_id_attempts = 0

                                while True:
                                    team_id = helpers.randint()
                                    print(f'team id is ::"":: {team_id}')

                                    status = await db_management.dbops('check_team_id_unique', team_id)

                                    team_id_attempts += 1
                                    if team_id_attempts >= 10:
                                        return 'invalid_something_went_wrong'

                                    if status:
                                        break

                                # TEAM NAME GENERATION
                                team_name_attempts = 0

                                while True:
                                    if len(mentions) == 1:
                                        print(f'mentions : from len 1: {mentions}')
                                        team_name = helpers.get_random_solo_name()
                                    else:
                                        team_name = helpers.get_random_team_name()
                                        print(f'team names are ::"":: {team_name}')

                                    status = await db_management.dbops('check_team_name_unique', team_name)

                                    team_name_attempts += 1
                                    if team_name_attempts >= 10:
                                        return 'invalid_something_went_wrong'

                                    if status:
                                        break

                                # date_after_planning = str(current_batch[0])  # e.g. 20260327
                                # date_obj = datetime.strptime(date_after_planning, "%Y%m%d")  # 2026-03-27
                                #
                                # deadline_date = date_obj + timedelta(days=int(updated_deadline))
                                #
                                # deadline_full = deadline_date.strftime("%Y%m%d")  # 20260410
                                # add to team
                                core_infos = {
                                    'topic': topic,
                                    'github_repo': github_repo,
                                    'tech': tech,
                                }

                                team_return = await db_management.dbops('add_to_team',
                                                                        [team_id, current_batch[0], mentions,
                                                                         int(deadline), current_batch[5],
                                                                         # deadline as date [5] don't take
                                                                         current_batch[1], core_infos, team_name,
                                                                         current_batch[3]])
                                # return only true won't get list of added devs
                                if team_return[0] is True:
                                    deadline_returned = team_return[1]
                                    deadline_as_formate_returned = team_return[2]
                                    deadline_full_returned = team_return[3]
                                    team_id_returned = team_return[4]
                                    # if all users are successfully added only then we add in devs table
                                    print('successfully added all users in teams table')
                                    for user_id in mentions:
                                        user_dict = {'user_tele_id': user_id,
                                                     'deadline': int(deadline_returned),
                                                     'deadline_full': deadline_full_returned,
                                                     'topic': topic,
                                                     'github_repo': github_repo,
                                                     'tech': tech,
                                                     'team_id': team_id_returned
                                                     }
                                        return_val = await db_management.dbops('add_dev_to_db',
                                                                               [user_id, user_dict, context,
                                                                                current_batch])

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
                                            dev_not_joined.append(developer_id_return)
                                            print('added user with user_name @ , so highly recommended to join')
                                        elif status == 3:
                                            # it won't work because if already joined if original_user_id == user_joined_name it cannot true, if it's true then already failed in team check
                                            dev_not_joined.append(developer_id_return)
                                            dev_already_joined.append(developer_id_return)
                                            print('found user didnt updated in /join')
                                        else:
                                            # it won't work because if already joined , team have record then make false
                                            dev_already_joined.append(developer_id_return)
                                            print("found user so now don't update")

                                else:
                                    imposter = team_return[1]
                                    print(
                                        f'he:{imposter} is already joined so ignoring not added anyone please ensure')
                                    return ['error_user_exist', imposter]

                                # clear list after all msg sent
                                print(
                                    f'devs not /join : {dev_not_joined} & already joined in this batch: {dev_already_joined} & new joins: {dev_currently_joined}')
                                print(f'devs already joined check {dev_already_joined}')
                                # user_dict = {'user_tele_id': user_id,
                                #              'deadline': int(updated_deadline),
                                #              # 'deadline_full': deadline_full, or deadline_dae
                                #              'topic': topic,
                                #              'github_repo': github_repo,
                                #              'tech': tech,
                                #              'team_id': team_id
                                #              }
                                return_list = ['valid', dev_currently_joined, dev_not_joined, topic, tech, github_repo,
                                               deadline, deadline_as_formate_returned, team_name]
                                return return_list
                            else:
                                continue
                    else:
                        print('tech stack not found')
                        return 'error_no_tech'

                print('not found github link')
                return 'error_no_github'
            else:
                print('topic not found')
                return 'error_no_topic'
        else:
            print('deadline not found')
            return 'error_no_deadline'
    else:
        print("didn't found starter")
        return 0


async def project_phase(msg_date, update: Update, context: ContextTypes.DEFAULT_TYPE, current_batch):
    date_to_string = str(msg_date)
    date_only = date_to_string[:10]
    sanitized_date = int(date_only.replace('-', ''))
    print(f'msg date: {date_only} and sanitized :{sanitized_date}')

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
            ext_days = int(extend_msg.group(1))
            new_ext_date = datetime.strptime(str(deadline_as_date), '%Y%m%d')
            temp = new_ext_date + timedelta(days=ext_days)
            ext_new_date = int(temp.strftime("%Y%m%d"))
            update_stat = await db_management.dbops('dev_extend_deadline',
                                                    [user_id, ext_new_date])
            if update_stat:
                return 'done'
            else:
                return 'not_updated_something_wrong'

        is_all_ok = False
        if sanitized_date <= deadline_as_date:
            if isFinishedFromUser == 1:
                return 'already_finished'
        else:
            if is_extended == 1 and sanitized_date <= ext_date:
                is_all_ok = True
            else:
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
                                                            0, team_id_ret])  # last 0 means first entry
                    return True

                else:
                    is_updated = await  db_management.dbops('add_activity_msg_first_entry_today',
                                                            [user_id, msg, sanitized_date, user_name_ret,
                                                             0, team_id_ret])  # last 0 means first entry

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
                                                            team_id_ret])  # 0,0 is user_name last 0 means first entry
                    if is_updated:
                        print(f'it"s after first update msg: {message} and length {len(message)}')
                        return True
                else:
                    activity_status = await db_management.dbops('add_activity_msg_first_entry_today',
                                                                [user_id, msg, sanitized_date, user_name_ret,
                                                                 1, team_id_ret])  # last 0 means first entry
                    print('msg after first record it"s activity')
            return True
        else:
            print('user already finished project so not updating')
            return False
