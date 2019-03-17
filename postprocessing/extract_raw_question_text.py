# Util function to get the raw text from all the questions. The raw text is then used in save_final_questions.py to remove duplicates from the questions.

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
  
def save_answers(conn):
    cur = conn.cursor()
    # get raw questions text of all existing questions
    cur.execute("SELECT raw FROM text")
    rows = cur.fetchall()
    answers = [] 
    for row in rows:
        answers.append(row[0])
    with open('raw_question_text.json','w') as outfile:
        json.dump(list(set(answers)), outfile) 

def main():
    database = "data/non_naqt.db"
    # create a database connection
    conn = create_connection(database)
    with conn:        
        save_answers(conn)
     
 
if __name__ == '__main__':
    main()
