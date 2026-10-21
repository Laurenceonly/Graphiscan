"""Read-only legacy retirement inventory. Prints counts only, never identities/config."""
import json
from pathlib import Path
import sys

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import mysql.connector
from config import DB_CONFIG


def main():
    connection = None
    try:
        connection = mysql.connector.connect(**{**DB_CONFIG, 'connection_timeout': 4})
        connection.start_transaction(readonly=True)
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT role, COUNT(*) AS count FROM users GROUP BY role')
        roles = cursor.fetchall()
        cursor.execute('SELECT COUNT(*) AS count FROM students')
        students = cursor.fetchone()['count']
        # These are indicators for review, never authority to delete a record.
        cursor.execute("""SELECT COUNT(*) AS count FROM users WHERE
            LOWER(fullname) LIKE 'synthetic %' OR LOWER(fullname) LIKE 'browser synthetic %'
            OR LOWER(email) LIKE '%@example.invalid'""")
        synthetic = cursor.fetchone()['count']
        print(json.dumps({'connected': True, 'read_only': True, 'accounts_by_role': roles,
                          'students': students, 'synthetic_name_indicators': synthetic,
                          'database_writes': False, 'deletion_performed': False}))
        connection.rollback()
        return 0
    except mysql.connector.Error as error:
        print(json.dumps({'connected': False, 'error_number': error.errno,
                          'database_writes': False, 'deletion_performed': False}))
        return 1
    finally:
        if connection:
            connection.close()


if __name__ == '__main__':
    sys.exit(main())
