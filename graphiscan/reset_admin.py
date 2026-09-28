import os
from dotenv import load_dotenv

from app import get_db_connection, hash_password

load_dotenv()
admin_email = os.getenv('GRAPHISCAN_ADMIN_EMAIL')
new_password = os.getenv('GRAPHISCAN_ADMIN_PASSWORD')
if not admin_email or not new_password:
    raise RuntimeError('Set GRAPHISCAN_ADMIN_EMAIL and GRAPHISCAN_ADMIN_PASSWORD in .env')

conn = get_db_connection()
cursor = conn.cursor()


cursor.execute("""
UPDATE users
SET password = %s
WHERE email = %s
""", (
    hash_password(new_password),
    admin_email
))

conn.commit()

print("Admin password has been reset.")

cursor.close()
conn.close()
