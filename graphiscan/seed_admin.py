import os
from dotenv import load_dotenv
import mysql.connector
from werkzeug.security import generate_password_hash

from config import DB_CONFIG

load_dotenv()

PASSWORD_PEPPER = os.getenv("GRAPHISCAN_PASSWORD_PEPPER")

if not PASSWORD_PEPPER:
    raise RuntimeError("GRAPHISCAN_PASSWORD_PEPPER is missing from .env")

ADMIN_NAME = "GRAPHISCAN Admin"
ADMIN_EMAIL = os.getenv("GRAPHISCAN_ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("GRAPHISCAN_ADMIN_PASSWORD")

if not ADMIN_EMAIL or not ADMIN_PASSWORD:
    raise RuntimeError("Set GRAPHISCAN_ADMIN_EMAIL and GRAPHISCAN_ADMIN_PASSWORD in .env")

def pepper_password(password):
    return f"{password}{PASSWORD_PEPPER}"

def hash_password(password):
    return generate_password_hash(
        pepper_password(password),
        method="pbkdf2:sha256",
        salt_length=16
    )

connection = mysql.connector.connect(**DB_CONFIG)
cursor = connection.cursor()

hashed_password = hash_password(ADMIN_PASSWORD)

cursor.execute(
    """
    INSERT INTO users
    (fullname, email, password, role, contact_no, account_status, approved_by, approved_at)
    VALUES (%s, %s, %s, %s, %s, %s, NULL, NOW())
    ON DUPLICATE KEY UPDATE
        fullname = VALUES(fullname),
        password = VALUES(password),
        role = VALUES(role),
        contact_no = VALUES(contact_no),
        account_status = VALUES(account_status),
        approved_at = NOW()
    """,
    (
        ADMIN_NAME,
        ADMIN_EMAIL,
        hashed_password,
        "admin",
        "",
        "active"
    )
)

connection.commit()
cursor.close()
connection.close()

print("Admin account ready.")
print("Email:", ADMIN_EMAIL)
