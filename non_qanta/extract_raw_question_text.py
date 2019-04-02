# Util function to get the raw text from all the questions
import sqlite3
from sqlite3 import Error
import json
 
def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
 
    return None
 
 
def print_answers(conn):
    cur = conn.cursor()
    # get raw questions text of all existing questions
    cur.execute("SELECT raw FROM text")
    rows = cur.fetchall()
    answers = [] 
    for row in rows:
        answers.append(row[0])
    with open('text.json','w') as outfile:
        json.dump(list(set(answers)), outfile) 

def main():
    database = "data/non_naqt.db"
    # create a database connection
    conn = create_connection(database)
    with conn:        
        print_answers(conn)
     
 
if __name__ == '__main__':
    main()
