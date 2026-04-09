from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import db_management
from datetime import datetime, timedelta

zero_dev_grp_id = -5287913183
import helpers as helpers_py

from telegram.constants import MessageEntityType


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
async def process_weekly_report(first_as_int, second_as_int, is_from_between: bool = None):
    if not is_from_between:
        empty = ''
    else:
        empty = '17d'
    # 🔹 Step 1: Get logs
    get_ret = await db_management.dbops(
        'get_log_combined_for_week_update',
        [first_as_int, second_as_int, empty]
    )

    if not get_ret:
        return 'no_records'

    # 🔹 Step 2: Aggregate logs per dev
    dev_stats = {}

    for log in get_ret:
        date, points, tele_id, team_id, deadline, name, username = log

        if tele_id not in dev_stats:
            dev_stats[tele_id] = {
                'name': name,
                'username': username,
                'weekly_points': 0,
                'active_days': set(),
                'streak_point_earned': False
            }

        # ✅ Add daily points
        dev_stats[tele_id]['weekly_points'] += points

        # ✅ Track unique active days
        dev_stats[tele_id]['active_days'].add(date)

    # 🔹 Step 3: Convert active_days set → int
    for dev in dev_stats.values():
        dev['active_days'] = len(dev['active_days'])

    # 🔹 Step 4: Process each dev (ONLY ONCE PER DEV)
    for tele_id, dev in dev_stats.items():

        # ✅ Fetch dev details ONCE
        dev_details = await db_management.dbops(
            'get_one_dev_details',
            [tele_id]
        )

        if not dev_details[0]:
            continue

        dev_data = dev_details[1][0]

        # 🔹 weekly streak column
        weekly_streak = dev_data[10]

        # 🔥 Correct bonus logic
        bonus = (weekly_streak // 6) * 2

        if bonus > 0:
            dev['streak_point_earned'] = True

        # 🔹 Final points
        dev['final_points'] = dev['weekly_points'] + bonus

        # 🔹 Update DB
        await db_management.dbops(
            'update_dev_points_and_cycle',
            [tele_id, dev['final_points'], bonus]
        )

    # 🔹 Step 5: Leaderboard
    leaderboard = sorted(
        dev_stats.values(),
        key=lambda x: x['final_points'],
        reverse=True
    )

    # 🔹 Step 6: Build report
    # 🔹 Step 6: Build report (WITH USER ID TAGGING)
    report = "🏆 <b>Weekly Leaderboard</b>\n\n"

    for i, (tele_id, dev) in enumerate(
            sorted(dev_stats.items(), key=lambda x: x[1]['final_points'], reverse=True),
            start=1):
        streak_tag = " 🔥" if dev['streak_point_earned'] else ""

        # ✅ Proper Telegram user mention using ID
        user_tag = f'<a href="tg://user?id={tele_id}">{dev["name"]}</a>'

        report += (
            f"<b>{i}.</b> {user_tag} — "
            f"<b>{dev['final_points']} pts</b> "
            f"({dev['active_days']} days){streak_tag}\n"
        )

    return report


def format_users(users):
    if not users:
        return "None"

    formatted = []

    for i, (tele_id, fullname, firstname, username, streak, points, team_name) in enumerate(users, start=1):
        name = fullname or firstname or username or "Unknown"

        mention = f'<a href="tg://user?id={tele_id}">{name}</a>'

        formatted.append(
            f"{i}. {mention}\n"
            f"🧠 Streak: {streak} | ⭐ Points: {points}\n"
            f"👥 Team: {team_name or 'No Team'}"
        )

    return "\n\n".join(formatted)


async def lets_clean_all(context: ContextTypes.DEFAULT_TYPE, update: Update):
    today = datetime.now().date()
    today_as_int = int(today.strftime("%Y%m%d"))
    today_as_int = 20260508

    getstatus = await db_management.dbops('check_is_msg_under_planning_phase', [today_as_int])
    print(f'\n BATCH: {getstatus}')

    if getstatus is None:
        print('no running batches')

    elif getstatus[0] == 'clean_up_day':
        clean_up_day = getstatus[1][7]
        print(f'clean up day: {clean_up_day} and today is {today_as_int} and {today}')
        if today_as_int == clean_up_day:  # from it
            print('its time to clean')

            finished, not_finished_not_extended, not_finished_extended = await  db_management.dbops(
                'clean_up_batch_end',
                '')
            message = (
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "🏁 <b>Batch Report</b>\n\n"

                "🏆 <b>Finished Users</b>\n"
                f"{format_users(finished)}\n\n"

                "⚠️ <b>Not Finished (Deadline Over)</b>\n"
                f"{format_users(not_finished_not_extended)}\n\n"

                "⏳ <b>Extended Users</b>\n"
                f"{format_users(not_finished_extended)}\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━"
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                parse_mode="HTML"
            )
        else:
            print('msg not under any')
    else:
        print('not found any clean up day')


# [Done]
async def attention_msgs(context):
    batch = await db_management.dbops('get_current_batch', '')
    if not batch:
        print("No active batch")
        return
    # unpack (based on your schema)
    planning_date = batch[1]
    deadline_days = batch[3]
    deadline_as_date = batch[5]
    project_start = batch[6]

    today = datetime.now().date()
    today_as_int = int(today.strftime("%Y%m%d"))

    tomorrow_as_int = int((today + timedelta(days=1)).strftime("%Y%m%d"))
    # today_as_int = 20260411
    # tomorrow_as_int = 20260507

    print(
        f"📅 Today: {today_as_int} tommorrow {tomorrow_as_int} || project start:{project_start} || deadline: {deadline_as_date} || planning date:{planning_date}")

    # 🔔 1. Before planning ends (1 day before)
    if tomorrow_as_int == planning_date:
        await context.bot.send_message(
            chat_id=zero_dev_grp_id,
            text="⚠️ Planning phase ends tomorrow. Get ready!"
        )

    # 🚀 2. Project start day
    if today_as_int == project_start:
        await context.bot.send_message(
            chat_id=zero_dev_grp_id,
            text="🚀 Project starts today! Let's go!"
        )

    # ⏳ 3. Before deadline (1 day before)
    if tomorrow_as_int == deadline_as_date:
        await context.bot.send_message(
            chat_id=zero_dev_grp_id,
            text="⏳ Deadline is tomorrow! Final push!"
        )

    return


# [Done]
async def weekly_report(context: ContextTypes.DEFAULT_TYPE):
    print('weekly')
    getstatus = await  db_management.dbops('get_current_batch', '')
    print(f'batch: {type(getstatus[1])} {type(getstatus[0])}')
    print(f'{getstatus}')
    # today
    today = datetime.now().date()

    # first week
    # today = datetime.now().date() + timedelta(days=9)

    # second week
    # today = datetime.now().date() + timedelta(days=16)

    # 2nd half week
    # today = datetime.now().date() + timedelta(days=20)
    #
    # # third week
    # today = datetime.now().date() + timedelta(days=22)
    #
    # # fourth week
    # today = datetime.now().date() + timedelta(days=29)

    today_as_int = int(today.strftime("%Y%m%d"))
    start = getstatus[6]  # start date
    deadline = getstatus[3]  # start date

    start_as_str = str(start)  # e.g. 20260327
    start_as_int = int(start)  # e.g. 20260327
    start_as_formate = datetime.strptime(start_as_str, "%Y%m%d")

    first_week = start_as_formate + timedelta(6)
    first_week = first_week.date()
    first_week_as_int = int(first_week.strftime("%Y%m%d"))

    second_week = start_as_formate + timedelta(13)
    second_week = second_week.date()
    second_week_as_int = int(second_week.strftime("%Y%m%d"))

    second_third_week_for_d_17 = second_week + timedelta(4)
    second_third_week_as_int = int(second_third_week_for_d_17.strftime("%Y%m%d"))

    third_week = second_week + timedelta(7)
    third_week_as_int = int(third_week.strftime("%Y%m%d"))

    fourth_week = third_week + timedelta(6)
    fourth_week_as_int = int(fourth_week.strftime("%Y%m%d"))

    print("\n📅 ===== WEEKLY REPORT DEBUG =====")

    print(f"🟢 Today          : {today} ({today.strftime('%A')}) | int: {today_as_int}")

    print("\n📌 Batch Info")
    print(f"Start Date        : {start_as_formate.date()} | int: {start_as_int}")
    print(f"Deadline (days)   : {deadline}")

    print("\n📊 Week Boundaries")
    print(f"Week 1 End        : {first_week} | int: {first_week_as_int}")
    print(f"Week 2 End        : {second_week} | int: {second_week_as_int}")
    print(f"Week 2.5 (17d)    : {second_third_week_for_d_17} | int: {second_third_week_as_int}")
    print(f"Week 3 End        : {third_week} | int: {third_week_as_int}")
    print(f"Week 4 End        : {fourth_week} | int: {fourth_week_as_int}")

    print("=================================\n")

    if getstatus is None:
        print('no running batches')
        return ['no_batches_currently', '']
    elif getstatus[6] <= today_as_int <= getstatus[5]:  # 5 is deadline as whole numbers, 6 is project starts
        print('report is reco as project phase')

        if today == first_week:  # if starts 03-01 , then today == 03-07 is saturday
            print(f'worked week one, {first_week}')
            # 🔥 subtract 1 day
            end_date = first_week - timedelta(days=1)
            end_date_as_int = int(end_date.strftime("%Y%m%d"))

            report = await process_weekly_report(
                start_as_int,
                end_date_as_int
            )

            if report == 'no_records':
                await context.bot.send_message(
                    # chat_id=update.effective_chat.id,
                    chat_id=zero_dev_grp_id,
                    text="⚠️ No records for this week"
                )
                return 0
            await context.bot.send_message(
                chat_id=zero_dev_grp_id,
                text=report,
                parse_mode='HTML'
            )
            # get_ret = await  db_management.dbops('get_log_combined_for_week_update',
            #                                      [start_as_int, first_week_as_int, ''])
            # if not get_ret:
            #     return 'no_records'
            # else:
            #     # print(f'return logs :{get_ret}')
            #
            #     dev_stats = {}
            #
            #     for log in get_ret:
            #         date, points, tele_id, team_id, deadline, name, username = log
            #
            #         if tele_id not in dev_stats:
            #             dev_stats[tele_id] = {
            #                 'name': name,
            #                 'username': username,
            #                 'weekly_points': 0,
            #                 'active_days': set(),
            #                 'streak_point_earned': False
            #             }
            #
            #         # ✅ Add daily points
            #         dev_stats[tele_id]['weekly_points'] += points
            #         # ✅ Track unique active days
            #         dev_stats[tele_id]['active_days'].add(date)
            #
            #     for tele_id, dev in dev_stats.items():
            #
            #         dev_details = await db_management.dbops(
            #             'get_one_dev_details',
            #             [tele_id]
            #         )
            #
            #         if not dev_details[0]:
            #             continue
            #
            #         dev_data = dev_details[1][0]
            #
            #         weekly_streak = dev_data[10]  # your weekly streak column
            #
            #         bonus = 0
            #
            #         if weekly_streak >= 6:
            #             bonus = 2
            #             dev['streak_point_earned'] = True
            #
            #         total_week_points = dev['weekly_points'] + bonus
            #
            #         # ✅ Update DB (correct way)
            #         await db_management.dbops(
            #             'update_dev_points_and_cycle',
            #             [tele_id, total_week_points, bonus]
            #         )

        elif today == second_week:
            print(f'worked second, {second_week}')

            end_date = second_week - timedelta(days=1)
            end_date_as_int = int(end_date.strftime("%Y%m%d"))

            report = await process_weekly_report(
                first_week_as_int,
                end_date_as_int
            )

            if report == 'no_records':
                await context.bot.send_message(
                    # chat_id=update.effective_chat.id,
                    chat_id=zero_dev_grp_id,
                    text="⚠️ No records for this week"
                )
                return 0
            await context.bot.send_message(
                chat_id=zero_dev_grp_id,
                text=report,
                parse_mode='HTML'
            )

        elif today == second_third_week_for_d_17:  # for 17 days deadline devs only
            #  here send second_week , end as +4 from second week, so 5th day from 2nd week is elif need to work
            print(f'worked 3rd middle {second_third_week_for_d_17} ')
            end_date = second_third_week_for_d_17 - timedelta(days=1)
            end_date_as_int = int(end_date.strftime("%Y%m%d"))
            report = await process_weekly_report(
                first_week_as_int,
                end_date_as_int, True
            )
            if report == 'no_records':
                await context.bot.send_message(
                    # chat_id=update.effective_chat.id,
                    chat_id=zero_dev_grp_id,
                    text="⚠️ No activity recorded for developers under the 17-day deadline."
                )
                return 0
            await context.bot.send_message(
                chat_id=zero_dev_grp_id,
                text=report,
                parse_mode='HTML'
            )

        elif today == third_week:
            # here same like deadline = 17's third week : means: end as +4 and 5th day is send weekly report as replace that fourth_week
            print(f'worked 3rd pure sunday {third_week}')
            end_date = third_week - timedelta(days=1)
            end_date_as_int = int(end_date.strftime("%Y%m%d"))

            report = await process_weekly_report(
                second_week_as_int,
                end_date_as_int
            )
            if report == 'no_records':
                await context.bot.send_message(
                    # chat_id=update.effective_chat.id,
                    chat_id=zero_dev_grp_id,
                    text="⚠️ No records for this week"
                )
                return 0
            await context.bot.send_message(
                chat_id=zero_dev_grp_id,
                text=report,
                parse_mode='HTML'
            )

        elif today == fourth_week:
            end_date = fourth_week - timedelta(days=1)
            end_date_as_int = int(end_date.strftime("%Y%m%d"))
            # here same like deadline = 17's third week : means: end as +4 and 5th day is send weekly report as replace that fourth_week
            print(f'worked fourth sunday {fourth_week}')
            report = await process_weekly_report(
                third_week_as_int,
                end_date_as_int
            )
            if report == 'no_records':
                await context.bot.send_message(
                    # chat_id=update.effective_chat.id,
                    chat_id=zero_dev_grp_id,
                    text="⚠️ No records for this week"
                )
                return 0
            await context.bot.send_message(
                chat_id=zero_dev_grp_id,
                text=report,
                parse_mode='HTML'
            )

        else:
            print('not reco date')

        return ['during_project_phase', getstatus]
    else:
        print('not reco the date')
        return [None, '']


# [Done]
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
    yesterday_as_int = 20260422  # testing purpose
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

            # 🔹 Group data
            for log in daily_logs:
                activity_status = log[0]
                update_status = log[1]
                tele_id = log[2]
                tele_username = log[3]
                first_name = log[4]  # ✅ NEW
                team_name = log[5]  # ✅ FIXED
                team_deadline = log[6]
                point = log[9]  # ✅ FIXED

                grouped[team_deadline][team_name].append({
                    "tele_id": tele_id,
                    "name": log[4],  # full name
                    "activity": activity_status,
                    "update": update_status,
                    "point": log[9]
                })

            # 🔹 Build message
            message = "📊 <b>Daily Report</b>\n\n"

            for deadline in sorted(grouped.keys()):
                for team in grouped[deadline]:

                    # 🔥 Format date
                    formatted_deadline = f"{str(deadline)[:4]}-{str(deadline)[4:6]}-{str(deadline)[6:]}"

                    message += f"📌 <b>Team: {team}</b>\n"
                    message += f"⏰ Deadline: <b>{formatted_deadline}</b>\n\n"

                    for user in grouped[deadline][team]:
                        status = "✅" if user["update"] == 1 else "❌"

                        user_tag = f'<a href="tg://user?id={user["tele_id"]}">{user["name"]}</a>'

                        message += (
                            f"👤 {user_tag} | "
                            f"Update: {status} | "
                            f"Pts: {user['point']}\n"
                        )

                    message += "\n"
            # 🔹 Send once
            await context.bot.send_message(
                chat_id=zero_dev_grp_id,
                text=message,
                parse_mode="HTML"
            )

    else:
        print('msg not under any')


# [Done]
async def notify_devs_to_update(context: ContextTypes.DEFAULT_TYPE):
    getstatus = await  db_management.dbops('get_current_batch', '')
    print(f'batch: {type(getstatus[1])} {type(getstatus[0])}')
    print(f'\n BATCH: {getstatus}')
    today = datetime.now().date()
    today_as_int = int(today.strftime("%Y%m%d"))
    # today_as_int = 20260425

    if getstatus is None:
        print('no running batches')
    elif getstatus[6] <= today_as_int <= getstatus[5]:  # 5 is deadline as whole numbers
        print('its show tym')
        devs = await  db_management.dbops('get_missed_updates', [today_as_int])
        if devs:
            print('devs found')
            print(f'today {today_as_int} and to: {today}')
            mentions = helpers_py.build_mentions(devs)
            # print( f'{len(devs[0])} and length : {len(devs)} and type {type(mentions)}')
            if len(devs) == 1:
                print('worked solo')
                random_msg = helpers_py.get_random_alert_solo_msg()
            else:
                print('squad')
                random_msg = helpers_py.get_random_alert_team_msg()

            final_msg = f"{random_msg}\n{mentions}"

            await context.bot.send_message(
                chat_id=zero_dev_grp_id,
                text=final_msg,
                parse_mode="HTML"
            )
    else:
        print('msg not under any')
