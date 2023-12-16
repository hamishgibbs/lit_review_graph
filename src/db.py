import pandas as pd
import sqlite3

def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)

    return None

def execute_sql(db_file, sql, data=None):
    conn = create_connection(db_file)
    try:
        c = conn.cursor()
        if data:
            c.execute(sql, data)
        else:
            c.execute(sql)
        conn.commit()
    except sqlite3.Error as e:
        print(e)
    
    conn.close()

def initialize_database(db_file):

    sql_create_bibliographies_table = """
    CREATE TABLE IF NOT EXISTS bibliographies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        mtime INTEGER
    ); """

    sql_create_dois_table = """
    CREATE TABLE IF NOT EXISTS dois (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doi TEXT NOT NULL,
        bib_id INTEGER NOT NULL,
        FOREIGN KEY (bib_id) REFERENCES bibliographies (id)
    ); """

    execute_sql(db_file, sql_create_bibliographies_table)
    execute_sql(db_file, sql_create_dois_table)


def create_bibliography(db_file, name, mtime):
    sql = ''' INSERT INTO bibliographies(name, mtime) VALUES(?, ?) '''
    execute_sql(db_file, sql, (name, mtime))

def delete_bibliography(db_file, id):
    sql = ''' DELETE FROM bibliographies WHERE id = ? '''
    execute_sql(db_file, sql, (id,))

def add_doi(db_file, doi, bib_id):
    sql = ''' INSERT INTO dois(doi, bib_id) VALUES(?, ?) '''
    execute_sql(db_file, sql, (doi, bib_id))

def delete_doi(db_file, doi):
    sql = ''' DELETE FROM dois WHERE doi = ? '''
    execute_sql(db_file, sql, (doi,))

def get_all_bibliographies(db_file):
    sql = ''' SELECT * FROM bibliographies '''
    conn = create_connection(db_file)
    cur = conn.cursor()
    cur.execute(sql)
    return cur.fetchall()

def get_dois_for_bibliography(db_file, bib_id):
    sql = ''' SELECT doi FROM dois WHERE bib_id = ? '''
    conn = create_connection(db_file)
    cur = conn.cursor()
    cur.execute(sql, (bib_id,))
    return cur.fetchall()