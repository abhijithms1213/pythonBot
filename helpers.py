import random
import asyncio

from telegram import Update

import db_management

import re
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import operator as op
from telegram.constants import MessageEntityType


def randint(min=00000, max=99999):
    num = random.randint(min, max)
    return num


async def check_exist():
    while True:
        team_id = randint()
        status = await db_management.dbops('check_team_id_unique',
                                           team_id)
        print(f'team id is ::"":: {team_id}')
        if status:
            break


import random

# 🎯 100 TEAM NAMES
TEAM_NAMES = [
    "Code Titans", "Bug Slayers", "Binary Beasts", "Stack Masters",
    "Dev Dominators", "Logic Legends", "Syntax Squad", "Byte Warriors",
    "Code Commanders", "Debug Ninjas", "Pixel Pioneers", "Algorithm Army",
    "Script Storm", "Compile Kings", "Tech Troopers", "Cyber Squad",
    "Quantum Coders", "Runtime Rebels", "Dev Dynasty", "Hack Heroes",
    "Infinite Loopers", "Null Pointers", "Recursive Minds", "Terminal Titans",
    "Git Guardians", "Merge Masters", "Branch Bosses", "Code Crafters",
    "Dev Dragons", "Stack Overflowers", "Cloud Crusaders", "Kernel Kings",
    "AI Avengers", "Data Dynamos", "Backend Bandits", "Frontend Force",
    "Fullstack Fighters", "Server Samurai", "Cache Crew", "Script Squad",
    "Bug Hunters", "Error Eliminators", "Logic Lords", "Syntax Samurai",
    "Binary Bosses", "Dev Knights", "Code Crushers", "Hack Hustlers",
    "Deploy Demons", "Runtime Raiders", "Compile Crew", "Script Soldiers",
    "Tech Titans", "Code Wizards", "Bug Busters", "Stack Slayers",
    "Dev Ninjas", "Cyber Knights", "Pixel Pirates", "Algorithm Aces",
    "Terminal Troops", "Merge Mavericks", "Branch Breakers", "Git Gurus",
    "Code Ninjas", "Debug Squad", "Stack Savages", "Binary Bandits",
    "Dev Storm", "Hack Squad", "Cloud Commanders", "Kernel Knights",
    "AI Squad", "Data Warriors", "Backend Bosses", "Frontend Ninjas",
    "Fullstack Squad", "Server Soldiers", "Cache Kings", "Script Ninjas",
    "Bug Squad", "Error Squad", "Logic Ninjas", "Syntax Soldiers",
    "Binary Soldiers", "Dev Legends", "Code Squad", "Hack Ninjas",
    "Deploy Squad", "Runtime Squad", "Compile Ninjas", "Script Kings",
    "Tech Squad", "Code Soldiers", "Bug Ninjas", "Stack Squad"
]

# 🎯 SOLO DEV NAMES
SOLO_NAMES = [
    "Lone Coder", "Solo Ninja", "Debug Monk", "Silent Hacker",
    "Code Wanderer", "Byte Hermit", "Logic Ranger", "Stack Samurai",
    "Bug Slayer", "Script Ghost", "Terminal Nomad", "Cyber Monk",
    "Code Sniper", "Binary Lonewolf", "Dev Phantom", "Hack Ranger",
    "AI Lonewolf", "Data Hermit", "Backend Ninja", "Frontend Solo",
    "Fullstack Lonewolf", "Server Ghost", "Cache Monk", "Script Ninja",
    "Bug Hunter", "Error Slayer", "Logic Ninja", "Syntax Monk",
    "Binary Ninja", "Dev Ranger"
]


# ✅ METHOD 1 → TEAM NAME
def get_random_team_name() -> str:
    return random.choice(TEAM_NAMES)


# ✅ METHOD 2 → SOLO NAME
def get_random_solo_name() -> str:
    return random.choice(SOLO_NAMES)


async def update_for_extended_devs(msg_date, update: Update, team_id_ret, user_name_ret):
    # checks is user's data already here in logs with current date
    sanitized_date = msg_date

    user_id = update.message.from_user.id
    user_name = update.message.chat.username
    msg = update.message.text
    msg_lower = msg.lower()
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


def build_mentions(devs):
    mentions = []

    for name, uid in devs:
        if str(uid).startswith("@"):
            mentions.append(uid)
        else:
            mentions.append(f'<a href="tg://user?id={uid}">{name}</a>')

    final_mentions = "\n".join(mentions)

    # return " ".join(mentions)
    return final_mentions


def get_random_alert_solo_msg():
    msgs = [
        "⚠️ Hey! You missed your update today.",
        "🚨 Reminder! You haven’t posted your update yet.",
        "👀 Still waiting for your update...",
        "⏳ Don’t forget to update today!",
        "🔥 Come on, your update is pending!",
        "📢 Your daily update is missing.",
        "🛑 No update from you today.",
        "💡 Quick reminder to post your update!"
    ]
    return random.choice(msgs)


def get_random_alert_team_msg():
    msgs = [
        "⚠️ Some updates are missing today:",
        "🚨 Attention team! Updates pending from:",
        "👀 Waiting on updates from:",
        "⏳ Daily updates still pending for:",
        "📢 Team update check — missing from:",
        "🔥 Let’s keep the streak going! Pending updates:",
        "🛑 Update not received from:",
        "📊 Daily report incomplete — waiting for:"
    ]
    return random.choice(msgs)
