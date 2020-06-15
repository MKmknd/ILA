import subprocess
import sqlite3
import sys

def read_issue_id_list(db_path):

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    issue_id_list = []
    command = """SELECT issue_id
                 FROM basic_fields;
                 """
    cur.execute(command)
    for row in cur.fetchall():
        issue_id_list.append(row[0])

    conn.close()
    return issue_id_list

if __name__=="__main__":
    print("TEST")
