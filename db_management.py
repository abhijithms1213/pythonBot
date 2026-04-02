import sqlite3
from datetime import datetime, timedelta
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import datetime as day


async def check_team_name_unique(args, cursor):
    team_name = args
    query = f'''
    select * from teams where team_name = '{team_name}';
    '''
    cursor.execute(query)
    result = cursor.fetchone()
    if result:
        return False
    else:
        return True


async def check_team_id_unique(args, cursor):
    team_id = args
    query = f'''
    select * from teams where team_id = {team_id};
    '''
    cursor.execute(query)
    result = cursor.fetchone()
    if result:
        return False
    else:
        return True


def check_team_under_batch(args, cursor):
    batch_id = int(args[0])
    user_id = str(args[1])
    # print(f'batch : {batch_id} and {user_id}')
    query = f'''
    select * from teams where batch_id = {batch_id} and devs_id = '{user_id}';
    '''
    # checks is user found in this batch
    cursor.execute(query)
    result = cursor.fetchall()
    # print(f'from raw user is :{result} and query: {query}')
    if result is None:
        return None
    else:
        return result


def check_any_batches_running(cursor):
    query = '''
    select * from batches where isCurrent = 1;
    '''
    cursor.execute(query)
    result = cursor.fetchall()
    print(f'from raw current batch result :{result}')
    if not result:
        return None
    else:
        return result[0]


def check_msg(msg_date, cursor):
    # msg_date=20260312
    getstatus = check_any_batches_running(cursor)
    print(f'status: {getstatus} and msg date: {msg_date}')
    if getstatus is None:
        print('no running batches')
        return ['no_batches_currently', '']
    if getstatus[0] <= msg_date and msg_date <= getstatus[1]:
        print('so its under the hood')
        return ['during_planning_phase', getstatus]

    elif getstatus[1] <= msg_date <= getstatus[5]:  # 5 is deadline as whole numbers
        print('its show tym')
        return ['during_project_phase', getstatus]
    elif msg_date > getstatus[5]:
        print('after deadline worked')
        # handle if result[4] is 1
        # check if dev extended already then ok to comment updates
        # else don't need to record add warning 'u didn't mention during project phase'
        return ['after_deadline', getstatus]
    else:
        print('msg not under any')
        return [None, '']


def addnewbatch(date, cursor):
    sanitizedDate = int(f'{date}'.replace('-', ''))
    status = check_msg(sanitizedDate, cursor)
    if status[0] == 'no_batches_currently':
        print(f'date is checking {sanitizedDate}\n')
        cursor.execute(f'''
       select * from batches ;
                       ''')
        # where Date_id = {sanitizedDate}
        output = cursor.fetchall()
        for row in output:
            print(f'each row 1st attr (Date_id): {row[0]}')
            # select Date_id from batches where Date_id = {sanitizedDate} OR isCurrent = 1
            if row[0] == sanitizedDate and row[2] == 1:
                #  but currently not active,
                cursor.execute(f'''
            select Date_id from batches where Date_id: {sanitizedDate};
                                 ''')
                output = cursor.fetchone()
                print(f'batch found in db:  {output[0]}')
                return 'running'
            else:
                continue

        plan_finish_date = 2
        deadline = 11

        batch_start = str(sanitizedDate)  # e.g. 20260327
        date_obj = datetime.strptime(batch_start, "%Y%m%d")

        # Step 1: batch finish date
        finish_date = date_obj + timedelta(days=plan_finish_date)
        finish_date_full = finish_date.strftime("%Y%m%d")

        # Step 2: deadline from finish date
        deadline_date = finish_date + timedelta(days=deadline)
        deadline_full = deadline_date.strftime("%Y%m%d")

        print(f"finish date full : {finish_date_full}")
        print(f"deadline full    : {deadline_full}")

        cursor.execute(f'''
        insert into batches (Date_id,Planning_Date,isCurrent,deadline,isExtended,deadline_as_date) values ({sanitizedDate},{finish_date_full},1,{deadline},0,{deadline_full}); 
                        ''')
        # 1 => currently running true , 14 => as default deadline, 0 => boolean that not Extending at initial so it's False
        cursor.execute('select * from batches;')
        output = cursor.fetchall()
        print(output)
        return 'added_new_batch'
    else:
        return 'running'


def clear_batch(cursor):
    query = '''
    delete from batches;
    '''
    cursor.execute(query)
    print('all clear')


# get user id by /join command
# +---------+-----------+-----------+------------+------------+---------+-------+-----+---------------+----------------+----------+------------+
# | tele_id | user_name | topic     | repository | isExtended | ExtDate | start | end | user_fullname | user_firstname | batch_id | tech_stack |
# +---------+-----------+-----------+------------+------------+---------+-------+-----+---------------+----------------+----------+------------+
# | 1       | jithu     | new topic | new_repo   | 0          | 12      | 10    | 20  | abhi          | jith           | 1        | <null>     |
# +---------+-----------+-----------+------------+------------+---------+-------+-----+---------------+----------------+----------+------------+

def add_new_user_to_db(args: list, cursor):
    user_id = args[0]
    user_name = args[1]
    user_fullname = args[2]
    user_first_name = args[3]
    query = f'''
    insert into devs values ('{user_id}','{user_name}','{user_fullname}','{user_first_name}',0,0);
    '''
    cursor.execute(query)
    query = f'''
        select tele_id,user_name,user_fullname,user_firstname from devs where tele_id = '{user_id}';
        '''
    cursor.execute(query)
    result = cursor.fetchone()
    print(f'result {result}')
    return True


async def check_is_user_already_present_and_update_if_yes(args, cursor):
    user_id = args[0]
    context: ContextTypes.DEFAULT_TYPE = args[1]
    chat_usr = await context.bot.get_chat(chat_id=user_id)
    first_name = chat_usr.first_name
    fullname = chat_usr.full_name
    user_name = chat_usr.username
    print(f'user id : {user_id} type:{type(user_id)} name is {user_name} , first: {first_name},full : {fullname}')
    included_username = f'@{user_name}'

    query = f'''
    select * from devs where tele_id = '{user_id}' or user_name = '{included_username}';
    '''
    cursor.execute(query)
    result = cursor.fetchone()

    print(f'result {result} and ')
    if not result:
        print('false as not found record so adding fresh user')
        return [False, '']
    else:
        if str(user_id) == result[0]:  # means same id so already registered
            print('record found returning')
            return ['exist', result]
        else:
            print('else working in /join command means different')
            query = f'''
                update devs set tele_id= '{user_id}',user_fullname = '{fullname}',user_firstname= '{first_name}' where user_name = '{included_username}';
            '''
            cursor.execute(query)
            query = f'''
                 select * from devs where user_name = '{included_username}';
            '''
            cursor.execute(query)

            # for add updated user_id to teams table
            query = f'''
               update teams set devs_id='{user_id}' where devs_id = ('{included_username}');
            '''
            print(f'query of team search {query}')
            cursor.execute(query)
            # +----------+----------+---------+--------------+------------+---------+----------+-----+------------------+--------+------------------------+---------------------------------+
            # | batch_id | team_id | devs_id      | isExtended | ExtDate | start    | end | deadline_as_date | streak | topic                  | repository                  | tech_stack   |
            # +----------+---------+--------------+------------+---------+----------+-----+------------------+--------+------------------------+-----------------------------+--------------+
            # | 20260329 | 90383   | @Jithuzz2255 | 0          | 0       | 20260401 | 21  | 20260421         | 0      | dbms management system | https://github.com/abhijith | @jithuzz2255 |
            # +----------+---------+--------------+------------+---------+----------+-----+------------------+--------+------------------------+-----------------------------+--------------+

            query = f'''
                select * from teams where devs_id = '{user_id}';
            '''
            cursor.execute(query)
            result_team = cursor.fetchone()

            result_teams = cursor.fetchone()
            print(f'resulted team {result_teams}')
            return ['updated_old', result_team, first_name]


async def add_dev_to_db(args, cursor):
    user_dictionary = args[1]
    context: ContextTypes.DEFAULT_TYPE = args[2]
    current_batch = args[3]

    # user details
    user_id = args[0]

    if not isinstance(user_id, str):
        chat_usr = await context.bot.get_chat(chat_id=user_id)
        first_name = chat_usr.first_name
        fullname = chat_usr.full_name
        user_name = chat_usr.username

    topic = user_dictionary['topic']
    deadline = user_dictionary['deadline']
    deadline_full = user_dictionary['deadline_full']
    github_repo = user_dictionary['github_repo']
    tech_stack = user_dictionary['tech']
    team_id = user_dictionary['team_id']
    #  add start end dates balance fields

    print(f'type of user id: {type(user_id)} and user id: is {user_id}')

    if isinstance(user_id, str) and user_id.startswith('@'):
        # checking in db is user exist
        print('inside if of @')
        # user_id_without_prefix=
        query = f'''
        select * from devs where user_name = '{user_id}';
        '''
        cursor.execute(query)
        result: list = cursor.fetchone()
        print(f'result {result}')
        if not result:
            print('inside if of @ and result [] not')
            # means not joined using /join so tell him to join but need to add date with user_id as user_name+batch abhi_20260228
            user_joined_name = f'{user_id}_{current_batch[0]}'
            query = f'''
            insert into devs (tele_id,user_name,user_fullname, user_firstname, batch_id, team_id)  values ('{user_joined_name}','{user_id}','','',{current_batch[0]},{team_id});
            '''
            cursor.execute(query)
            print('added this user but here means not joined using /join so tell him to join but recorded')
            return [1, user_id]
        else:
            print('inside else case of @')
            user_joined_name = f'{user_id}_{current_batch[0]}'
            # if joined from bot , the user we already filled with user_id , in else also filled with name+_batch_id
            original_user_id = result[0]
            if original_user_id == user_joined_name:  # it means that ['valid',]user didn't joined , after joining the current batch
                # but it's won't check because, if user already joined then in team check already return as invalid, so not even execute this fun()
                print('inside @ and equal names found @abc_24')
                print('found already in batch , also didnt updated details using /join after warnings')
                # here user didn't updated after warnings
                return [3, user_id]

                # return [3, result[1]]
            # elif means user didn't update while joining in second batch so names will diff: because of we completed id with batch_id so currently user have previous batch's id as 'tail'.
            # elif: original_user_id != user_joined_name: act as else (below)
            else:
                query = f'''
                         update devs set tele_id = '{user_joined_name}',batch_id = {current_batch[0]},team_id= {team_id} where user_name = '{user_id}';
                        '''
                cursor.execute(query)
                print(
                    'he already in our db with @abc_+ prev_batch_id so updated batch and new infos not even looking is filled other info about batch coz it doesnt matter')
                return [0, user_id]

    else:
        query = f'''
        select * from devs where tele_id = '{user_id}';
        '''
        cursor.execute(query)
        result: list = cursor.fetchone()
        print(f'result {result}')
        if not result:
            print('not found any records so add fresh')
            print(f"""
            user_id       : {user_id}
            user_name     : {user_name}
            topic         : {topic}
            github_repo   : {github_repo}
            current_batch : {current_batch}
            batch_id      : {current_batch[0]}
            deadline      : {deadline}
            fullname      : {fullname}
            first_name    : {first_name}
            tech_stack    : {tech_stack}
            """)
            query = f'''
            insert into devs ( tele_id, user_name, user_fullname, user_firstname, batch_id,team_id) values ('{user_id}','{user_name}','{fullname}','{first_name}',{current_batch[0]}, {team_id});
            '''
            cursor.execute(query)
            return [0, user_id]
        elif not result[5]:
            print(f'user already but new to this batch, and : result of team id : {result[5]}')
            # after 1st batches the team_id,batch_id will be cleared so it means , this user act old but ready to join to new (new to this batch)
            batch_id = int(current_batch[0])
            query = f'''
                update devs set batch_id = {batch_id}, team_id = {team_id} where tele_id='{user_id}';
            '''
            cursor.execute(query)
            return [0, user_id]
        else:
            # it won't work , coz in team already failed if found the document of this user in teams table
            print('found already in batch so not adding')
            return [2, user_id]
    # if result[0] is None:
    #     print('I found @ mention, and it must add through /join')
    #     return '@'


def add_to_team(args, cursor):
    # after bach team will be cleared
    team_id = args[0]
    team_name = args[7]
    batch_id = args[1]
    devs_id = args[2]
    deadline = args[3]
    deadline_full = args[4]
    start_date = args[5]
    project_infos = args[6]

    topic = project_infos['topic']
    github_repo = project_infos['github_repo']
    tech_stack = project_infos['tech']

    date_planning = str(start_date)  # e.g. 20260327
    date_obj = datetime.strptime(date_planning, "%Y%m%d")  # 2026-03-27
    date_after_planning = date_obj + timedelta(days=int(1))
    start = date_after_planning.strftime("%Y%m%d")  # 20260410

    print(f'devs ids passed to add team:{devs_id}')
    isBreaked = False
    imposter: str = ''
    for dev in devs_id:
        print(f'devs ids passed to add team:{type(dev)}')
        # circle through each dev's if any dev already joined in team we break entirely ,
        # because if a new user need to be added to this group we're already providing 'add' command
        query = f'''
            select * from teams where devs_id = '{dev}';
            '''
        cursor.execute(query)
        result: list = cursor.fetchone()
        print(f'result {result}')
        if result:
            isBreaked = True
            imposter = f'{dev}'
            break
        else:
            continue

    if isBreaked:  # it means any of the mention we found in already teamed,then entirely we ignore
        print('breaked because i found that dev already joined another team')
        isBreaked = False
        return [False, imposter]
    else:
        for dev in devs_id:
            query = f'''
            insert into teams (batch_id,team_id,devs_id,isExtended,ExtDate,start,end,deadline_as_date,topic,repository,tech_stack,team_name) values ({batch_id},{team_id},'{dev}',0,0,{start},{deadline},{deadline_full},'{topic}','{github_repo}','{tech_stack}','{team_name}');
            '''
            #  remove those fields from usr
            print(f'query while adding team {query}')
            cursor.execute(query)
            res = cursor.fetchall()
            print(f'result after adding in team {res}')

        return True
    # return True
    # else:
    #     return False


def daily_activity_record_check_record(args, cursor):
    user_id = str(args[0])
    msg_date = args[1]

    query = f'''
    select * from daily_logs where tele_id = '{user_id}' and Date = {msg_date};
    '''
    # checks is user found in this batch
    cursor.execute(query)
    result = cursor.fetchall()
    print(f'from raw user is :{result} and query: {query}')
    if result is None:
        return None
    else:
        return result


def update_deadline_of_batch(args, cursor):
    new_deadline = args[0]
    batch_after_planning = args[1]

    planning_date = str(batch_after_planning)  # e.g. 20260327
    date_obj = datetime.strptime(planning_date, "%Y%m%d")  # 2026-03-27

    deadline_date = date_obj + timedelta(days=int(new_deadline))
    deadline_full = deadline_date.strftime("%Y%m%d")  # 20260410

    db_query = f'''
    update batches set deadline={new_deadline} ,deadline_as_date = {deadline_full} where  isCurrent = 1;
    '''
    print(f'query : {db_query}')
    cursor.execute(db_query)
    query = '''
    select * from batches where isCurrent = 1;
    '''
    cursor.execute(query)
    result = cursor.fetchall()
    print(f'result of update deadline: {result}')
    # print(f'from raw user is :{result} and query: {db_query}')
    if result is None:
        return None
    else:
        return result[0][3] or new_deadline


async def check_is_user_already_exist_in_user_db(args, cursor):
    user_id = args
    query = f'''
    select * from devs where user_name = '{user_id}';
    '''

    cursor.execute(query)
    result = cursor.fetchall()
    print(f'user found {result} and query {query}  ')
    if not result:
        print('empty result not worked')
        return None
    # also check if start with @ if not then return that because maybe this field have @jithu_batch_no
    else:
        user_id_from_db: str = result[0]
        if user_id_from_db[0].isdigit():
            return result[0][0]
        else:
            return None


def add_daily_update_in_logs(args, cursor):
    msg_date = args[0]
    # msg_date = 20260401
    msg_content = args[3]
    # date_to_string = str(msg_date)
    # date_only = date_to_string[:10]
    # extracted = int(date_only.replace('-', ''))
    user_id = args[1]
    user_name = args[2]
    check_entry = args[4]

    # check already updated ?
    query = f'''
           select isUpdated from daily_logs where tele_id = {user_id} and Date = {msg_date};
       '''

    cursor.execute(query)
    result = cursor.fetchone()
    if not result[0] == 1:
        if check_entry == 0:
            query = f'''
            insert into daily_logs (Date,tele_id,isUpdated,Activity,MsgLen,UserName,UpdateText) values ({msg_date},'{user_id}',1,0,0,'{user_name}','{msg_content}');
            '''

            cursor.execute(query)
            result = cursor.fetchone()
            # if result[0] == 1:
            #     return True
            # else:
            #     return False
        else:
            query = f'''
                update daily_logs set isUpdated = 1,UpdateText= '{msg_content}' where  tele_id = {user_id} and Date = {msg_date};
            '''

            cursor.execute(query)
            query = f'''
                select isUpdated from daily_logs where tele_id = {user_id} and Date = {msg_date};
            '''

            cursor.execute(query)
            result = cursor.fetchone()

        print('now check the streak coz: isUpdate in both cases we made as: 1 ')

        # Streak Logic =========================================================

        query = f'''
                select Date,isUpdated from daily_logs where tele_id= {user_id} order by Date desc limit 2;
              '''
        # first will be today's , second is last updated means result[0] and [1]

        cursor.execute(query)
        result = cursor.fetchall()

        today_updation_status = result[0][1]
        last_updated_status = result[1][1]

        today_date = str(result[0][0])
        last_updation_day = str(result[1][0])

        today_formatted = day.datetime.strptime(today_date, "%Y%m%d")
        last_updation_day_formatted = day.datetime.strptime(last_updation_day, "%Y%m%d")

        yesterday = today_formatted - timedelta(days=1)

        # now check is yesterday is last updation day
        if yesterday == last_updation_day_formatted and last_updated_status == 1:

            query = f'''
                select streak from teams where devs_id = '{user_id}';
                '''
            cursor.execute(query)
            result = cursor.fetchone()
            print(f'streak count is {result}')
            streak_count_db = result[0]
            streak_count_db += 1

            query = f'''
               update teams set streak={streak_count_db} where devs_id = '{user_id}';
            '''
            cursor.execute(query)
            query = f'''
                select streak from teams where devs_id = '{user_id}';
                           '''
            cursor.execute(query)
            result = cursor.fetchone()
            print(f'after streak count is from db: {result}')

            return True
        else:
            print('add as "1" as streak ')
            query = f'''
                         update teams set streak=1 where devs_id = '{user_id}';
                      '''
            cursor.execute(query)
            query = f'''
                          select streak from teams where devs_id = '{user_id}';
                                     '''
            cursor.execute(query)
            result = cursor.fetchone()

            print(f'the last updated results: {result} ')
            return True
    else:
        print('already updated u before')
        return False


def add_activity_msg_first_entry_today(args, cursor):
    user_id = args[0]
    msg = args[1]
    user_name = args[3]

    msg_date = args[2]
    print(f'msg date in activity method: {msg_date}')
    # msg_date = 20260401
    # msg_date = '2026-04-01'
    date_to_string = str(msg_date)
    date_only = date_to_string[:10]
    extracted = int(date_only.replace('-', ''))
    msg_len = len(msg)
    check_entry = args[4]
    if check_entry == 0:
        if msg_len > 20:
            print('msg above 20')
            query = f'''
            insert into daily_logs (Date,tele_id,Activity,MsgLen,UserName) values ({extracted},'{user_id}',1,{msg_len},'{user_name}');
            '''

            cursor.execute(query)
            cursor.fetchall()
        else:
            print('msg len under 20')
            query = f'''
                 insert into daily_logs (Date,tele_id,Activity,MsgLen,UserName) values ({extracted},'{user_id}',0,{msg_len},'{user_name}');
                 '''

            cursor.execute(query)
            cursor.fetchall()
        return True
    else:
        # fetch already occuring MsgLength and sum up if sum > 20 then we will make Activity as 1 else only update msg length
        query = f'''
                  select Activity,MsgLen from daily_logs where tele_id = {user_id} and Date = {msg_date};
              '''

        cursor.execute(query)
        result = cursor.fetchone()
        print(f'result of after daily log: {result}')
        activity = result[0]
        msg_length_from_db = result[1]

        if not activity == 1:  # means not filled 20 length race
            msg_added_length = msg_length_from_db + msg_len  # adding length from db with current msg length
            if msg_added_length > 20:
                query = f'''
                    update daily_logs set Activity = 1,MsgLen= {msg_added_length} where tele_id = {user_id} and Date = {msg_date};
                '''

                cursor.execute(query)
                query = f'''
                    select Activity from daily_logs where tele_id = {user_id};
                '''
                cursor.execute(query)
                result = cursor.fetchone()
                if result[0] == 1:
                    return True
                else:
                    return False
            else:
                query = f'''
                               update daily_logs set MsgLen= {msg_added_length} where tele_id = {user_id} and Date = {msg_date};
                           '''

                cursor.execute(query)
                return True

        else:
            print('Activity is already True, u made it')
            return True


def streak_update(args, cursor):
    print('strk')


async def dbops(operation, args):
    try:
        connect = sqlite3.connect('zerodev.db')
        cursor = connect.cursor()
        if operation == 'clear_batch':  # for clearing db
            clear_batch(cursor)
        if operation == 'check_batch':
            return addnewbatch(args, cursor)
        if operation == 'get_current_batch':
            return check_any_batches_running(cursor)
        if operation == 'check_is_msg_under_planning_phase':
            return check_msg(args, cursor)
        # user join group related
        if operation == 'add_dev_to_db':  # used in that  msg_process method
            return await add_dev_to_db(args, cursor)
        if operation == 'check_is_user_already_present_and_update_if_yes':
            return await check_is_user_already_present_and_update_if_yes(args, cursor)
        if operation == 'check_is_user_already_exist_in_user_db':
            return await check_is_user_already_exist_in_user_db(args, cursor)
        if operation == 'add_new_user_to_db':  # while joining /join
            return add_new_user_to_db(args, cursor)
        if operation == 'update_deadline_of_batch':
            return update_deadline_of_batch(args, cursor)
        # ====================================
        if operation == 'add_to_team':
            return add_to_team(args, cursor)
        if operation == 'check_team_name_unique':
            return await check_team_name_unique(args, cursor)
        if operation == 'check_team_id_unique':
            return await check_team_id_unique(args, cursor)

        #  using some fun below for during project phase executions
        if operation == 'check_team_under_batch':
            return check_team_under_batch(args, cursor)
        if operation == 'daily_activity_record_check_record':
            return daily_activity_record_check_record(args, cursor)
        if operation == 'add_daily_update_in_logs':
            return add_daily_update_in_logs(args, cursor)
        if operation == 'add_activity_msg_first_entry_today':
            return add_activity_msg_first_entry_today(args, cursor)
        if operation == 'streak_update':
            return streak_update(args, cursor)

    except sqlite3.Error as error:
        print(f'error is : {error}')

    finally:
        if connect:
            connect.commit()
            connect.close()
            print('connection closed\n===========================================')


if __name__ == '__main__':
    dbops('clear_batch', '')

#  test query : update devs set topic='',repository=''  where tele_id='1054613006'; for already added in user list but new to batch
