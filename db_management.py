import sqlite3


def addnewbatch(date, cursor):
    sanitizedDate = int(f'{date}'.replace('-', ''))
    isfound = False
    print(f'date is checking {sanitizedDate}')
    cursor.execute(f'''
   select * from batches ;
                   ''')
    # where Date_id = {sanitizedDate}
    output = cursor.fetchall()
    for row in output:
        print(f'each row 1st attr: {row[0]}')
        if row[0] == sanitizedDate:
            cursor.execute(f'''
        select Date_id from batches where Date_id = {sanitizedDate} 
                             ''')
            output = cursor.fetchone()
            print(f'found in db {output}')
            isfound = True
        else:
            continue

    if not isfound:
        plan_finish_date = sanitizedDate + 2
        cursor.execute(f'''
        insert into batches values ({sanitizedDate},{plan_finish_date},0,0);
                    ''')
        cursor.execute('select * from batches;')
        output = cursor.fetchall()
        print(output)
    return None


def dbops(operation, args):
    try:
        connect = sqlite3.connect('zerodev.db')
        cursor = connect.cursor()
        if operation == 'check_batch':
            addnewbatch(args, cursor)

    except sqlite3.Error as error:
        print(f'error is : {error}')

    finally:
        if connect:
            connect.commit()
            connect.close()
            print('connection closed')
