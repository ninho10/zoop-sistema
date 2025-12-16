import mysql.connector
from db import get_db_connection

def trigger_error():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Intentionally query wrong column
            cursor.execute("SELECT * FROM users WHERE approved = 1")
        except Exception as e:
            print(f"Caught exception type: {type(e)}")
            print(f"Exception message: {e}")
        finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    trigger_error()
