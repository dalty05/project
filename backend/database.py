# import sqlite3

# DATABASE = "events.db"

# def get_db_connection():
#     conn = sqlite3.connect(DATABASE)
#     conn.row_factory = sqlite3.Row
#     return conn


import sqlite3

def get_db_connection():
    # Use absolute path or relative path for the db file
    conn = sqlite3.connect("events.db")
    
    # This enables column access by name: row['title']
    conn.row_factory = sqlite3.Row 
    return conn