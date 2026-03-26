import sqlite3


def check_any_batches_running(cursor):
    query = '''
    select * from batches where isCurrent = 1;
    '''
    cursor.execute(query)
    result = cursor.fetchone()
    print(f'from raw result :{result}')
    if result is []:
        return None
    else:
        # print(
        # f'found in db Data => date: {result[0]} , planning_phase: {result[1]} isCurrent: {result[2]} , batch-deadLine: {result[3]}')
        return result


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
        if row[0] == sanitizedDate or row[2] == 1:
            cursor.execute(f'''
        select Date_id from batches but currently not active,  Date_id: {sanitizedDate};
                             ''')
            output = cursor.fetchone()
            print(f'batch found in db:  {output[0]}')
            return 'running'
        else:
            continue

    plan_finish_date = sanitizedDate + 2
    cursor.execute(f'''
    insert into batches values ({sanitizedDate},{plan_finish_date},1,14,0); 
                    ''')
    # 1 => currently running true , 14 => as default deadline, 0 => boolean that not Extending at initial so it's False
    cursor.execute('select * from batches;')
    output = cursor.fetchall()
    print(output)
    return 'added_new_batch'


def check_msg(msg_date, cursor):
    getstatus = check_any_batches_running(cursor)
    print(f'status: {getstatus}')
    if getstatus is None:
        return ''
    deadline = getstatus[0] + getstatus[3]
    if getstatus[0] >= msg_date <= getstatus[1]:
        print('so its under the hood')
        return 'during_planning_phase'
    elif getstatus[1] >= msg_date <= deadline:
        print('its show tym')
        return 'during_project_phase'
    elif msg_date > deadline:
        print('after deadline worked')
        # handle if result[4] is 1
        # check if dev extended already then ok to comment updates
        # else don't need to record add warning 'u didn't mention during project phase'
        return 'after_deadline'


def clear_batch(cursor):
    query = '''
    delete from batches;
    '''
    cursor.execute(query)
    print('all clear')


def dbops(operation, args):
    try:
        connect = sqlite3.connect('zerodev.db')
        cursor = connect.cursor()
        if operation == 'clear_batch':  # for clearing db
            clear_batch(cursor)
        if operation == 'check_batch':
            return addnewbatch(args, cursor)
        if operation == 'check_is_msg_under_planning_phase':
            return check_msg(args, cursor)

    except sqlite3.Error as error:
        print(f'error is : {error}')

    finally:
        if connect:
            connect.commit()
            connect.close()
            print('connection closed\n===========================================')


if __name__ == '__main__':
    dbops('clear_batch', '')
