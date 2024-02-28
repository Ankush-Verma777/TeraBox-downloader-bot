import sqlite3
import threading
import logging

class SQLiteCustomDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.create_table_if_not_exists()

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA locking_mode = EXCLUSIVE;")
            self.conn.row_factory = sqlite3.Row
            self.db_lock = threading.Lock()
            return True
        except sqlite3.Error as e:
            logging.error(f"Error connecting to the database: {e}")
            return False

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None


    def create_table_if_not_exists(self):
        try:
            create_table_query = '''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                update_id INTEGER UNIQUE NOT NULL,
                chat_id INTEGER,
                main_message_id INTEGER,
                sub_message_id INTEGER,
                message_link TEXT,
                download_link TEXT,
                status INTEGER DEFAULT 0
            )
        '''
            self.execute_query(create_table_query)
        except Exception as e:
            logging.error(f"Error Occured Creating Table: {e}") 

    def execute_query(self, query, params=None):
        try:
            if not self.conn:
                self.connect()
            
            with self.db_lock:
                cursor = self.conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                self.conn.commit()
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error executing query: {e}")
        except Exception as e:
            logging.error(f"Error executing query: {e}")
        finally:
            self.disconnect()        
        return None