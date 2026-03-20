import sqlite3


def addnewbatch(date, cursor):
    sanitizedDate = f'{date}'.replace('-', '')
    print(f'add new batch called {sanitizedDate}')
    cursor.execute(f'''
   select * from batches where Date_id = {sanitizedDate} 
                   ''')
    output = cursor.fetchall()
    print(output)

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
            connect.close()
            print('connection closed')
