import mysql.connector
from db import get_db_connection

def inspect_schema():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DESCRIBE users")
            columns = cursor.fetchall()
            print("Columns in 'users' table:")
            for col in columns:
                print(col)
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    inspect_schema()
