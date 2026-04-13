import sqlite3

try:
    # db initialized
    conn = sqlite3.connect('zerodev.db')
    cursor = conn.cursor()
    print('db init')

    query = ' select * from batches'
    cursor.execute(query)
    result = cursor.fetchall()
    for row in result:
        print(f'te:{row[0]}, Planning: {row[1]},isPlanned: {row[2]}')
    cursor.close()

except sqlite3.Error as error:
    print(f'error is : {error}')

finally:
    if conn:
        conn.close()
        print('connection closedfrom test')