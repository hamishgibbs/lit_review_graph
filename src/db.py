import sqlite3

def create_connection(db_file):
    """ create a database connection to the SQLite database specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)

    return None

def execute_sql(conn, sql, data=None):
    """ Execute a given SQL command with optional data """
    try:
        c = conn.cursor()
        if data:
            c.execute(sql, data)
        else:
            c.execute(sql)
        conn.commit()
    except sqlite3.Error as e:
        print(e)

def initialize_database():
    database = "path_to_your_database.db"

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

    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        execute_sql(conn, sql_create_bibliographies_table)
        execute_sql(conn, sql_create_dois_table)
    else:
        print("Error! Cannot create the database connection.")

    conn.close()

def create_bibliography(conn, name, mtime):
    sql = ''' INSERT INTO bibliographies(name, mtime) VALUES(?, ?) '''
    execute_sql(conn, sql, (name, mtime))

def delete_bibliography(conn, id):
    sql = ''' DELETE FROM bibliographies WHERE id = ? '''
    execute_sql(conn, sql, (id,))

def add_doi(conn, doi, bib_id):
    sql = ''' INSERT INTO dois(doi, bib_id) VALUES(?, ?) '''
    execute_sql(conn, sql, (doi, bib_id))

def delete_doi(conn, doi):
    sql = ''' DELETE FROM dois WHERE doi = ? '''
    execute_sql(conn, sql, (doi,))

def get_all_bibliographies(conn):
    sql = ''' SELECT * FROM bibliographies '''
    cur = conn.cursor()
    cur.execute(sql)
    return cur.fetchall()

def get_dois_for_bibliography(conn, bib_id):
    sql = ''' SELECT doi FROM dois WHERE bib_id = ? '''
    cur = conn.cursor()
    cur.execute(sql, (bib_id,))
    return cur.fetchall()