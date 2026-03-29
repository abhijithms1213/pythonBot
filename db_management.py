import sqlite3
from datetime import datetime, timedelta
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


def check_any_batches_running(cursor):
    query = '''
    select * from batches where isCurrent = 1;
    '''
    cursor.execute(query)
    result = cursor.fetchone()
    print(f'from raw current batch result :{result}')
    if result is []:
        return None
    else:
        # print(
        # f'found in db Data => date: {result[0]} , planning_phase: {result[1]} isCurrent: {result[2]} , batch-deadLine: {result[3]}')
        return result


def check_msg(msg_date, cursor):
    getstatus = check_any_batches_running(cursor)
    print(f'status: {getstatus} and msg date: {msg_date}')
    if getstatus is None:
        return ''
    if getstatus[0] >= msg_date <= getstatus[1]:
        print('so its under the hood')
        return 'during_planning_phase'
    elif getstatus[1] >= msg_date <= getstatus[5]:  # 5 is deadline as whole numbers
        print('its show tym')
        return 'during_project_phase'
    elif msg_date > getstatus[5]:
        print('after deadline worked')
        # handle if result[4] is 1
        # check if dev extended already then ok to comment updates
        # else don't need to record add warning 'u didn't mention during project phase'
        return 'after_deadline'
    return None


def addnewbatch(date, cursor):
    sanitizedDate = int(f'{date}'.replace('-', ''))
    status = check_msg(sanitizedDate, cursor)
    if status != '':
        print('currently running a batch')
        return 'running'

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
    deadline = 14

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
    insert into batches (Date_id,Planning_Date,isCurrent,deadline,isExtended,deadline_as_date) values ({sanitizedDate},{finish_date_full},1,14,0,{deadline_full}); 
                    ''')
    # 1 => currently running true , 14 => as default deadline, 0 => boolean that not Extending at initial so it's False
    cursor.execute('select * from batches;')
    output = cursor.fetchall()
    print(output)
    return 'added_new_batch'


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
    insert into devs values ('{user_id}','{user_name}','','',0,0,0,0,'{user_fullname}','{user_first_name}',0,'',0);
    '''
    cursor.execute(query)
    query = f'''
        select tele_id,user_name,user_fullname,user_firstname,topic,repository,isExtended,ExtDate,start,end from devs where tele_id = '{user_id}';
        '''
    cursor.execute(query)
    result = cursor.fetchone()
    print(f'result {result}')
    return True


async def check_is_user_already_present(args, cursor):
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
    result: list = cursor.fetchone()




    # query = f'''
    # select * from devs where user_name = '{included_username}';
    # '''
    # cursor.execute(query)
    # result: list = cursor.fetchone()
    print(f'result {result} and ')
    # print(f'result {result} and user id type: {type(result[0])} and id {result[0]}')
    if not result:
        print('false as not found record so adding fresh user')
        return [False,'']
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
            result: list = cursor.fetchone()
            print(f'result {result}')
            return ['updated_old', result]


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
            insert into devs (tele_id,user_name, topic, repository, isExtended, ExtDate, start, end, user_fullname, user_firstname, batch_id, tech_stack,deadline_as_date)  values ('{user_joined_name}','{user_id}','{topic}','{github_repo}',0,0,{current_batch[0]},{deadline},'','',{current_batch[0]}, '{tech_stack}',{deadline_full});
            '''
            cursor.execute(query)
            print('added this user but here means not joined using /join so tell him to join but recorded')
            return [1,user_id]
        else:
            print('inside else case of @')
            user_joined_name = f'{user_id}_{current_batch[0]}'
            # if joined from bot , the user we already filled with user_id , in else also filled with name+_batch_id
            original_user_id = result[0]
            if original_user_id == user_joined_name:  # it means that user didn't joined , after joining the current batch
                print('inside @ and equal names found @abc_24')
                print('user still didnt updated after my warning')
                return [3, result[1]]

            else:  # means user id exist
                if not result[2] and not result[3]:
                    print('inside @ and repository and topic found as empty')
                    query = f'''
                     update devs set topic = '{topic}',repository = '{github_repo}',start= {current_batch[0]},end = {deadline},batch_id = {current_batch[0]},tech_stack={tech_stack} ,deadline_as_date ={current_batch[5]} where tele_id = '{result[0]}';
                    '''
                    cursor.execute(query)
                    print('updated existing user in current batch')
                    return [1, result[0]]
                #  next setup returning each dev based on categorised for msging
                else:
                    print('inside @ and already u are in batch')
                    print('found already in batch so not adding')
                    return [2, result[0]]
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
            insert into devs ( tele_id, user_name, topic, repository, isExtended, ExtDate,start, end, user_fullname, user_firstname, batch_id, tech_stack,deadline_as_date) values ('{user_id}','{user_name}','{topic}','{github_repo}',0,0,{current_batch[0]},{deadline},'{fullname}','{first_name}',{current_batch[0]}, '{tech_stack}',{deadline_full});
            '''
            cursor.execute(query)
            return [0, user_id]
        else:
            print(f'under else : tpic: {result[2]} and {result[3]}')
            if not result[2] and not result[3]:
                print('2 and 3 are empty')
                # when finishing time we clear all the user's these project related fields (before clearing we move it to finished table)
                query = f'''
                     update devs set topic= '{topic}',repository = '{github_repo}',start= {current_batch[0]},end = {deadline},batch_id = {current_batch[0]},tech_stack='{tech_stack}',deadline_as_date ={current_batch[5]} where tele_id = '{user_id}';
                    '''
                cursor.execute(query)
                print('updated existing user in current batch')
                return [0, user_id]
            else:
                print('found already in batch so not adding')
                return [2, user_id]
    # if result[0] is None:
    #     print('I found @ mention, and it must add through /join')
    #     return '@'


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
        if operation == 'add_dev_to_db':
            return await add_dev_to_db(args, cursor)
        if operation == 'check_is_user_already_present':
            return await check_is_user_already_present(args, cursor)
        if operation == 'add_new_user_to_db':
            return add_new_user_to_db(args, cursor)

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
