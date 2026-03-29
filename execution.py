from telegram import ForceReply, Update
import re
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import operator as op
from typing import TypedDict
from telegram.constants import MessageEntityType

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
                mentions.append(mention_text)

    if not mentions:
        mentions.append(update.message.from_user.id)
    return mentions


async def msg_process(msg_date, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    returnValue = 'false'

    # pattern = r"'([^']*)'|\"([^\"]*)\""
    class user_dict(TypedDict):
        user_tele_id: int
        deadline: int
        topic: str
        github_repo: str

    if op.contains(lower_msg, find_starting):
        deadline_match = re.search(r'/deadline\s*(\d+)', lower_msg)
        if deadline_match:
            deadline = deadline_match.group(1)
            print(f'deadlin captured is {deadline}')
            if deadline not in deadlines:
                print('deadline found as invalid')
                return 'invalid'
            if op.contains(lower_msg, find_topic):
                topic = str(re.findall('"([^"]*)"', lower_msg))
                if not topic:
                    print(f'quotes didnt added{topic}')
                    return 'invalid'
                else:
                    tech_stack = re.search(r'/tech\s*(\d+)', lower_msg)
                    if tech_stack:
                        tech = tech_stack.group(1)
                        print(f'topic is : {topic}')
                        for link in lower_split:
                            if link.startswith(github_url):
                                github_repo = link
                                print(f'its all set and valid repo is {github_repo}')
                                #  get mentions from the message
                                mentions = await mention_check(update, context)
                                print(f'mentions in loop {mentions}')
                                current_batch = db_management.dbops('get_current_batch', '')
                                print(f'status: {current_batch}')
                                if current_batch is None:
                                    return 'invalid'
                                else:
                                    deadline = current_batch[0] + current_batch[3]
                                    print(
                                        f'batch info : {current_batch[0]} and deadline: {current_batch[3]}')  # i currently at this pos.

                                for user_id in mentions:
                                    user_dict = {'user_tele_id': user_id,
                                                 'deadline': int(deadline),
                                                 'topic': topic,
                                                 'github_repo': github_repo,
                                                 'tech': tech
                                                 }
                                    return_val = db_management.dbops('add_dev_to_db',
                                                                     [user_id, user_dict, context, current_batch])
                                    print(f'result is {return_val}')
                                    if return_val == 'Added':
                                        print('status means new user add entire new user with details')
                                        # add_user(user_id)
                                    elif return_val == '@':
                                        print('found @ in that for loop msg_procuess method')
                                    else:
                                        print("found user so now don't update")

                                # call from db : add_new_user_to_db
                                return 'valid'
                            else:
                                continue
                    else:
                        print('tech stach not found')
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
