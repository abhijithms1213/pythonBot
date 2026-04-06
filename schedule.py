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

def format_users(users):
    formatted = []
    for i, (tele_id, fullname, firstname, username, streak, points, team_name) in enumerate(users, start=1):
        name = fullname or firstname or username or "Unknown"
        mention = f'<a href="tg://user?id={tele_id}">{name}</a>'

        formatted.append(
            f"{i}. {mention}\n"
            f"   🧠 Streak: {streak} | ⭐ Points: {points}\n"
            f"   👥 Team: {team_name or 'No Team'}"
        )

    return "\n\n".join(formatted) if formatted else "None"


async def lets_clean_all(context: ContextTypes.DEFAULT_TYPE, update: Update):
    print('deadline+1 st day is clean up day')
    getstatus = await  db_management.dbops('get_current_batch', '')
    print(f'batch: {type(getstatus[1])} {type(getstatus[5])}\n')
    print(f'{getstatus}')
    today = datetime.now().date()
    today_as_int = int(today.strftime("%Y%m%d"))

    # for get clean up day
    deadline = getstatus[5]
    deadline_as_str = str(deadline)
    deadline_as_date = datetime.strptime(deadline_as_str, "%Y%m%d")
    clean_up_day = deadline_as_date + timedelta(days=1)
    clean_up_day_as_int = int(clean_up_day.strftime("%Y%m%d"))

    if today == clean_up_day:  # from it
        print('its time to clean')

        finished, not_finished_not_extended, not_finished_extended = await  db_management.dbops('clean_up_batch_end',
                                                                                                '')
        message = f"""
        ━━━━━━━━━━━━━━━━━━━━━━

        🏁 <b>Batch Report</b>

        🏆 <b>Finished Users</b>
        {format_users(finished)}

        ⚠️ <b>Not Finished (Deadline Over)</b>
        {format_users(not_finished_not_extended)}

        ⏳ <b>Extended Users</b>
        {format_users(not_finished_extended)}

        ━━━━━━━━━━━━━━━━━━━━━━
        """
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            parse_mode="HTML"
        )
        return ['clean_finished', getstatus]
    else:
        print('msg not under any')
        return [None, '']


def attention_msgs():
    print('attention')


async def weekly_report():
    print('weekly')
    getstatus = await  db_management.dbops('get_current_batch', '')
    print(f'batch: {type(getstatus[1])} {type(getstatus[0])}')
    print(f'{getstatus}')
    # today
    today = datetime.now().date()
    today = datetime.now().date() + timedelta(days=3)

    yesterday = today + timedelta(days=19)
    today_as_int = int(today.strftime("%Y%m%d"))
    start = getstatus[6]  # start date
    deadline = getstatus[3]  # start date

    start_as_str = str(start)  # e.g. 20260327
    start_as_formate = datetime.strptime(start_as_str, "%Y%m%d")

    first_week = start_as_formate + timedelta(7)
    first_week = first_week.date()

    second_week = start_as_formate + timedelta(14)
    second_week = second_week.date()

    devs = await  db_management.dbops('get_log_combined_for_week_update', [])

    if getstatus is None:
        print('no running batches')
        return ['no_batches_currently', '']
    elif getstatus[6] <= today_as_int <= getstatus[5]:  # 5 is deadline as whole numbers, 6 is project starts
        print(
            f'today {today} and day {today.strftime("%A")}, first week {first_week} ,and start: {start_as_formate},deadline {deadline}')
        if deadline == 14:
            if today == first_week:  # if starts 03-01 , then today == 03-07 is saturday
                #  here send start , end as first_week-1 for get data from daily log
                print('worked first sunday')
            elif today == second_week:
                #  here send first_week , end as scnd week-1 for get data from daily log
                print('worked first sunday')

        if deadline == 17:
            third_week = second_week + timedelta(4)
            third_week = third_week.date()
            if today == first_week:  # if starts 03-01 , then today == 03-07 is saturday
                #  here send start , end as first_week-1 for get data from daily log
                print('worked first sunday')
            elif today == second_week:
                #  here send first_week , end as scnd week-1 for get data from daily log
                print('worked first sunday')
            elif today == third_week:
                #  here send second_week , end as +4 from second week, so 5th day from 2nd week is elif need to work
                print('worked first sunday')

        if deadline == 26:
            if today == first_week:  # if starts 03-01 , then today == 03-07 is saturday
                print('worked first sunday')
            elif today == second_week:
                print('worked first sunday')
            elif today == third_week:
                #  here send second_week , end as third week-1 for get data from daily log
                print('worked first sunday')
            elif today == fourth_week:
                # here same like deadline = 17's third week : means: end as +4 and 5th day is send weekly report as replace that fourth_week
                print('worked first sunday')

        print('report is reco as project phase')
        return ['during_project_phase', getstatus]
    else:
        print('msg not under any')
        return [None, '']


async def daily_update(context: ContextTypes.DEFAULT_TYPE):
    getstatus = await  db_management.dbops('get_current_batch', '')
    print(f'batch: {type(getstatus[1])} {type(getstatus[0])}')
    print(f'{getstatus}')
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    yesterday = today
    print(f'yest : {yesterday}')
    today_as_int = int(today.strftime("%Y%m%d"))
    yesterday_as_int = int(yesterday.strftime("%Y%m%d"))
    print(f'day as str {today_as_int} yes :{yesterday_as_int}')

    if getstatus is None:
        print('no running batches')
    # if getstatus[0] <= yesterday_as_int <= getstatus[1]:
    #     # run the daily update in this case
    #     print('report is reco as planning')
    #     return ['during_planning', []]
    # elif getstatus[6] <= yesterday_as_int <= getstatus[5]:  # 5 is deadline as whole numbers
    if getstatus[0] <= yesterday_as_int <= getstatus[5]:  # 5 is deadline as whole numbers
        print('report is reco as project phase')
        daily_logs = await db_management.dbops('fetch_daily_log', [yesterday_as_int])
        print(f'daily_log {daily_logs}')
        if not daily_logs:
            print('no one updated yesterday')
        else:
            from collections import defaultdict

            grouped = defaultdict(lambda: defaultdict(list))

            for log in daily_logs:
                activity_status = log[0]
                update_status = log[1]
                tele_id = log[2]
                tele_username = log[3]
                team_name = log[4]
                team_deadline = log[6]
                point = log[8]

                grouped[team_deadline][team_name].append({
                    "user": tele_username,
                    "activity": activity_status,
                    "update": update_status,
                    "point": point
                })
                message = "📊 <b>Daily Report</b>\n\n"

                for deadline in sorted(grouped.keys()):
                    message += f"⏰ <b>Deadline: {deadline}</b>\n"

                    for team in grouped[deadline]:
                        message += f"\n📌 <b>Team: {team}</b>\n"

                        for user in grouped[deadline][team]:
                            status = "✅" if user["update"] == 1 else "❌"

                            message += (
                                f"  👤 {user['user']} | "
                                f"Update: {status} | "
                                f"Pts: {user['point']}\n"
                            )

                    message += "\n"

                zero_dev_grp_id = -5287913183
                await context.bot.send_message(
                    chat_id=zero_dev_grp_id,
                    text=message,
                    parse_mode="HTML"
                )

    else:
        print('msg not under any')


if __name__ == '__main__':
    asyncio.run(weekly_report())
