import asyncio
from xmlrpc.client import DateTime

from telegram import Update
from datetime import datetime, timedelta
import re
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import operator as op
from telegram.constants import MessageEntityType

import helpers
import db_management

from datetime import datetime, timedelta


# async def daily_update():
#     getstatus = await  db_management.dbops('get_current_batch', '')
#     print(f'batch: {type(getstatus[1])} {type(getstatus[0])}')
#     print(f'{getstatus}')
#     today = datetime.now().date()
#     yesterday = today + timedelta(days=19)
#     print(f'yest : {yesterday}')
#     today_as_int = int(today.strftime("%Y%m%d"))
#     yesterday_as_int = int(yesterday.strftime("%Y%m%d"))
#     print(f'day as str {today_as_int} yes :{yesterday_as_int}')
#
#     if getstatus is None:
#         print('no running batches')
#         return ['no_batches_currently', '']
#     if getstatus[0] <= yesterday_as_int <= getstatus[1]:
#         # run the code
#         print('report is reco as planning')
#         return ['during_planning_phase', getstatus]
#
#     elif getstatus[6] <= yesterday_as_int <= getstatus[5]:  # 5 is deadline as whole numbers
#         print('report is reco as project phase')
#         return ['during_project_phase', getstatus]
#     elif yesterday_as_int > getstatus[5]:
#         print('after deadline worked')
#         return ['after_deadline', getstatus]
#     else:
#         print('msg not under any')
#         return [None, '']

def clean_up_everything():
    print('clean up')


def attention_msgs():
    print('attention')


def weekly_report():
    print('weekly')


async def daily_update():
    getstatus = await  db_management.dbops('get_current_batch', '')
    print(f'batch: {type(getstatus[1])} {type(getstatus[0])}')
    print(f'{getstatus}')
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    # yesterday = today
    print(f'yest : {yesterday}')
    today_as_int = int(today.strftime("%Y%m%d"))
    yesterday_as_int = int(yesterday.strftime("%Y%m%d"))
    print(f'day as str {today_as_int} yes :{yesterday_as_int}')

    if getstatus is None:
        print('no running batches')
        return ['no_batches_currently', '']
    # if getstatus[0] <= yesterday_as_int <= getstatus[1]:
    #     # run the daily update in this case
    #     print('report is reco as planning')
    #     return ['during_planning', []]
    # elif getstatus[6] <= yesterday_as_int <= getstatus[5]:  # 5 is deadline as whole numbers
    if getstatus[0] <= yesterday_as_int < getstatus[5]:  # 5 is deadline as whole numbers
        print('report is reco as project phase')
        daily_logs = await db_management.dbops('fetch_daily_log', [yesterday_as_int])
        print(f'daily_log {daily_logs}')
        if not daily_logs:
            print('no one updated yesterday')
            return ['during_planning_phase', daily_logs]
        else:
            for log in daily_logs:
                update_status = log[1]
                activity_status = log[0]
                tele_id = log[2]
                tele_username = log[3]
                team_name = log[4]
                team_deadline_as_date = log[5]
                team_deadline = log[6]
                team_id = log[7]
                print(f"""
                Activity        : {activity_status}
                Update Status   : {update_status}
                Telegram ID     : {tele_id}
                Username        : {tele_username}
                Team Name       : {team_name}
                Deadline Date   : {team_deadline_as_date}
                Deadline        : {team_deadline}
                Team ID         : {team_id}
                """)

            return ['during_planning_phase', daily_logs]
    elif yesterday_as_int > getstatus[5]:
        print('after deadline worked')
        return ['after_deadline', getstatus]
    else:
        print('msg not under any')
        return [None, '']


async def daily_report(date: int):
    get_devs = await  db_management.dbops('extract_dev_details', '')
    print('get all devs who are joined in this batch')

    print(get_devs)


if __name__ == '__main__':
    asyncio.run(daily_update())
