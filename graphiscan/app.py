# =========================================================
# 01. IMPORTS
# =========================================================

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, g, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import os
import random
import secrets
import hashlib
import re
from functools import wraps
from dotenv import load_dotenv


from config import DB_CONFIG, SECRET_KEY
from predict import predict_handwriting

# =========================================================
# 02. LOAD ENVIRONMENT VARIABLES
# =========================================================
load_dotenv()
# =========================================================
# 02. APP CONFIGURATION
# =========================================================

app = Flask(__name__)

# Allows Vue admin web app to call Flask API routes.
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost",
            "capacitor://localhost",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://10.120.208.249:5173",
            "http://10.120.208.249:5174"
        ],
        "allow_headers": ["Content-Type", "Authorization"],
        "methods": ["GET", "POST", "OPTIONS"]
    }
})

app.secret_key = SECRET_KEY

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

from flask import request

@app.after_request
def add_mobile_cors_headers(response):
    origin = request.headers.get("Origin")
    
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"

    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Private-Network"] = "true"

    return response

# =========================================================
# PASSWORD PEPPER CONFIG
# Secret app-wide pepper loaded from .env
# =========================================================

PASSWORD_PEPPER = os.getenv("GRAPHISCAN_PASSWORD_PEPPER")

if not PASSWORD_PEPPER:
    raise RuntimeError("GRAPHISCAN_PASSWORD_PEPPER is missing from .env")

# Vue admin panel base URL.
# Old Flask admin routes will redirect here.
VUE_ADMIN_BASE_URL = "http://localhost:5173"
USER_APP_BASE_URL = "http://localhost:5174"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================================================
# ADMIN API TOKEN STORAGE
# Simple development token storage for Vue admin API access.
# Tokens reset when Flask restarts.
# =========================================================

ADMIN_TOKENS = {}
USER_TOKENS = {}


# =========================================================
# 03. HELPER FUNCTIONS
# =========================================================

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def log_action(user_id, action):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO audit_logs (user_id, action)
        VALUES (%s, %s)
    """, (user_id, action))

    conn.commit()
    cursor.close()
    conn.close()


def is_logged_in():
    return "user_id" in session


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def run_handwriting_screening(image_path, demo=False):
    """
    Runs the GRAPHISCAN binary model and returns normalized values
    used by the database, teacher app, guest demo, expert review,
    and parent result pages.
    """
    prediction_result = predict_handwriting(image_path)

    analysis_summary = prediction_result.get("analysis_summary", "")

    if demo:
        analysis_summary = (
            f"{analysis_summary} "
            "This is a demo screening result only and was not saved as an official student record."
        ).strip()

    return {
        "classification": prediction_result.get("classification", "Unclassified"),
        "dysgraphia_probability": prediction_result.get("dysgraphia_probability", 0),
        "confidence_score": prediction_result.get("confidence_score", 0),
        "analysis_summary": analysis_summary,
        "normal_probability": prediction_result.get("normal_probability", 0),
        "high_potential_probability": prediction_result.get("high_potential_probability", 0)
    }

def safe_date_string(value):
    if value:
        return str(value)

    return None


def build_image_url(image_path):
    if not image_path:
        return None

    clean_image_path = str(image_path).replace("\\", "/").lstrip("/")

    if clean_image_path.startswith("http://") or clean_image_path.startswith("https://"):
        return clean_image_path

    return f"{request.host_url.rstrip('/')}/{clean_image_path}"
# =========================================================
# AUTH SECURITY HELPERS
# Email validation, password rules, hash + salt + pepper
# =========================================================



def validate_email_format(email):
    if not email:
        return False

    email = email.strip().lower()

    pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$"
    return re.match(pattern, email) is not None


def validate_password_strength(password):
    errors = []

    if not password:
        errors.append("Password is required.")
        return errors

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")

    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")

    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")

    if not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one number.")

    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("Password must contain at least one symbol.")

    if password != password.strip():
        errors.append("Password must not start or end with spaces.")

    return errors


def pepper_password(password):
    return f"{password}{PASSWORD_PEPPER}"


def hash_password(password):
    return generate_password_hash(
        pepper_password(password),
        method="pbkdf2:sha256",
        salt_length=16
    )


def verify_password(stored_hash, password):
    """
    Returns:
    - is_valid
    - needs_upgrade

    needs_upgrade=True means the password matched the old non-peppered hash.
    We can re-save it using the new peppered hash after successful login.
    """

    if not stored_hash or not password:
        return False, False

    # New secure check: password + pepper
    if check_password_hash(stored_hash, pepper_password(password)):
        return True, False

    # Legacy check: old accounts before pepper was added
    if check_password_hash(stored_hash, password):
        return True, True

    return False, False


def hash_reset_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# =========================================================
# ADMIN API PROTECTION
# Protects /api/admin routes from direct unauthorized access.
# =========================================================

def require_admin_api(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({
                "success": False,
                "message": "Missing admin authorization token."
            }), 401

        token = auth_header.replace("Bearer ", "").strip()
        admin_user = ADMIN_TOKENS.get(token)

        if not admin_user:
            return jsonify({
                "success": False,
                "message": "Invalid or expired admin token."
            }), 401

        if admin_user.get("role") != "admin":
            return jsonify({
                "success": False,
                "message": "Admin access required."
            }), 403

        g.current_admin = admin_user

        return route_function(*args, **kwargs)



    return wrapper

# =========================================================
# USER APP API PROTECTION
# Protects Teacher / Parent / Expert mobile app API routes
# =========================================================

def require_user_api(allowed_roles=None):
    def decorator(route_function):
        @wraps(route_function)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")

            if not auth_header.startswith("Bearer "):
                return jsonify({
                    "success": False,
                    "message": "Missing user authorization token."
                }), 401

            token = auth_header.replace("Bearer ", "").strip()
            token_user = USER_TOKENS.get(token)

            if not token_user:
                return jsonify({
                    "success": False,
                    "message": "Invalid or expired user token."
                }), 401

            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            try:
                cursor.execute("""
                    SELECT 
                        user_id,
                        fullname,
                        email,
                        role,
                        account_status
                    FROM users
                    WHERE user_id = %s
                    LIMIT 1
                """, (token_user["user_id"],))

                fresh_user = cursor.fetchone()

            finally:
                cursor.close()
                conn.close()

            if not fresh_user:
                USER_TOKENS.pop(token, None)

                return jsonify({
                    "success": False,
                    "message": "Your account session is no longer valid. Please log in again."
                }), 401

            account_status = fresh_user.get("account_status", "active")

            if account_status != "active":
                USER_TOKENS.pop(token, None)

                return jsonify({
                    "success": False,
                    "message": "Your account is no longer active. Please contact the administrator.",
                    "account_status": account_status
                }), 403

            if allowed_roles and fresh_user.get("role") not in allowed_roles:
                return jsonify({
                    "success": False,
                    "message": "Access denied for this role."
                }), 403

            USER_TOKENS[token] = {
                "user_id": fresh_user["user_id"],
                "fullname": fresh_user["fullname"],
                "email": fresh_user["email"],
                "role": fresh_user["role"],
                "account_status": account_status
            }

            g.current_user = USER_TOKENS[token]

            return route_function(*args, **kwargs)

        return wrapper

    return decorator

# =========================================================
# 04. PUBLIC ROUTES
# =========================================================

@app.route("/")
def home():
    return render_template("home.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    flash("Accounts are created by a GraphiScan administrator or researcher.", "info")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Flask/Jinja login is kept only for old pages.
    New admin-web and user-app should use their Vue login screens.
    """
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        if not validate_email_format(email):
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        is_valid_password, needs_upgrade = verify_password(user["password"], password)

        if not is_valid_password:
            cursor.close()
            conn.close()
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        account_status = user.get("account_status", "active")

        if account_status == "pending":
            cursor.close()
            conn.close()
            flash("Your account is awaiting approval.", "danger")
            return render_template("login.html")

        if account_status in ["rejected", "disabled"]:
            cursor.close()
            conn.close()
            flash("Your account is not available. Please contact the administrator.", "danger")
            return render_template("login.html")

        if needs_upgrade:
            upgraded_hash = hash_password(password)

            cursor.execute("""
                UPDATE users
                SET password = %s
                WHERE user_id = %s
            """, (upgraded_hash, user["user_id"]))

            conn.commit()

        cursor.close()
        conn.close()

        session["user_id"] = user["user_id"]
        session["fullname"] = user["fullname"]
        session["role"] = user["role"]

        log_action(user["user_id"], "User logged in")

        flash("Login successful.", "success")

        if user["role"] == "admin":
            return redirect(f"{VUE_ADMIN_BASE_URL}/login")
        elif user["role"] == "teacher":
            return redirect(url_for("teacher_dashboard"))
        elif user["role"] == "expert":
            return redirect(url_for("expert_dashboard"))
        elif user["role"] == "parent":
            return redirect(url_for("parent_dashboard"))
        elif user["role"] == "guest":
            flash("Guest accounts should use the GRAPHISCAN app login.", "info")
            return redirect(url_for("login"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")

# =========================================================
# 05. VUE ADMIN AUTH API
# =========================================================


@app.route("/api/admin/login", methods=["POST"])
def api_admin_login():
    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400

    if not validate_email_format(email):
        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    is_valid_password, needs_upgrade = verify_password(user["password"], password)

    if not is_valid_password:
        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    if user["role"] != "admin":
        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    account_status = user.get("account_status", "active")

    if account_status != "active":
        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Your account is not available. Please contact the administrator."
        }), 403

    if needs_upgrade:
        upgraded_hash = hash_password(password)

        cursor.execute("""
            UPDATE users
            SET password = %s
            WHERE user_id = %s
        """, (upgraded_hash, user["user_id"]))

        conn.commit()

    admin_token = secrets.token_urlsafe(32)

    ADMIN_TOKENS[admin_token] = {
        "user_id": user["user_id"],
        "fullname": user["fullname"],
        "email": user["email"],
        "role": user["role"]
    }

    log_action(user["user_id"], "Admin logged in through Vue web app")

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "token": admin_token,
        "user": {
            "user_id": user["user_id"],
            "fullname": user["fullname"],
            "email": user["email"],
            "role": user["role"]
        }
    })

# =========================================================
# VUE ADMIN LOGOUT API
# Records admin logout in audit logs and removes admin token.
# =========================================================

@app.route("/api/admin/logout", methods=["POST"])
@require_admin_api
def api_admin_logout():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()

    admin_id = g.current_admin["user_id"]

    log_action(admin_id, "Admin logged out from Vue web app")

    if token in ADMIN_TOKENS:
        del ADMIN_TOKENS[token]

    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    })

    # =========================================================
# ADMIN CHANGE PASSWORD API
# Allows logged-in admin to change password securely.
# Requires current password and logs action in audit logs.
# =========================================================

@app.route("/api/admin/change-password", methods=["POST"])
@require_admin_api
def api_admin_change_password():
    data = request.get_json() or {}

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    confirm_password = data.get("confirm_password", "")

    admin_id = g.current_admin["user_id"]

    if not current_password or not new_password or not confirm_password:
        return jsonify({
            "success": False,
            "message": "Please complete all password fields."
        }), 400

    if new_password != confirm_password:
        return jsonify({
            "success": False,
            "message": "New passwords do not match."
        }), 400

    if current_password == new_password:
        return jsonify({
            "success": False,
            "message": "New password must be different from your current password."
        }), 400

    password_errors = validate_password_strength(new_password)

    if password_errors:
        return jsonify({
            "success": False,
            "message": password_errors[0]
        }), 400

    auth_header = request.headers.get("Authorization", "")
    current_token = auth_header.replace("Bearer ", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT user_id, password, role, account_status
            FROM users
            WHERE user_id = %s
            AND role = 'admin'
            LIMIT 1
        """, (admin_id,))

        admin_user = cursor.fetchone()

        if not admin_user:
            return jsonify({
                "success": False,
                "message": "Admin account not found."
            }), 404

        if admin_user["account_status"] != "active":
            return jsonify({
                "success": False,
                "message": "Your admin account is not active."
            }), 403

        is_valid_password, needs_upgrade = verify_password(
            admin_user["password"],
            current_password
        )

        if not is_valid_password:
            return jsonify({
                "success": False,
                "message": "Current password is incorrect."
            }), 403

        new_hashed_password = hash_password(new_password)

        cursor.execute("""
            UPDATE users
            SET password = %s
            WHERE user_id = %s
        """, (new_hashed_password, admin_id))

        conn.commit()

        log_action(admin_id, "Admin changed account password")

        # Invalidate this admin's active admin tokens after password change.
        tokens_to_remove = []

        for token, token_user in ADMIN_TOKENS.items():
            if token_user.get("user_id") == admin_id:
                tokens_to_remove.append(token)

        for token in tokens_to_remove:
            ADMIN_TOKENS.pop(token, None)

        return jsonify({
            "success": True,
            "message": "Password changed successfully. Please log in again."
        })

    except mysql.connector.Error as error:
        conn.rollback()

        print("ADMIN CHANGE PASSWORD ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Unable to change password. Please try again."
        }), 400

    finally:
        cursor.close()
        conn.close()
# =========================================================
# USER APP AUTH API
# Used by the Teacher / Parent / Expert mobile app
# =========================================================


@app.route("/api/user/login", methods=["POST"])
def api_user_login():
    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400

    if not validate_email_format(email):
        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    is_valid_password, needs_upgrade = verify_password(user["password"], password)

    if not is_valid_password:
        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    if user["role"] not in ["teacher", "parent", "expert", "guest"]:
        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    account_status = user.get("account_status", "active")

    if account_status == "pending":
        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Your account is awaiting approval."
        }), 403

    if account_status in ["rejected", "disabled"]:
        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Your account is not available. Please contact the administrator."
        }), 403

    if needs_upgrade:
        upgraded_hash = hash_password(password)

        cursor.execute("""
            UPDATE users
            SET password = %s
            WHERE user_id = %s
        """, (upgraded_hash, user["user_id"]))

        conn.commit()

    user_token = secrets.token_urlsafe(32)

    USER_TOKENS[user_token] = {
        "user_id": user["user_id"],
        "fullname": user["fullname"],
        "email": user["email"],
        "role": user["role"]
    }

    log_action(user["user_id"], f"{user['role'].title()} logged in through user app")

    redirect_path = "/login"

    if user["role"] == "teacher":
        redirect_path = "/teacher/dashboard"
    elif user["role"] == "parent":
        redirect_path = "/parent/dashboard"
    elif user["role"] == "expert":
        redirect_path = "/expert/dashboard"
    elif user["role"] == "guest":
        redirect_path = "/guest/dashboard"

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "token": user_token,
        "redirect_path": redirect_path,
        "user": {
            "user_id": user["user_id"],
            "fullname": user["fullname"],
            "email": user["email"],
            "role": user["role"],
            "account_status": account_status
        }
    })


@app.route("/api/user/register", methods=["POST"])
def api_user_register():
    return jsonify({
        "success": False,
        "message": "Accounts are created by a GraphiScan administrator or researcher."
    }), 403

# =========================================================
# USER APP CURRENT SESSION API
# Checks if the logged-in user token is still valid and active.
# =========================================================

@app.route("/api/user/me", methods=["GET"])
@require_user_api()
def api_user_me():
    user = g.current_user

    redirect_path = "/login"

    if user["role"] == "teacher":
        redirect_path = "/teacher/dashboard"
    elif user["role"] == "parent":
        redirect_path = "/parent/dashboard"
    elif user["role"] == "expert":
        redirect_path = "/expert/dashboard"
    elif user["role"] == "guest":
        redirect_path = "/guest/dashboard"

    return jsonify({
        "success": True,
        "message": "User session is active.",
        "redirect_path": redirect_path,
        "user": {
            "user_id": user["user_id"],
            "fullname": user["fullname"],
            "email": user["email"],
            "role": user["role"],
            "account_status": user.get("account_status", "active")
        }
    })

    # =========================================================
# USER APP LOGOUT API
# Records user logout in audit logs and removes user token.
# =========================================================

@app.route("/api/user/logout", methods=["POST"])
@require_user_api()
def api_user_logout():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()

    user = g.current_user
    user_id = user["user_id"]
    role = user["role"]

    log_action(user_id, f"{role.title()} logged out from user app")

    if token in USER_TOKENS:
        del USER_TOKENS[token]

    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    })

        # =========================================================
# USER APP FORGOT PASSWORD API
# Creates a one-time password reset token
# =========================================================

@app.route("/api/user/forgot-password", methods=["POST"])
def api_user_forgot_password():
    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()

    safe_message = "If this email is registered, password reset instructions will be sent."

    if not email or not validate_email_format(email):
        return jsonify({
            "success": True,
            "message": safe_message
        })

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT user_id, email, role, account_status
            FROM users
            WHERE email = %s
            LIMIT 1
        """, (email,))

        user = cursor.fetchone()

        if user:
            raw_token = secrets.token_urlsafe(48)
            token_hash = hash_reset_token(raw_token)

            cursor.execute("""
                UPDATE password_reset_tokens
                SET used_at = NOW()
                WHERE user_id = %s
                AND used_at IS NULL
            """, (user["user_id"],))

            cursor.execute("""
                INSERT INTO password_reset_tokens
                (user_id, token_hash, expires_at)
                VALUES (%s, %s, DATE_ADD(NOW(), INTERVAL 30 MINUTE))
            """, (user["user_id"], token_hash))

            conn.commit()

            reset_link = f"{USER_APP_BASE_URL}/reset-password?token={raw_token}"

            print("\n=================================================")
            print("GRAPHISCAN PASSWORD RESET LINK")
            print(reset_link)
            print("This link expires in 30 minutes.")
            print("=================================================\n")

            log_action(user["user_id"], "Password reset requested")

        return jsonify({
            "success": True,
            "message": safe_message
        })

    except mysql.connector.Error:
        return jsonify({
            "success": True,
            "message": safe_message
        })

    finally:
        cursor.close()
        conn.close()


# =========================================================
# USER APP RESET PASSWORD API
# Validates reset token and updates password using hash + salt + pepper
# =========================================================

@app.route("/api/user/reset-password", methods=["POST"])
def api_user_reset_password():
    data = request.get_json() or {}

    token = data.get("token", "").strip()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    if not token or not password or not confirm_password:
        return jsonify({
            "success": False,
            "message": "Please complete all required fields."
        }), 400

    if password != confirm_password:
        return jsonify({
            "success": False,
            "message": "Passwords do not match."
        }), 400

    password_errors = validate_password_strength(password)

    if password_errors:
        return jsonify({
            "success": False,
            "message": password_errors[0]
        }), 400

    token_hash = hash_reset_token(token)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT 
                pr.reset_id,
                pr.user_id,
                pr.expires_at,
                pr.used_at,
                u.email,
                u.role
            FROM password_reset_tokens pr
            JOIN users u ON pr.user_id = u.user_id
            WHERE pr.token_hash = %s
            AND pr.used_at IS NULL
            AND pr.expires_at > NOW()
            LIMIT 1
        """, (token_hash,))

        reset_record = cursor.fetchone()

        if not reset_record:
            return jsonify({
                "success": False,
                "message": "Invalid or expired reset link."
            }), 400

        new_hashed_password = hash_password(password)

        cursor.execute("""
            UPDATE users
            SET password = %s
            WHERE user_id = %s
        """, (new_hashed_password, reset_record["user_id"]))

        cursor.execute("""
            UPDATE password_reset_tokens
            SET used_at = NOW()
            WHERE reset_id = %s
        """, (reset_record["reset_id"],))

        conn.commit()

        log_action(reset_record["user_id"], "Password was reset successfully")

        return jsonify({
            "success": True,
            "message": "Password reset successfully. You may now log in."
        })

    except mysql.connector.Error as error:
        print("PASSWORD RESET ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Unable to reset password. Please try again."
        }), 400

    finally:
        cursor.close()
        conn.close()

@app.route("/api/user/results/<int:result_id>/download-image", methods=["GET"])
@require_user_api(["teacher", "parent", "expert"])
def api_user_download_result_image(result_id):
    user = g.current_user
    user_id = user["user_id"]
    role = user["role"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if role == "teacher":
        cursor.execute("""
            SELECT hs.image_path
            FROM results r
            JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
            WHERE r.result_id = %s
            AND hs.teacher_id = %s
            LIMIT 1
        """, (result_id, user_id))

    elif role == "parent":
        cursor.execute("""
            SELECT hs.image_path
            FROM results r
            JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
            JOIN students s ON hs.student_id = s.student_id
            JOIN validations v ON r.result_id = v.result_id
            WHERE r.result_id = %s
            AND s.parent_id = %s
            AND v.validation_status = 'Validated'
            LIMIT 1
        """, (result_id, user_id))

    else:
        cursor.execute("""
            SELECT hs.image_path
            FROM results r
            JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
            WHERE r.result_id = %s
            LIMIT 1
        """, (result_id,))

    record = cursor.fetchone()

    cursor.close()
    conn.close()

    if not record or not record.get("image_path"):
        return jsonify({
            "success": False,
            "message": "Image not found."
        }), 404

    image_path = str(record["image_path"]).replace("\\", "/")

    if os.path.isabs(image_path):
        absolute_path = image_path
    else:
        absolute_path = os.path.join(os.getcwd(), image_path)

    if not os.path.exists(absolute_path):
        return jsonify({
            "success": False,
            "message": "Image file is missing from the server."
        }), 404

    filename = os.path.basename(absolute_path)

    return send_file(
        absolute_path,
        as_attachment=True,
        download_name=filename
    )

# =========================================================
# TEACHER APP API - STUDENT LIST
# Used by user-app teacher student page
# =========================================================

@app.route("/api/user/teacher/students", methods=["GET"])
@require_user_api(["teacher"])
def api_teacher_students():
    teacher_id = g.current_user["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            s.student_id,
            s.fullname,
            s.age,
            s.grade_level,
            s.created_at,
            u.fullname AS parent_name
        FROM students s
        LEFT JOIN users u ON s.parent_id = u.user_id
        WHERE s.teacher_id = %s
        ORDER BY s.created_at DESC
    """, (teacher_id,))

    students = cursor.fetchall()

    cursor.close()
    conn.close()

    for student in students:
        if student["created_at"]:
            student["created_at"] = str(student["created_at"])

        if student["parent_name"] is None:
            student["parent_name"] = "Not assigned"

    return jsonify({
        "success": True,
        "students": students,
        "total_students": len(students)
    })

# =========================================================
# TEACHER APP API - PARENT LIST
# Used by Add Student page for parent/guardian dropdown
# =========================================================

@app.route("/api/user/teacher/parents", methods=["GET"])
@require_user_api(["teacher"])
def api_teacher_parents():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            user_id,
            fullname,
            email
        FROM users
        WHERE role = 'parent'
        AND account_status = 'active'
        ORDER BY fullname ASC
    """)

    parents = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "parents": parents
    })

    # =========================================================
# TEACHER APP API - ADD STUDENT
# Allows teacher to create a student record from user-app
# =========================================================

@app.route("/api/user/teacher/students/add", methods=["POST"])
@require_user_api(["teacher"])
def api_teacher_add_student():
    teacher_id = g.current_user["user_id"]
    data = request.get_json()

    fullname = data.get("fullname")
    age = data.get("age")
    grade_level = data.get("grade_level")
    parent_id = data.get("parent_id")

    if not fullname or not age or not grade_level:
        return jsonify({
            "success": False,
            "message": "Full name, age, and grade level are required."
        }), 400

    if parent_id == "" or parent_id is None:
        parent_id = None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if parent_id:
        cursor.execute("""
            SELECT user_id
            FROM users
            WHERE user_id = %s AND role = 'parent'
        """, (parent_id,))

        parent = cursor.fetchone()

        if not parent:
            cursor.close()
            conn.close()

            return jsonify({
                "success": False,
                "message": "Selected parent account was not found."
            }), 404

    cursor.execute("""
        INSERT INTO students (fullname, age, grade_level, parent_id, teacher_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (fullname, age, grade_level, parent_id, teacher_id))

    conn.commit()

    log_action(teacher_id, f"Added student record through user app: {fullname}")

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Student added successfully."
    })

    # =========================================================
# TEACHER APP API - UPLOAD HANDWRITING SAMPLE
# Allows teacher to upload handwriting image and generate AI result
# =========================================================

@app.route("/api/user/teacher/upload", methods=["POST"])
@require_user_api(["teacher"])
def api_teacher_upload_sample():
    teacher_id = g.current_user["user_id"]

    student_id = request.form.get("student_id")
    file = request.files.get("handwriting_image")

    if not student_id:
        return jsonify({
            "success": False,
            "message": "Please select a student."
        }), 400

    if not file or file.filename == "":
        return jsonify({
            "success": False,
            "message": "Please select a handwriting image."
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "message": "Invalid file type. Please upload JPG, JPEG, or PNG only."
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT student_id
        FROM students
        WHERE student_id = %s AND teacher_id = %s
    """, (student_id, teacher_id))

    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Selected student was not found under your account."
        }), 404

    filename = secure_filename(file.filename)
    unique_filename = f"{teacher_id}_{student_id}_{random.randint(1000, 9999)}_{filename}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)

    try:
        file.save(filepath)
        screening_result = run_handwriting_screening(filepath)

    except Exception as err:
        print("Teacher upload screening error:", err)

        cursor.close()
        conn.close()

        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as cleanup_error:
                print("Unable to remove failed upload file:", cleanup_error)

        return jsonify({
            "success": False,
            "message": "Unable to process handwriting screening. Please try again."
        }), 500

    classification = screening_result["classification"]
    dysgraphia_probability = screening_result["dysgraphia_probability"]
    confidence_score = screening_result["confidence_score"]
    analysis_summary = screening_result["analysis_summary"]

    cursor.execute("""
        INSERT INTO handwriting_samples (student_id, teacher_id, image_path)
        VALUES (%s, %s, %s)
    """, (student_id, teacher_id, filepath))

    sample_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO results 
        (sample_id, dysgraphia_probability, classification, confidence_score, analysis_summary, recommendation)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        sample_id,
        dysgraphia_probability,
        classification,
        confidence_score,
        analysis_summary,
        ""
    ))

    result_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO validations (result_id, validation_status)
        VALUES (%s, 'Pending')
    """, (result_id,))

    cursor.execute("SELECT COUNT(*) FROM reports WHERE student_id = %s", (student_id,))
    report_type = "Follow-up Screening" if cursor.fetchone()[0] else "Initial Screening"
    cursor.execute("""
        INSERT INTO reports (student_id, result_id, report_type, report_status)
        VALUES (%s, %s, %s, 'Generated')
    """, (student_id, result_id, report_type))

    conn.commit()

    log_action(
        teacher_id,
        f"Uploaded handwriting sample through user app and generated result ID {result_id}"
    )

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Handwriting sample uploaded and screened successfully.",
        "result_id": result_id,
        "classification": classification,
        "confidence_score": confidence_score,
        "dysgraphia_probability": dysgraphia_probability
    })

    # =========================================================
# TEACHER APP API - RESULT HISTORY
# Shows screening results generated by the logged-in teacher
# =========================================================

@app.route("/api/user/teacher/results", methods=["GET"])
@require_user_api(["teacher"])
def api_teacher_results():
    teacher_id = g.current_user["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            r.result_id,
            r.classification,
            r.dysgraphia_probability,
            r.confidence_score,
            r.date_generated,
            s.fullname AS student_name,
            s.grade_level,
            v.validation_status
        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        JOIN students s ON hs.student_id = s.student_id
        LEFT JOIN validations v ON r.result_id = v.result_id
        WHERE hs.teacher_id = %s
        ORDER BY r.date_generated DESC
    """, (teacher_id,))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    for result in results:
        if result["date_generated"]:
            result["date_generated"] = str(result["date_generated"])

        if result["validation_status"] is None:
            result["validation_status"] = "Pending"

    return jsonify({
        "success": True,
        "results": results,
        "total_results": len(results)
    })


 ##### Teacher Child Progress API

@app.route("/api/user/teacher/students/<int:student_id>/progress", methods=["GET"])
@require_user_api(["teacher"])
def api_teacher_student_progress(student_id):
    teacher_id = g.current_user["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.student_id,
            s.fullname,
            s.age,
            s.grade_level,
            parent.fullname AS parent_name
        FROM students s
        LEFT JOIN users parent ON s.parent_id = parent.user_id
        WHERE s.student_id = %s
        AND s.teacher_id = %s
    """, (student_id, teacher_id))

    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Student not found or access denied."
        }), 404

    cursor.execute("""
        SELECT
            r.result_id,
            r.dysgraphia_probability,
            r.classification,
            r.confidence_score,
            r.date_generated,
            COALESCE(v.validation_status, 'Pending') AS validation_status,
            COALESCE(v.remarks, '') AS remarks,
            COALESCE(v.expert_recommendation, '') AS expert_recommendation,
            COALESCE(v.follow_up_needed, 'No') AS follow_up_needed,
            expert.fullname AS expert_name
        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        LEFT JOIN validations v ON r.result_id = v.result_id
        LEFT JOIN users expert ON v.expert_id = expert.user_id
        WHERE hs.student_id = %s
        AND hs.teacher_id = %s
        ORDER BY r.date_generated ASC
    """, (student_id, teacher_id))

    progress = cursor.fetchall()

    cursor.close()
    conn.close()

    for item in progress:
        if item["date_generated"]:
            item["date_generated"] = str(item["date_generated"])

    latest_result = progress[-1] if progress else None
    summary = {
        "total_screenings": len(progress),
        "latest_result": latest_result
    }
    return jsonify({
        "success": True,
        "student": student,
        "summary": summary,
        "progress": progress
    })
# =========================================================
# GUEST DEMO SCREENING API
# Runs AI prediction only.
# Does NOT save official sample/result/report/validation records.
# =========================================================

@app.route("/api/user/guest/demo-screening", methods=["POST"])
@require_user_api(["guest"])
def api_guest_demo_screening():
    guest_id = g.current_user["user_id"]

    file = request.files.get("handwriting_image")

    if not file or file.filename == "":
        return jsonify({
            "success": False,
            "message": "Please select a handwriting image."
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "message": "Invalid file type. Please upload JPG, JPEG, or PNG only."
        }), 400

    filename = secure_filename(file.filename)
    unique_filename = f"guest_demo_{guest_id}_{random.randint(1000, 9999)}_{filename}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)

    try:
        file.save(filepath)
        screening_result = run_handwriting_screening(filepath, demo=True)

        classification = screening_result["classification"]
        dysgraphia_probability = screening_result["dysgraphia_probability"]
        confidence_score = screening_result["confidence_score"]
        analysis_summary = screening_result["analysis_summary"]

        log_action(
            guest_id,
            "Ran guest demo handwriting screening through user app"
        )

        return jsonify({
            "success": True,
            "message": "Demo screening completed. This result was not saved as an official record.",
            "classification": classification,
            "confidence_score": confidence_score,
            "dysgraphia_probability": dysgraphia_probability,
            "analysis_summary": analysis_summary,
            "is_demo": True
        })

    except Exception as err:
        print("Guest demo screening error:", err)

        return jsonify({
            "success": False,
            "message": "Unable to run demo screening. Please try again."
        }), 500

    finally:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as cleanup_error:
                print("Unable to remove guest demo file:", cleanup_error)
    # =========================================================
# TEACHER APP API - RESULT DETAILS
# Shows one screening result owned by the logged-in teacher
# =========================================================

@app.route("/api/user/teacher/results/<int:result_id>", methods=["GET"])
@require_user_api(["teacher"])
def api_teacher_result_detail(result_id):
    teacher_id = g.current_user["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            r.result_id,
            r.dysgraphia_probability,
            r.classification,
            r.confidence_score,
            r.analysis_summary,
            r.date_generated,

            hs.image_path,
            hs.teacher_id,

            s.fullname AS student_name,
            s.age,
            s.grade_level,

            parent.fullname AS parent_name,

            COALESCE(v.validation_status, 'Pending') AS validation_status,
            COALESCE(v.remarks, '') AS remarks,
            COALESCE(v.expert_recommendation, '') AS expert_recommendation,
            COALESCE(v.follow_up_needed, 'No') AS follow_up_needed,
            v.validation_date,

            expert.fullname AS expert_name

        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        JOIN students s ON hs.student_id = s.student_id
        LEFT JOIN users parent ON s.parent_id = parent.user_id
        LEFT JOIN validations v ON r.result_id = v.result_id
        LEFT JOIN users expert ON v.expert_id = expert.user_id
        WHERE r.result_id = %s AND hs.teacher_id = %s
    """, (result_id, teacher_id))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if not result:
        return jsonify({
            "success": False,
            "message": "Result not found or access denied."
        }), 404

    if result["date_generated"]:
        result["date_generated"] = str(result["date_generated"])

    if result["validation_date"]:
        result["validation_date"] = str(result["validation_date"])

    result["image_url"] = build_image_url(result.get("image_path"))

    return jsonify({
        "success": True,
        "result": result
    })

    # =========================================================
# EXPERT APP API - VALIDATION QUEUE / RESULTS
# Shows screening results for Expert / SPED review
# =========================================================

@app.route("/api/user/expert/results", methods=["GET"])
@require_user_api(["expert"])
def api_expert_results():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            r.result_id,
            r.classification,
            r.dysgraphia_probability,
            r.confidence_score,
            r.date_generated,
            s.fullname AS student_name,
            s.age,
            s.grade_level,
            teacher.fullname AS teacher_name,
            v.validation_status,
            v.remarks
        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        JOIN students s ON hs.student_id = s.student_id
        JOIN users teacher ON hs.teacher_id = teacher.user_id
        LEFT JOIN validations v ON r.result_id = v.result_id
        ORDER BY 
            CASE 
                WHEN v.validation_status = 'Pending' OR v.validation_status IS NULL THEN 1
                WHEN v.validation_status = 'Flagged' THEN 2
                WHEN v.validation_status = 'Validated' THEN 3
                ELSE 4
            END,
            r.date_generated DESC
    """)

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    for result in results:
        if result["date_generated"]:
            result["date_generated"] = str(result["date_generated"])

        if result["validation_status"] is None:
            result["validation_status"] = "Pending"

        if result["remarks"] is None:
            result["remarks"] = "No remarks yet."

    return jsonify({
        "success": True,
        "results": results,
        "total_results": len(results)
    })

    # =========================================================
# EXPERT APP API - RESULT DETAILS FOR VALIDATION
# Shows one screening result for Expert / SPED review
# =========================================================

@app.route("/api/user/expert/results/<int:result_id>", methods=["GET"])
@require_user_api(["expert"])
def api_expert_result_detail(result_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            r.result_id,
            r.dysgraphia_probability,
            r.classification,
            r.confidence_score,
            r.analysis_summary,
            r.date_generated,

            hs.image_path,
            
            s.student_id,
            s.fullname AS student_name,
            s.age,
            s.grade_level,

            teacher.fullname AS teacher_name,

            COALESCE(v.validation_status, 'Pending') AS validation_status,
            COALESCE(v.remarks, '') AS remarks,
            COALESCE(v.expert_recommendation, '') AS expert_recommendation,
            COALESCE(v.follow_up_needed, 'No') AS follow_up_needed,
            v.validation_date,

            expert.fullname AS expert_name

        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        JOIN students s ON hs.student_id = s.student_id
        JOIN users teacher ON hs.teacher_id = teacher.user_id
        LEFT JOIN validations v ON r.result_id = v.result_id
        LEFT JOIN users expert ON v.expert_id = expert.user_id
        WHERE r.result_id = %s
    """, (result_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if not result:
        return jsonify({
            "success": False,
            "message": "Result not found."
        }), 404

    if result["date_generated"]:
        result["date_generated"] = str(result["date_generated"])

    if result["validation_date"]:
        result["validation_date"] = str(result["validation_date"])

    result["image_url"] = build_image_url(result.get("image_path"))

    return jsonify({
        "success": True,
        "result": result
    })



 ###Expert Student Progress API
@app.route("/api/user/expert/students/<int:student_id>/progress", methods=["GET"])
@require_user_api(["expert"])
def api_expert_student_progress(student_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.student_id,
            s.fullname,
            s.age,
            s.grade_level,
            teacher.fullname AS teacher_name,
            parent.fullname AS parent_name
        FROM students s
        JOIN users teacher ON s.teacher_id = teacher.user_id
        LEFT JOIN users parent ON s.parent_id = parent.user_id
        WHERE s.student_id = %s
        AND EXISTS (
            SELECT 1
            FROM handwriting_samples hs
            JOIN results r ON hs.sample_id = r.sample_id
            WHERE hs.student_id = s.student_id
        )
    """, (student_id,))

    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Student not found or no screening record available."
        }), 404

    cursor.execute("""
        SELECT
            r.result_id,
            r.dysgraphia_probability,
            r.classification,
            r.confidence_score,
            r.date_generated,
            COALESCE(v.validation_status, 'Pending') AS validation_status,
            COALESCE(v.remarks, '') AS remarks,
            COALESCE(v.expert_recommendation, '') AS expert_recommendation,
            COALESCE(v.follow_up_needed, 'No') AS follow_up_needed,
            expert.fullname AS expert_name
        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        LEFT JOIN validations v ON r.result_id = v.result_id
        LEFT JOIN users expert ON v.expert_id = expert.user_id
        WHERE hs.student_id = %s
        ORDER BY r.date_generated ASC
    """, (student_id,))

    progress = cursor.fetchall()

    cursor.close()
    conn.close()

    for item in progress:
        if item["date_generated"]:
            item["date_generated"] = str(item["date_generated"])

    latest_result = progress[-1] if progress else None
    summary = {
        "total_screenings": len(progress),
        "latest_result": latest_result
    }
    return jsonify({
        "success": True,
        "student": student,
        "summary": summary,
        "progress": progress
    })

# =========================================================
# EXPERT APP API - VALIDATE RESULT
# Allows Expert / SPED to update validation status and remarks
# =========================================================

@app.route("/api/user/expert/results/<int:result_id>/validate", methods=["POST"])
@require_user_api(["expert"])
def api_expert_validate_result(result_id):
    expert_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}

    validation_status = data.get("validation_status")
    remarks = data.get("remarks", "").strip()
    expert_recommendation = data.get("expert_recommendation", "").strip()
    follow_up_needed = data.get("follow_up_needed", "No")

    if validation_status not in ["Validated", "Flagged"]:
        return jsonify({
            "success": False,
            "message": "Validation status must be Validated or Flagged."
        }), 400

    if follow_up_needed not in ["Yes", "No"]:
        return jsonify({
            "success": False,
            "message": "Follow-up needed must be Yes or No."
        }), 400

    if not remarks:
        return jsonify({
            "success": False,
            "message": "Please enter expert remarks."
        }), 400

    if not expert_recommendation:
        return jsonify({
            "success": False,
            "message": "Please enter expert recommendation."
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT result_id
        FROM validations
        WHERE result_id = %s
    """, (result_id,))

    validation = cursor.fetchone()

    if not validation:
        cursor.execute("""
            INSERT INTO validations 
            (
                result_id,
                validation_status,
                remarks,
                expert_recommendation,
                follow_up_needed,
                expert_id,
                validation_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (
            result_id,
            validation_status,
            remarks,
            expert_recommendation,
            follow_up_needed,
            expert_id
        ))
    else:
        cursor.execute("""
            UPDATE validations
            SET validation_status = %s,
                remarks = %s,
                expert_recommendation = %s,
                follow_up_needed = %s,
                expert_id = %s,
                validation_date = NOW()
            WHERE result_id = %s
        """, (
            validation_status,
            remarks,
            expert_recommendation,
            follow_up_needed,
            expert_id,
            result_id
        ))

    conn.commit()

    log_action(
        expert_id,
        f"Updated validation for result ID {result_id} to {validation_status}. Follow-up needed: {follow_up_needed}"
    )

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Result validation updated successfully."
    })
    # =========================================================
# PARENT APP API - CHILD RESULTS
# Shows screening results for students linked to the logged-in parent
# =========================================================

@app.route("/api/user/parent/results", methods=["GET"])
@require_user_api(["parent"])
def api_parent_results():
    parent_id = g.current_user["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            r.result_id,
            s.student_id,
            r.classification,
            r.dysgraphia_probability,
            r.confidence_score,
            r.date_generated,

            s.fullname AS student_name,
            s.age,
            s.grade_level,

            teacher.fullname AS teacher_name,

            COALESCE(v.validation_status, 'Pending') AS validation_status,
            COALESCE(v.remarks, '') AS remarks,
            COALESCE(v.expert_recommendation, '') AS expert_recommendation,
            COALESCE(v.follow_up_needed, 'No') AS follow_up_needed

        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        JOIN students s ON hs.student_id = s.student_id
        JOIN users teacher ON hs.teacher_id = teacher.user_id
        JOIN validations v ON r.result_id = v.result_id
        WHERE s.parent_id = %s
        AND v.validation_status = 'Validated'
        ORDER BY r.date_generated DESC
    """, (parent_id,))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    for result in results:
        if result["date_generated"]:
            result["date_generated"] = str(result["date_generated"])

        if not result["remarks"]:
            result["remarks"] = "No remarks yet."

        if not result["expert_recommendation"]:
            result["expert_recommendation"] = "No expert recommendation yet."

    return jsonify({
        "success": True,
        "results": results,
        "total_results": len(results)
    })
# =========================================================
# PARENT APP API - RESULT DETAILS
# Shows one screening result connected to the logged-in parent
# =========================================================

@app.route("/api/user/parent/results/<int:result_id>", methods=["GET"])
@require_user_api(["parent"])
def api_parent_result_detail(result_id):
    parent_id = g.current_user["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            r.result_id,
            s.student_id,
            r.dysgraphia_probability,
            r.classification,
            r.confidence_score,
            r.analysis_summary,
            r.date_generated,

            hs.image_path,

            s.fullname AS student_name,
            s.age,
            s.grade_level,

            teacher.fullname AS teacher_name,

            COALESCE(v.validation_status, 'Pending') AS validation_status,
            COALESCE(v.remarks, '') AS remarks,
            COALESCE(v.expert_recommendation, '') AS expert_recommendation,
            COALESCE(v.follow_up_needed, 'No') AS follow_up_needed,
            v.validation_date,

            expert.fullname AS expert_name

        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        JOIN students s ON hs.student_id = s.student_id
        JOIN users teacher ON hs.teacher_id = teacher.user_id
        JOIN validations v ON r.result_id = v.result_id
        LEFT JOIN users expert ON v.expert_id = expert.user_id
        WHERE r.result_id = %s
        AND s.parent_id = %s
        AND v.validation_status = 'Validated'
    """, (result_id, parent_id))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if not result:
        return jsonify({
            "success": False,
            "message": "Result not found or access denied."
        }), 404

    if result["date_generated"]:
        result["date_generated"] = str(result["date_generated"])

    if result["validation_date"]:
        result["validation_date"] = str(result["validation_date"])

    result["image_url"] = build_image_url(result.get("image_path"))

    return jsonify({
        "success": True,
        "result": result
    })

 ####### Parent Child Progress API

@app.route("/api/user/parent/students/<int:student_id>/progress", methods=["GET"])
@require_user_api(["parent"])
def api_parent_student_progress(student_id):
    parent_id = g.current_user["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.student_id,
            s.fullname,
            s.age,
            s.grade_level,
            teacher.fullname AS teacher_name
        FROM students s
        JOIN users teacher ON s.teacher_id = teacher.user_id
        WHERE s.student_id = %s
        AND s.parent_id = %s
    """, (student_id, parent_id))

    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Student not found or access denied."
        }), 404

    cursor.execute("""
        SELECT
            r.result_id,
            r.dysgraphia_probability,
            r.classification,
            r.confidence_score,
            r.date_generated,
            COALESCE(v.validation_status, 'Pending') AS validation_status,
            COALESCE(v.remarks, '') AS remarks,
            COALESCE(v.expert_recommendation, '') AS expert_recommendation,
            COALESCE(v.follow_up_needed, 'No') AS follow_up_needed,
            expert.fullname AS expert_name
        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        JOIN validations v ON r.result_id = v.result_id
        LEFT JOIN users expert ON v.expert_id = expert.user_id
        WHERE hs.student_id = %s
        AND v.validation_status = 'Validated'
        ORDER BY r.date_generated ASC
    """, (student_id,))

    progress = cursor.fetchall()

    cursor.close()
    conn.close()

    for item in progress:
        if item["date_generated"]:
            item["date_generated"] = str(item["date_generated"])

    latest_result = progress[-1] if progress else None

    summary = {
        "total_screenings": len(progress),
        "latest_result": latest_result
    }

    return jsonify({
        "success": True,
        "student": student,
        "summary": summary,
        "progress": progress
    })
# =========================================================
# 06. OLD ADMIN PAGE ROUTES
# These no longer render old Jinja admin templates.
# They now redirect to the Vue admin web panel.
# =========================================================

@app.route("/admin/dashboard")
def admin_dashboard():
    return redirect(f"{VUE_ADMIN_BASE_URL}/admin/dashboard")


@app.route("/admin/users")
def admin_users():
    return redirect(f"{VUE_ADMIN_BASE_URL}/admin/users")


@app.route("/admin/results")
def admin_results():
    return redirect(f"{VUE_ADMIN_BASE_URL}/admin/results")


@app.route("/admin/audit-logs")
def admin_audit_logs():
    return redirect(f"{VUE_ADMIN_BASE_URL}/admin/audit-logs")


@app.route("/admin/validations")
def admin_validations():
    return redirect(f"{VUE_ADMIN_BASE_URL}/admin/results?validation=Pending")


# =========================================================
# 07. VUE ADMIN DASHBOARD API
# =========================================================

@app.route("/api/admin/dashboard", methods=["GET"])
@require_admin_api
def api_admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cursor.fetchone()["total_users"]

    cursor.execute("SELECT COUNT(*) AS total_students FROM students")
    total_students = cursor.fetchone()["total_students"]

    cursor.execute("SELECT COUNT(*) AS total_samples FROM handwriting_samples")
    total_samples = cursor.fetchone()["total_samples"]

    cursor.execute("SELECT COUNT(*) AS total_results FROM results")
    total_results = cursor.fetchone()["total_results"]

    cursor.execute("""
        SELECT COUNT(*) AS pending_validations
        FROM validations
        WHERE validation_status = 'Pending'
    """)
    pending_validations = cursor.fetchone()["pending_validations"]

    cursor.execute("""
        SELECT COUNT(*) AS validated_validations
        FROM validations
        WHERE validation_status = 'Validated'
    """)
    validated_validations = cursor.fetchone()["validated_validations"]

    cursor.execute("""
        SELECT COUNT(*) AS flagged_validations
        FROM validations
        WHERE validation_status = 'Flagged'
    """)
    flagged_validations = cursor.fetchone()["flagged_validations"]

    cursor.execute("SELECT COUNT(*) AS total_logs FROM audit_logs")
    total_logs = cursor.fetchone()["total_logs"]

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "dashboard": {
            "total_users": total_users,
            "total_students": total_students,
            "total_samples": total_samples,
            "total_results": total_results,
            "pending_validations": pending_validations,
            "validated_validations": validated_validations,
            "flagged_validations": flagged_validations,
            "total_logs": total_logs
        }
    })


# =========================================================
# 08. TEACHER / EXPERT / PARENT DASHBOARDS
# These are still Flask/Jinja pages.
# Do not delete their templates yet.
# =========================================================

@app.route("/teacher/dashboard")
def teacher_dashboard():
    if not is_logged_in() or session.get("role") != "teacher":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    return render_template("teacher_dashboard.html")


@app.route("/expert/dashboard")
def expert_dashboard():
    if not is_logged_in() or session.get("role") != "expert":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    return render_template("expert_dashboard.html")


@app.route("/parent/dashboard")
def parent_dashboard():
    if not is_logged_in() or session.get("role") != "parent":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    return render_template("parent_dashboard.html")


# =========================================================
# 09. TEACHER STUDENT MANAGEMENT
# =========================================================

@app.route("/students")
def students():
    if not is_logged_in() or session.get("role") != "teacher":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            s.student_id,
            s.fullname,
            s.age,
            s.grade_level,
            s.created_at,
            u.fullname AS parent_name
        FROM students s
        LEFT JOIN users u ON s.parent_id = u.user_id
        WHERE s.teacher_id = %s
        ORDER BY s.created_at DESC
    """, (session["user_id"],))

    student_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("students.html", students=student_list)


@app.route("/students/add", methods=["GET", "POST"])
def add_student():
    if not is_logged_in() or session.get("role") != "teacher":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT user_id, fullname FROM users WHERE role = 'parent'")
    parents = cursor.fetchall()

    if request.method == "POST":
        fullname = request.form["fullname"]
        age = request.form["age"]
        grade_level = request.form["grade_level"]
        parent_id = request.form.get("parent_id")

        if parent_id == "":
            parent_id = None

        cursor.execute("""
            INSERT INTO students (fullname, age, grade_level, parent_id, teacher_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (fullname, age, grade_level, parent_id, session["user_id"]))

        conn.commit()

        log_action(session["user_id"], f"Added student record: {fullname}")

        cursor.close()
        conn.close()

        flash("Student added successfully.", "success")
        return redirect(url_for("students"))

    cursor.close()
    conn.close()

    return render_template("add_student.html", parents=parents)


# =========================================================
# 10. HANDWRITING SAMPLE UPLOAD + AI SCREENING
# =========================================================

@app.route("/upload", methods=["GET", "POST"])
def upload_sample():
    if not is_logged_in() or session.get("role") != "teacher":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT student_id, fullname, age, grade_level
        FROM students
        WHERE teacher_id = %s
        ORDER BY fullname ASC
    """, (session["user_id"],))

    students = cursor.fetchall()

    if request.method == "POST":
        student_id = request.form["student_id"]
        file = request.files.get("handwriting_image")

        if not file or file.filename == "":
            flash("Please select or capture a handwriting image.", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for("upload_sample"))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            unique_filename = f"{session['user_id']}_{student_id}_{random.randint(1000, 9999)}_{filename}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)

            file.save(filepath)

            # AI SCREENING RESULT
            # Uses the active GRAPHISCAN binary model.
            try:
                screening_result = run_handwriting_screening(filepath)

            except Exception as err:
                print("Flask upload screening error:", err)

                cursor.close()
                conn.close()

                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except Exception as cleanup_error:
                        print("Unable to remove failed upload file:", cleanup_error)

                flash("Unable to process handwriting screening. Please try again.", "danger")
                return redirect(url_for("upload_sample"))

            classification = screening_result["classification"]
            dysgraphia_probability = screening_result["dysgraphia_probability"]
            confidence_score = screening_result["confidence_score"]
            analysis_summary = screening_result["analysis_summary"]

            cursor.execute("""
                INSERT INTO handwriting_samples (student_id, teacher_id, image_path)
                VALUES (%s, %s, %s)
            """, (student_id, session["user_id"], filepath))

            sample_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO results 
                (sample_id, dysgraphia_probability, classification, confidence_score, analysis_summary, recommendation)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                sample_id,
                dysgraphia_probability,
                classification,
                confidence_score,
                analysis_summary,
                ""
            ))

            result_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO validations (result_id, validation_status)
                VALUES (%s, 'Pending')
            """, (result_id,))

            cursor.execute("SELECT COUNT(*) FROM reports WHERE student_id = %s", (student_id,))
            report_type = "Follow-up Screening" if cursor.fetchone()[0] else "Initial Screening"
            cursor.execute("""
                INSERT INTO reports (student_id, result_id, report_type, report_status)
                VALUES (%s, %s, %s, 'Generated')
            """, (student_id, result_id, report_type))

            conn.commit()

            log_action(
                session["user_id"],
                f"Uploaded handwriting sample and generated screening result ID {result_id}"
            )

            cursor.close()
            conn.close()

            flash("Handwriting sample uploaded and screened successfully.", "success")
            return redirect(url_for("view_result", result_id=result_id))

        flash("Invalid file type. Please upload JPG, JPEG, or PNG only.", "danger")

    cursor.close()
    conn.close()

    return render_template("upload.html", students=students)


# =========================================================
# 11. SHARED RESULT VIEW
# Used by teacher, parent, expert, and admin.
# =========================================================

@app.route("/result/<int:result_id>")
def view_result(result_id):
    if not is_logged_in():
        flash("Please log in first.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            r.result_id,
            r.dysgraphia_probability,
            r.classification,
            r.confidence_score,
            r.analysis_summary,
            r.date_generated,
            hs.image_path,
            hs.teacher_id,
            s.student_id,
            s.fullname AS student_name,
            s.age,
            s.grade_level,
            s.parent_id,
            v.validation_status,
            v.remarks
        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        JOIN students s ON hs.student_id = s.student_id
        LEFT JOIN validations v ON r.result_id = v.result_id
        WHERE r.result_id = %s
    """, (result_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if not result:
        flash("Result not found.", "danger")
        return redirect(url_for("login"))

    role = session.get("role")
    user_id = session.get("user_id")

    allowed = False

    if role == "admin":
        allowed = True
    elif role == "expert":
        allowed = True
    elif role == "teacher" and result["teacher_id"] == user_id:
        allowed = True
    elif role == "parent" and result["parent_id"] == user_id and result["validation_status"] == "Validated":
        allowed = True

    if not allowed:
        flash("Access denied.", "danger")

        if role == "teacher":
            return redirect(url_for("teacher_dashboard"))
        elif role == "parent":
            return redirect(url_for("parent_dashboard"))
        elif role == "expert":
            return redirect(url_for("expert_dashboard"))
        elif role == "admin":
            return redirect(f"{VUE_ADMIN_BASE_URL}/admin/dashboard")
        else:
            return redirect(url_for("login"))

    return render_template("result.html", result=result)


# =========================================================
# 12. TEACHER RESULT HISTORY
# =========================================================

@app.route("/results")
def result_history():
    if not is_logged_in() or session.get("role") != "teacher":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            r.result_id,
            r.classification,
            r.dysgraphia_probability,
            r.confidence_score,
            r.date_generated,
            s.fullname AS student_name,
            s.grade_level,
            v.validation_status
        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        JOIN students s ON hs.student_id = s.student_id
        LEFT JOIN validations v ON r.result_id = v.result_id
        WHERE hs.teacher_id = %s
        ORDER BY r.date_generated DESC
    """, (session["user_id"],))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("result_history.html", results=results)


# =========================================================
# 13. EXPERT RESULTS + VALIDATION
# =========================================================

@app.route("/expert/results")
def expert_results():
    if not is_logged_in() or session.get("role") != "expert":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            r.result_id,
            r.classification,
            r.dysgraphia_probability,
            r.confidence_score,
            r.date_generated,
            s.fullname AS student_name,
            s.age,
            s.grade_level,
            u.fullname AS teacher_name,
            v.validation_status,
            v.remarks
        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        JOIN students s ON hs.student_id = s.student_id
        JOIN users u ON hs.teacher_id = u.user_id
        LEFT JOIN validations v ON r.result_id = v.result_id
        ORDER BY r.date_generated DESC
    """)

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("expert_results.html", results=results)


@app.route("/expert/validate/<int:result_id>", methods=["GET", "POST"])
def validate_result(result_id):
    if not is_logged_in() or session.get("role") != "expert":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        validation_status = request.form["validation_status"]
        remarks = request.form["remarks"]

        cursor.execute("""
            UPDATE validations
            SET validation_status = %s,
                remarks = %s,
                expert_id = %s,
                validation_date = NOW()
            WHERE result_id = %s
        """, (validation_status, remarks, session["user_id"], result_id))

        conn.commit()

        log_action(
            session["user_id"],
            f"Updated validation for result ID {result_id} to {validation_status}"
        )

        cursor.close()
        conn.close()

        flash("Result validation updated successfully.", "success")
        return redirect(url_for("expert_results"))

    cursor.execute("""
        SELECT 
            r.result_id,
            r.dysgraphia_probability,
            r.classification,
            r.confidence_score,
            r.analysis_summary,
            r.date_generated,
            hs.image_path,
            s.fullname AS student_name,
            s.age,
            s.grade_level,
            u.fullname AS teacher_name,
            v.validation_status,
            v.remarks
        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        JOIN students s ON hs.student_id = s.student_id
        JOIN users u ON hs.teacher_id = u.user_id
        LEFT JOIN validations v ON r.result_id = v.result_id
        WHERE r.result_id = %s
    """, (result_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if not result:
        flash("Result not found.", "danger")
        return redirect(url_for("expert_results"))

    return render_template("validate_result.html", result=result)


# =========================================================
# 14. PARENT RESULTS
# =========================================================

@app.route("/parent/results")
def parent_results():
    if not is_logged_in() or session.get("role") != "parent":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            r.result_id,
            r.classification,
            r.dysgraphia_probability,
            r.confidence_score,
            r.date_generated,
            s.fullname AS student_name,
            s.age,
            s.grade_level,
            u.fullname AS teacher_name,
            v.validation_status,
            v.remarks
        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        JOIN students s ON hs.student_id = s.student_id
        JOIN users u ON hs.teacher_id = u.user_id
        JOIN validations v ON r.result_id = v.result_id
        WHERE s.parent_id = %s
        AND v.validation_status = 'Validated'
        ORDER BY r.date_generated DESC
    """, (session["user_id"],))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("parent_results.html", results=results)


# =========================================================
# 15. REPORT VIEW
# =========================================================

@app.route("/report/<int:result_id>")
def view_report(result_id):
    if not is_logged_in():
        flash("Please log in first.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            r.result_id,
            r.dysgraphia_probability,
            r.classification,
            r.confidence_score,
            r.analysis_summary,
            r.date_generated,
            hs.image_path,
            hs.teacher_id,
            s.student_id,
            s.fullname AS student_name,
            s.age,
            s.grade_level,
            s.parent_id,
            teacher.fullname AS teacher_name,
            parent.fullname AS parent_name,
            v.validation_status,
            v.remarks,
            expert.fullname AS expert_name,
            v.validation_date
        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        JOIN students s ON hs.student_id = s.student_id
        JOIN users teacher ON hs.teacher_id = teacher.user_id
        LEFT JOIN users parent ON s.parent_id = parent.user_id
        LEFT JOIN validations v ON r.result_id = v.result_id
        LEFT JOIN users expert ON v.expert_id = expert.user_id
        WHERE r.result_id = %s
    """, (result_id,))

    report = cursor.fetchone()

    cursor.close()
    conn.close()

    if not report:
        flash("Report not found.", "danger")
        return redirect(url_for("login"))

    role = session.get("role")
    user_id = session.get("user_id")

    allowed = False

    if role == "admin":
        allowed = True
    elif role == "expert":
        allowed = True
    elif role == "teacher" and report["teacher_id"] == user_id:
        allowed = True
    elif role == "parent" and report["parent_id"] == user_id and report["validation_status"] == "Validated":
        allowed = True

    if not allowed:
        flash("Access denied.", "danger")

        if role == "teacher":
            return redirect(url_for("teacher_dashboard"))
        elif role == "parent":
            return redirect(url_for("parent_dashboard"))
        elif role == "expert":
            return redirect(url_for("expert_dashboard"))
        elif role == "admin":
            return redirect(f"{VUE_ADMIN_BASE_URL}/admin/dashboard")
        else:
            return redirect(url_for("login"))

    return render_template("report_view.html", report=report)


# =========================================================
# 16. VUE ADMIN USERS API
# =========================================================


@app.route("/api/admin/users", methods=["GET"])
@require_admin_api
def api_admin_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            user_id,
            fullname,
            email,
            role,
            contact_no,
            account_status,
            approved_by,
            approved_at,
            created_at
        FROM users
        ORDER BY created_at DESC
    """)

    users = cursor.fetchall()

    cursor.close()
    conn.close()

    for user in users:
        if user["created_at"]:
            user["created_at"] = str(user["created_at"])

        if user["approved_at"]:
            user["approved_at"] = str(user["approved_at"])

    return jsonify({
        "success": True,
        "users": users
    })

# =========================================================
# ADMIN APPROVE USER API
# Allows admin to activate pending/rejected/disabled accounts.
# =========================================================

@app.route("/api/admin/users/<int:user_id>/approve", methods=["POST"])
@require_admin_api
def api_admin_approve_user(user_id):
    admin_id = g.current_admin["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT user_id, fullname, email, role, account_status
            FROM users
            WHERE user_id = %s
            LIMIT 1
        """, (user_id,))

        target_user = cursor.fetchone()

        if not target_user:
            return jsonify({
                "success": False,
                "message": "User account not found."
            }), 404

        cursor.execute("""
            UPDATE users
            SET account_status = 'active',
                approved_by = %s,
                approved_at = NOW()
            WHERE user_id = %s
        """, (admin_id, user_id))

        conn.commit()

        log_action(
            admin_id,
            f"Admin approved user account: {target_user['fullname']} <{target_user['email']}>"
        )

        return jsonify({
            "success": True,
            "message": "User account approved successfully."
        })

    except mysql.connector.Error as error:
        conn.rollback()
        print("ADMIN APPROVE USER ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Unable to approve account. Please try again."
        }), 400

    finally:
        cursor.close()
        conn.close()


# =========================================================
# ADMIN REJECT USER API
# Rejects pending accounts.
# =========================================================

@app.route("/api/admin/users/<int:user_id>/reject", methods=["POST"])
@require_admin_api
def api_admin_reject_user(user_id):
    admin_id = g.current_admin["user_id"]

    if user_id == admin_id:
        return jsonify({
            "success": False,
            "message": "You cannot reject your own admin account."
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT user_id, fullname, email, role, account_status
            FROM users
            WHERE user_id = %s
            LIMIT 1
        """, (user_id,))

        target_user = cursor.fetchone()

        if not target_user:
            return jsonify({
                "success": False,
                "message": "User account not found."
            }), 404

        if target_user["role"] == "admin":
            return jsonify({
                "success": False,
                "message": "Admin accounts cannot be rejected."
            }), 400

        cursor.execute("""
            UPDATE users
            SET account_status = 'rejected',
                approved_by = %s,
                approved_at = NOW()
            WHERE user_id = %s
        """, (admin_id, user_id))

        conn.commit()

        log_action(
            admin_id,
            f"Admin rejected user account: {target_user['fullname']} <{target_user['email']}>"
        )

        return jsonify({
            "success": True,
            "message": "User account rejected successfully."
        })

    except mysql.connector.Error as error:
        conn.rollback()
        print("ADMIN REJECT USER ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Unable to reject account. Please try again."
        }), 400

    finally:
        cursor.close()
        conn.close()


# =========================================================
# ADMIN DISABLE USER API
# Temporarily locks an account without deleting records.
# =========================================================

@app.route("/api/admin/users/<int:user_id>/disable", methods=["POST"])
@require_admin_api
def api_admin_disable_user(user_id):
    admin_id = g.current_admin["user_id"]

    if user_id == admin_id:
        return jsonify({
            "success": False,
            "message": "You cannot disable your own admin account."
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT user_id, fullname, email, role, account_status
            FROM users
            WHERE user_id = %s
            LIMIT 1
        """, (user_id,))

        target_user = cursor.fetchone()

        if not target_user:
            return jsonify({
                "success": False,
                "message": "User account not found."
            }), 404

        if target_user["role"] == "admin":
            cursor.execute("""
                SELECT COUNT(*) AS active_admins
                FROM users
                WHERE role = 'admin'
                AND account_status = 'active'
            """)

            active_admins = cursor.fetchone()["active_admins"]

            if active_admins <= 1:
                return jsonify({
                    "success": False,
                    "message": "You cannot disable the only active admin account."
                }), 400

        cursor.execute("""
            UPDATE users
            SET account_status = 'disabled',
                approved_by = %s,
                approved_at = NOW()
            WHERE user_id = %s
        """, (admin_id, user_id))

        conn.commit()

        log_action(
            admin_id,
            f"Admin disabled user account: {target_user['fullname']} <{target_user['email']}>"
        )

        return jsonify({
            "success": True,
            "message": "User account disabled successfully."
        })

    except mysql.connector.Error as error:
        conn.rollback()
        print("ADMIN DISABLE USER ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Unable to disable account. Please try again."
        }), 400

    finally:
        cursor.close()
        conn.close()


# =========================================================
# ADMIN RESTORE USER API
# Restores rejected/disabled users back to active.
# =========================================================

@app.route("/api/admin/users/<int:user_id>/restore", methods=["POST"])
@require_admin_api
def api_admin_restore_user(user_id):
    admin_id = g.current_admin["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT user_id, fullname, email, role, account_status
            FROM users
            WHERE user_id = %s
            LIMIT 1
        """, (user_id,))

        target_user = cursor.fetchone()

        if not target_user:
            return jsonify({
                "success": False,
                "message": "User account not found."
            }), 404

        cursor.execute("""
            UPDATE users
            SET account_status = 'active',
                approved_by = %s,
                approved_at = NOW()
            WHERE user_id = %s
        """, (admin_id, user_id))

        conn.commit()

        log_action(
            admin_id,
            f"Admin restored user account: {target_user['fullname']} <{target_user['email']}>"
        )

        return jsonify({
            "success": True,
            "message": "User account restored successfully."
        })

    except mysql.connector.Error as error:
        conn.rollback()
        print("ADMIN RESTORE USER ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Unable to restore account. Please try again."
        }), 400

    finally:
        cursor.close()
        conn.close()
# =========================================================
# ADMIN STUDENTS API
# Allows admin to view all student records in the system.
# =========================================================

@app.route("/api/admin/students", methods=["GET"])
@require_admin_api
def api_admin_students():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.student_id,
            s.fullname,
            s.age,
            s.grade_level,
            s.created_at,

            teacher.user_id AS teacher_id,
            teacher.fullname AS teacher_name,
            teacher.email AS teacher_email,

            parent.user_id AS parent_id,
            parent.fullname AS parent_name,
            parent.email AS parent_email
        FROM students s
        LEFT JOIN users teacher ON s.teacher_id = teacher.user_id
        LEFT JOIN users parent ON s.parent_id = parent.user_id
        ORDER BY s.created_at DESC
    """)

    students = cursor.fetchall()

    cursor.close()
    conn.close()

    for student in students:
        if student["created_at"]:
            student["created_at"] = str(student["created_at"])

        if student["teacher_name"] is None:
            student["teacher_name"] = "Not assigned"

        if student["teacher_email"] is None:
            student["teacher_email"] = "N/A"

        if student["parent_name"] is None:
            student["parent_name"] = "Not assigned"

        if student["parent_email"] is None:
            student["parent_email"] = "N/A"

    return jsonify({
        "success": True,
        "students": students,
        "total_students": len(students)
    })

#####Admin All Students Progress API
@app.route("/api/admin/students/progress", methods=["GET"])
@require_admin_api
def api_admin_students_progress():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.student_id,
            s.fullname AS student_name,
            s.age,
            s.grade_level,

            teacher.fullname AS teacher_name,
            parent.fullname AS parent_name,

            r.result_id,
            r.dysgraphia_probability,
            r.classification,
            r.confidence_score,
            r.date_generated,

            COALESCE(v.validation_status, 'Pending') AS validation_status,
            COALESCE(v.remarks, '') AS remarks,
            COALESCE(v.expert_recommendation, '') AS expert_recommendation,
            COALESCE(v.follow_up_needed, 'No') AS follow_up_needed,
            v.validation_date,

            expert.fullname AS expert_name

        FROM students s
        LEFT JOIN users teacher ON s.teacher_id = teacher.user_id
        LEFT JOIN users parent ON s.parent_id = parent.user_id
        LEFT JOIN handwriting_samples hs ON s.student_id = hs.student_id
        LEFT JOIN results r ON hs.sample_id = r.sample_id
        LEFT JOIN validations v ON r.result_id = v.result_id
        LEFT JOIN users expert ON v.expert_id = expert.user_id
        ORDER BY s.fullname ASC, r.date_generated ASC
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    student_map = {}
    all_results = []

    for row in rows:
        student_id = row["student_id"]

        if student_id not in student_map:
            student_map[student_id] = {
                "student_id": student_id,
                "student_name": row["student_name"],
                "age": row["age"],
                "grade_level": row["grade_level"],
                "teacher_name": row["teacher_name"] or "Not assigned",
                "parent_name": row["parent_name"] or "Not assigned",
                "progress": []
            }

        if row["result_id"]:
            date_generated = safe_date_string(row["date_generated"])
            validation_date = safe_date_string(row["validation_date"])

            progress_item = {
                "result_id": row["result_id"],
                "dysgraphia_probability": row["dysgraphia_probability"],
                "classification": row["classification"],
                "confidence_score": row["confidence_score"],
                "date_generated": date_generated,
                "validation_status": row["validation_status"] or "Pending",
                "remarks": row["remarks"] or "",
                "expert_recommendation": row["expert_recommendation"] or "",
                "follow_up_needed": row["follow_up_needed"] or "No",
                "validation_date": validation_date,
                "expert_name": row["expert_name"] or "Not yet reviewed"
            }

            student_map[student_id]["progress"].append(progress_item)
            all_results.append(progress_item)

    students = []

    for student in student_map.values():
        progress = student["progress"]
        latest_result = progress[-1] if progress else None
        students.append({
            "student_id": student["student_id"],
            "student_name": student["student_name"],
            "age": student["age"],
            "grade_level": student["grade_level"],
            "teacher_name": student["teacher_name"],
            "parent_name": student["parent_name"],
            "total_screenings": len(progress),
            "latest_result_id": latest_result["result_id"] if latest_result else None,
            "latest_classification": latest_result["classification"] if latest_result else "No result yet",
            "latest_probability": latest_result["dysgraphia_probability"] if latest_result else None,
            "latest_confidence": latest_result["confidence_score"] if latest_result else None,
            "latest_validation_status": latest_result["validation_status"] if latest_result else "Pending",
            "follow_up_needed": latest_result["follow_up_needed"] if latest_result else "No"
        })

    classification_counts = {}
    validation_counts = {
        "Pending": 0,
        "Validated": 0,
        "Flagged": 0
    }
    follow_up_counts = {
        "Yes": 0,
        "No": 0
    }

    for result in all_results:
        classification = result["classification"] or "Unclassified"
        validation_status = result["validation_status"] or "Pending"
        follow_up_needed = result["follow_up_needed"] or "No"

        classification_counts[classification] = classification_counts.get(classification, 0) + 1
        validation_counts[validation_status] = validation_counts.get(validation_status, 0) + 1
        follow_up_counts[follow_up_needed] = follow_up_counts.get(follow_up_needed, 0) + 1

    screened_students = len([
        student for student in students
        if student["total_screenings"] > 0
    ])

    students_needing_follow_up = len([
        student for student in students
        if student["follow_up_needed"] == "Yes"
    ])

    summary = {
        "total_students": len(students),
        "screened_students": screened_students,
        "total_screenings": len(all_results),
        "pending_validations": validation_counts.get("Pending", 0),
        "expert_reviewed": validation_counts.get("Validated", 0) + validation_counts.get("Flagged", 0),
        "students_needing_follow_up": students_needing_follow_up
    }

    return jsonify({
        "success": True,
        "summary": summary,
        "students": students,
        "charts": {
            "classification_counts": classification_counts,
            "validation_counts": validation_counts,
            "follow_up_counts": follow_up_counts
        }
    })

####Admin Individual Student Progress API
@app.route("/api/admin/students/<int:student_id>/progress", methods=["GET"])
@require_admin_api
def api_admin_student_progress_detail(student_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.student_id,
            s.fullname,
            s.age,
            s.grade_level,
            teacher.fullname AS teacher_name,
            parent.fullname AS parent_name
        FROM students s
        LEFT JOIN users teacher ON s.teacher_id = teacher.user_id
        LEFT JOIN users parent ON s.parent_id = parent.user_id
        WHERE s.student_id = %s
    """, (student_id,))

    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Student not found."
        }), 404

    cursor.execute("""
        SELECT
            r.result_id,
            r.dysgraphia_probability,
            r.classification,
            r.confidence_score,
            r.date_generated,

            COALESCE(v.validation_status, 'Pending') AS validation_status,
            COALESCE(v.remarks, '') AS remarks,
            COALESCE(v.expert_recommendation, '') AS expert_recommendation,
            COALESCE(v.follow_up_needed, 'No') AS follow_up_needed,
            v.validation_date,

            expert.fullname AS expert_name

        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        LEFT JOIN validations v ON r.result_id = v.result_id
        LEFT JOIN users expert ON v.expert_id = expert.user_id
        WHERE hs.student_id = %s
        ORDER BY r.date_generated ASC
    """, (student_id,))

    progress = cursor.fetchall()

    cursor.close()
    conn.close()

    for item in progress:
        if item["date_generated"]:
            item["date_generated"] = str(item["date_generated"])

        if item["validation_date"]:
            item["validation_date"] = str(item["validation_date"])

        if not item["validation_status"]:
            item["validation_status"] = "Pending"

        if not item["remarks"]:
            item["remarks"] = ""

        if not item["expert_recommendation"]:
            item["expert_recommendation"] = ""

        if not item["follow_up_needed"]:
            item["follow_up_needed"] = "No"

        if not item["expert_name"]:
            item["expert_name"] = "Not yet reviewed"

    latest_result = progress[-1] if progress else None

    summary = {
        "total_screenings": len(progress),
        "latest_result": latest_result
    }

    return jsonify({
        "success": True,
        "student": student,
        "summary": summary,
        "progress": progress
    })
# =========================================================
# ADMIN CREATE USER API
# Allows admin to create admin, teacher, parent, expert, or guest accounts.
# New admin-created accounts are active immediately.
# =========================================================

@app.route("/api/admin/users/add", methods=["POST"])
@require_admin_api
def api_admin_add_user():
    data = request.get_json() or {}

    fullname = data.get("fullname", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")
    role = data.get("role", "").strip().lower()
    contact_no = data.get("contact_no", "").strip()

    admin_id = g.current_admin["user_id"]

    if not fullname or not email or not password or not confirm_password or not role:
        return jsonify({
            "success": False,
            "message": "Please complete all required fields."
        }), 400

    if not validate_email_format(email):
        return jsonify({
            "success": False,
            "message": "Please enter a valid email address."
        }), 400

    if role not in ["admin", "teacher", "parent", "expert", "guest"]:
        return jsonify({
            "success": False,
            "message": "Invalid account role."
        }), 400

    if password != confirm_password:
        return jsonify({
            "success": False,
            "message": "Passwords do not match."
        }), 400

    password_errors = validate_password_strength(password)

    if password_errors:
        return jsonify({
            "success": False,
            "message": password_errors[0]
        }), 400

    hashed_password = hash_password(password)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT user_id
            FROM users
            WHERE email = %s
            LIMIT 1
        """, (email,))

        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({
                "success": False,
                "message": "An account with this email already exists."
            }), 400

        cursor.execute("""
            INSERT INTO users
            (fullname, email, password, role, contact_no, account_status, approved_by, approved_at)
            VALUES (%s, %s, %s, %s, %s, 'active', %s, NOW())
        """, (fullname, email, hashed_password, role, contact_no, admin_id))

        conn.commit()

        new_user_id = cursor.lastrowid

        log_action(
            admin_id,
            f"Admin created new {role} account: {fullname} <{email}>"
        )

        return jsonify({
            "success": True,
            "message": "User account created successfully.",
            "user_id": new_user_id
        })

    except mysql.connector.Error as error:
        conn.rollback()

        print("ADMIN ADD USER ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Unable to create user account. Please try again."
        }), 400

    finally:
        cursor.close()
        conn.close()

        # =========================================================
# ADMIN ADD STUDENT API
# Allows admin to create a student and assign teacher/parent.
# =========================================================

@app.route("/api/admin/students/add", methods=["POST"])
@require_admin_api
def api_admin_add_student():
    data = request.get_json() or {}

    fullname = data.get("fullname", "").strip()
    age = data.get("age")
    grade_level = data.get("grade_level", "").strip()
    teacher_id = data.get("teacher_id")
    parent_id = data.get("parent_id")

    admin_id = g.current_admin["user_id"]

    if not fullname or not age or not grade_level or not teacher_id:
        return jsonify({
            "success": False,
            "message": "Full name, age, grade level, and teacher are required."
        }), 400

    if parent_id == "" or parent_id is None:
        parent_id = None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT user_id, fullname, email
            FROM users
            WHERE user_id = %s
            AND role = 'teacher'
            AND account_status = 'active'
            LIMIT 1
        """, (teacher_id,))

        teacher = cursor.fetchone()

        if not teacher:
            return jsonify({
                "success": False,
                "message": "Selected teacher account was not found or is not active."
            }), 404

        if parent_id:
            cursor.execute("""
                SELECT user_id, fullname, email
                FROM users
                WHERE user_id = %s
                AND role = 'parent'
                AND account_status = 'active'
                LIMIT 1
            """, (parent_id,))

            parent = cursor.fetchone()

            if not parent:
                return jsonify({
                    "success": False,
                    "message": "Selected parent account was not found or is not active."
                }), 404

        cursor.execute("""
            INSERT INTO students (fullname, age, grade_level, parent_id, teacher_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (fullname, age, grade_level, parent_id, teacher_id))

        conn.commit()

        student_id = cursor.lastrowid

        log_action(
            admin_id,
            f"Admin added student record: {fullname} assigned to teacher ID {teacher_id}"
        )

        return jsonify({
            "success": True,
            "message": "Student added successfully.",
            "student_id": student_id
        })

    except mysql.connector.Error as error:
        conn.rollback()

        print("ADMIN ADD STUDENT ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Unable to add student. Please try again."
        }), 400

    finally:
        cursor.close()
        conn.close()

        # =========================================================
# ADMIN PERMANENT DELETE STUDENT API
# Requires DELETE confirmation + admin password.
# Deletes connected samples, results, reports, and validations.
# =========================================================

@app.route("/api/admin/students/<int:student_id>/delete", methods=["POST"])
@require_admin_api
def api_admin_delete_student(student_id):
    data = request.get_json() or {}

    confirmation_text = data.get("confirmation_text", "").strip()
    admin_password = data.get("admin_password", "")

    if confirmation_text != "DELETE":
        return jsonify({
            "success": False,
            "message": "Please type DELETE to confirm permanent deletion."
        }), 400

    if not admin_password:
        return jsonify({
            "success": False,
            "message": "Admin password is required."
        }), 400

    admin_id = g.current_admin["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT user_id, password
            FROM users
            WHERE user_id = %s
            AND role = 'admin'
            LIMIT 1
        """, (admin_id,))

        admin_user = cursor.fetchone()

        if not admin_user:
            return jsonify({
                "success": False,
                "message": "Admin account not found."
            }), 404

        is_valid_password, needs_upgrade = verify_password(
            admin_user["password"],
            admin_password
        )

        if not is_valid_password:
            return jsonify({
                "success": False,
                "message": "Admin password confirmation failed."
            }), 403

        if needs_upgrade:
            upgraded_hash = hash_password(admin_password)

            cursor.execute("""
                UPDATE users
                SET password = %s
                WHERE user_id = %s
            """, (upgraded_hash, admin_id))

        cursor.execute("""
            SELECT student_id, fullname
            FROM students
            WHERE student_id = %s
            LIMIT 1
        """, (student_id,))

        student = cursor.fetchone()

        if not student:
            return jsonify({
                "success": False,
                "message": "Student record not found."
            }), 404

        deleted_summary = {
            "samples": 0,
            "results": 0,
            "reports": 0,
            "validations": 0
        }

        cursor.execute("""
            SELECT sample_id, image_path
            FROM handwriting_samples
            WHERE student_id = %s
        """, (student_id,))

        samples = cursor.fetchall()
        sample_ids = [sample["sample_id"] for sample in samples]
        image_paths = [sample["image_path"] for sample in samples if sample["image_path"]]

        deleted_summary["samples"] = len(sample_ids)

        result_ids = []

        if sample_ids:
            sample_placeholders = ",".join(["%s"] * len(sample_ids))

            cursor.execute(f"""
                SELECT result_id
                FROM results
                WHERE sample_id IN ({sample_placeholders})
            """, tuple(sample_ids))

            result_ids = [row["result_id"] for row in cursor.fetchall()]
            deleted_summary["results"] = len(result_ids)

        if result_ids:
            result_placeholders = ",".join(["%s"] * len(result_ids))

            cursor.execute(f"""
                SELECT COUNT(*) AS total_reports
                FROM reports
                WHERE result_id IN ({result_placeholders})
            """, tuple(result_ids))
            deleted_summary["reports"] = cursor.fetchone()["total_reports"]

            cursor.execute(f"""
                SELECT COUNT(*) AS total_validations
                FROM validations
                WHERE result_id IN ({result_placeholders})
            """, tuple(result_ids))
            deleted_summary["validations"] = cursor.fetchone()["total_validations"]

            cursor.execute(f"""
                DELETE FROM reports
                WHERE result_id IN ({result_placeholders})
            """, tuple(result_ids))

            cursor.execute(f"""
                DELETE FROM validations
                WHERE result_id IN ({result_placeholders})
            """, tuple(result_ids))

            cursor.execute(f"""
                DELETE FROM results
                WHERE result_id IN ({result_placeholders})
            """, tuple(result_ids))

        if sample_ids:
            sample_placeholders = ",".join(["%s"] * len(sample_ids))

            cursor.execute(f"""
                DELETE FROM handwriting_samples
                WHERE sample_id IN ({sample_placeholders})
            """, tuple(sample_ids))

        cursor.execute("""
            DELETE FROM students
            WHERE student_id = %s
        """, (student_id,))

        conn.commit()

        for image_path in image_paths:
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
            except OSError:
                pass

        log_action(
            admin_id,
            (
                "PERMANENT DELETE STUDENT: "
                f"{student['fullname']} student_id={student_id}. "
                f"Deleted related records: "
                f"samples={deleted_summary['samples']}, "
                f"results={deleted_summary['results']}, "
                f"reports={deleted_summary['reports']}, "
                f"validations={deleted_summary['validations']}."
            )
        )

        return jsonify({
            "success": True,
            "message": "Student record permanently deleted successfully.",
            "deleted_summary": deleted_summary
        })

    except mysql.connector.Error as error:
        conn.rollback()

        print("ADMIN DELETE STUDENT ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Unable to permanently delete student. Please check linked records or database constraints."
        }), 400

    finally:
        cursor.close()
        conn.close()

        # =========================================================
# ADMIN UPDATE STUDENT GUARDIAN API
# Allows admin to link, change, or remove a student's parent/guardian.
# =========================================================

@app.route("/api/admin/students/<int:student_id>/guardian", methods=["POST"])
@require_admin_api
def api_admin_update_student_guardian(student_id):
    data = request.get_json() or {}

    parent_id = data.get("parent_id")
    admin_id = g.current_admin["user_id"]

    if parent_id == "" or parent_id is None:
        parent_id = None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT student_id, fullname, parent_id
            FROM students
            WHERE student_id = %s
            LIMIT 1
        """, (student_id,))

        student = cursor.fetchone()

        if not student:
            return jsonify({
                "success": False,
                "message": "Student record not found."
            }), 404

        parent = None

        if parent_id:
            cursor.execute("""
                SELECT user_id, fullname, email
                FROM users
                WHERE user_id = %s
                AND role = 'parent'
                AND account_status = 'active'
                LIMIT 1
            """, (parent_id,))

            parent = cursor.fetchone()

            if not parent:
                return jsonify({
                    "success": False,
                    "message": "Selected parent account was not found or is not active."
                }), 404

        cursor.execute("""
            UPDATE students
            SET parent_id = %s
            WHERE student_id = %s
        """, (parent_id, student_id))

        conn.commit()

        if parent:
            action_text = (
                f"Admin linked guardian {parent['fullname']} <{parent['email']}> "
                f"to student {student['fullname']}"
            )
            message = "Guardian linked successfully."
        else:
            action_text = f"Admin removed guardian from student {student['fullname']}"
            message = "Guardian removed successfully."

        log_action(admin_id, action_text)

        return jsonify({
            "success": True,
            "message": message
        })

    except mysql.connector.Error as error:
        conn.rollback()

        print("ADMIN UPDATE STUDENT GUARDIAN ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Unable to update guardian. Please try again."
        }), 400

    finally:
        cursor.close()
        conn.close()
# =========================================================
# ADMIN PERMANENT DELETE USER API
# Requires DELETE confirmation + admin password.
# This is a destructive action and is recorded in audit logs.
# =========================================================

@app.route("/api/admin/users/<int:user_id>/delete", methods=["POST"])
@require_admin_api
def api_admin_delete_user(user_id):
    data = request.get_json() or {}

    confirmation_text = data.get("confirmation_text", "").strip()
    admin_password = data.get("admin_password", "")

    if confirmation_text != "DELETE":
        return jsonify({
            "success": False,
            "message": "Please type DELETE to confirm permanent deletion."
        }), 400

    if not admin_password:
        return jsonify({
            "success": False,
            "message": "Admin password is required."
        }), 400

    admin_id = g.current_admin["user_id"]

    if user_id == admin_id:
        return jsonify({
            "success": False,
            "message": "You cannot delete your own admin account."
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Verify current admin password
        cursor.execute("""
            SELECT user_id, password, role, account_status
            FROM users
            WHERE user_id = %s
            LIMIT 1
        """, (admin_id,))

        admin_user = cursor.fetchone()

        if not admin_user:
            return jsonify({
                "success": False,
                "message": "Admin account not found."
            }), 404

        is_valid_password, needs_upgrade = verify_password(
            admin_user["password"],
            admin_password
        )

        if not is_valid_password:
            return jsonify({
                "success": False,
                "message": "Admin password confirmation failed."
            }), 403

        if needs_upgrade:
            upgraded_hash = hash_password(admin_password)

            cursor.execute("""
                UPDATE users
                SET password = %s
                WHERE user_id = %s
            """, (upgraded_hash, admin_id))

        # Get target user
        cursor.execute("""
            SELECT user_id, fullname, email, role, account_status
            FROM users
            WHERE user_id = %s
            LIMIT 1
        """, (user_id,))

        target_user = cursor.fetchone()

        if not target_user:
            return jsonify({
                "success": False,
                "message": "User account not found."
            }), 404

        # Prevent deleting the only active admin
        if target_user["role"] == "admin":
            cursor.execute("""
                SELECT COUNT(*) AS active_admins
                FROM users
                WHERE role = 'admin'
                AND account_status = 'active'
            """)

            active_admins = cursor.fetchone()["active_admins"]

            if active_admins <= 1:
                return jsonify({
                    "success": False,
                    "message": "You cannot delete the only active admin account."
                }), 400

        deleted_summary = {
            "students": 0,
            "samples": 0,
            "results": 0,
            "reports": 0,
            "validations": 0
        }

        # If deleting a teacher, delete their students and related screening data.
        if target_user["role"] == "teacher":
            cursor.execute("""
                SELECT student_id
                FROM students
                WHERE teacher_id = %s
            """, (user_id,))

            student_ids = [row["student_id"] for row in cursor.fetchall()]
            deleted_summary["students"] = len(student_ids)

            if student_ids:
                student_placeholders = ",".join(["%s"] * len(student_ids))

                cursor.execute(f"""
                    SELECT sample_id
                    FROM handwriting_samples
                    WHERE teacher_id = %s
                    OR student_id IN ({student_placeholders})
                """, tuple([user_id] + student_ids))
            else:
                cursor.execute("""
                    SELECT sample_id
                    FROM handwriting_samples
                    WHERE teacher_id = %s
                """, (user_id,))

            sample_ids = [row["sample_id"] for row in cursor.fetchall()]
            deleted_summary["samples"] = len(sample_ids)

            result_ids = []

            if sample_ids:
                sample_placeholders = ",".join(["%s"] * len(sample_ids))

                cursor.execute(f"""
                    SELECT result_id
                    FROM results
                    WHERE sample_id IN ({sample_placeholders})
                """, tuple(sample_ids))

                result_ids = [row["result_id"] for row in cursor.fetchall()]
                deleted_summary["results"] = len(result_ids)

            if result_ids:
                result_placeholders = ",".join(["%s"] * len(result_ids))

                cursor.execute(f"""
                    SELECT COUNT(*) AS total_reports
                    FROM reports
                    WHERE result_id IN ({result_placeholders})
                """, tuple(result_ids))

                deleted_summary["reports"] = cursor.fetchone()["total_reports"]

                cursor.execute(f"""
                    SELECT COUNT(*) AS total_validations
                    FROM validations
                    WHERE result_id IN ({result_placeholders})
                """, tuple(result_ids))

                deleted_summary["validations"] = cursor.fetchone()["total_validations"]

                cursor.execute(f"""
                    DELETE FROM reports
                    WHERE result_id IN ({result_placeholders})
                """, tuple(result_ids))

                cursor.execute(f"""
                    DELETE FROM validations
                    WHERE result_id IN ({result_placeholders})
                """, tuple(result_ids))

                cursor.execute(f"""
                    DELETE FROM results
                    WHERE result_id IN ({result_placeholders})
                """, tuple(result_ids))

            if sample_ids:
                sample_placeholders = ",".join(["%s"] * len(sample_ids))

                cursor.execute(f"""
                    DELETE FROM handwriting_samples
                    WHERE sample_id IN ({sample_placeholders})
                """, tuple(sample_ids))

            if student_ids:
                student_placeholders = ",".join(["%s"] * len(student_ids))

                cursor.execute(f"""
                    DELETE FROM students
                    WHERE student_id IN ({student_placeholders})
                """, tuple(student_ids))

        # If deleting a parent, keep students but unlink the parent account.
        if target_user["role"] == "parent":
            cursor.execute("""
                UPDATE students
                SET parent_id = NULL
                WHERE parent_id = %s
            """, (user_id,))

        # If deleting an expert, keep validations but remove expert reference.
        if target_user["role"] == "expert":
            cursor.execute("""
                UPDATE validations
                SET expert_id = NULL
                WHERE expert_id = %s
            """, (user_id,))

        # Preserve audit logs but remove direct user reference.
        cursor.execute("""
            UPDATE audit_logs
            SET user_id = NULL
            WHERE user_id = %s
        """, (user_id,))

        # Delete password reset tokens for this user if any exist.
        cursor.execute("""
            DELETE FROM password_reset_tokens
            WHERE user_id = %s
        """, (user_id,))

        # Permanently delete the user.
        cursor.execute("""
            DELETE FROM users
            WHERE user_id = %s
        """, (user_id,))

        conn.commit()

        log_action(
            admin_id,
            (
                "PERMANENT DELETE USER: "
                f"{target_user['fullname']} <{target_user['email']}> "
                f"role={target_user['role']}. "
                f"Deleted related records: "
                f"students={deleted_summary['students']}, "
                f"samples={deleted_summary['samples']}, "
                f"results={deleted_summary['results']}, "
                f"reports={deleted_summary['reports']}, "
                f"validations={deleted_summary['validations']}."
            )
        )

        return jsonify({
            "success": True,
            "message": "User account permanently deleted successfully.",
            "deleted_summary": deleted_summary
        })

    except mysql.connector.Error as error:
        conn.rollback()

        print("ADMIN DELETE USER ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Unable to permanently delete user. Please check linked records or database constraints."
        }), 400

    finally:
        cursor.close()
        conn.close()
# =========================================================
# 17. VUE ADMIN RESULTS API
# =========================================================

@app.route("/api/admin/results", methods=["GET"])
@require_admin_api
def api_admin_results():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            r.result_id,
            r.classification,
            r.dysgraphia_probability,
            r.confidence_score,
            r.date_generated,
            s.fullname AS student_name,
            s.grade_level,
            teacher.fullname AS teacher_name,
            parent.fullname AS parent_name,
            v.validation_status
        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        JOIN students s ON hs.student_id = s.student_id
        JOIN users teacher ON hs.teacher_id = teacher.user_id
        LEFT JOIN users parent ON s.parent_id = parent.user_id
        LEFT JOIN validations v ON r.result_id = v.result_id
        ORDER BY r.date_generated DESC
    """)

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    for result in results:
        if result["date_generated"]:
            result["date_generated"] = str(result["date_generated"])

        if result["validation_status"] is None:
            result["validation_status"] = "Pending"

    return jsonify({
        "success": True,
        "results": results
    })


@app.route("/api/admin/results/<int:result_id>", methods=["GET"])
@require_admin_api
def api_admin_result_detail(result_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            r.result_id,
            r.dysgraphia_probability,
            r.classification,
            r.confidence_score,
            r.analysis_summary,
            r.date_generated,

            hs.image_path,

            s.fullname AS student_name,
            s.age,
            s.grade_level,

            teacher.fullname AS teacher_name,
            parent.fullname AS parent_name,

            COALESCE(v.validation_status, 'Pending') AS validation_status,
            COALESCE(v.remarks, '') AS remarks,
            COALESCE(v.expert_recommendation, '') AS expert_recommendation,
            COALESCE(v.follow_up_needed, 'No') AS follow_up_needed,
            v.validation_date,

            expert.fullname AS expert_name

        FROM results r
        JOIN handwriting_samples hs ON r.sample_id = hs.sample_id
        JOIN students s ON hs.student_id = s.student_id
        JOIN users teacher ON hs.teacher_id = teacher.user_id
        LEFT JOIN users parent ON s.parent_id = parent.user_id
        LEFT JOIN validations v ON r.result_id = v.result_id
        LEFT JOIN users expert ON v.expert_id = expert.user_id
        WHERE r.result_id = %s
    """, (result_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if not result:
        return jsonify({
            "success": False,
            "message": "Result not found."
        }), 404

    if result["date_generated"]:
        result["date_generated"] = str(result["date_generated"])

    if result["validation_date"]:
        result["validation_date"] = str(result["validation_date"])

        result["image_url"] = build_image_url(result.get("image_path"))

    return jsonify({
        "success": True,
        "result": result
    })


# =========================================================
# 18. VUE ADMIN AUDIT LOGS API
# =========================================================

@app.route("/api/admin/audit-logs", methods=["GET"])
@require_admin_api
def api_admin_audit_logs():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            a.log_id,
            a.action,
            a.log_date,
            u.fullname,
            u.email,
            u.role
        FROM audit_logs a
        LEFT JOIN users u ON a.user_id = u.user_id
        ORDER BY a.log_date DESC
    """)

    logs = cursor.fetchall()

    cursor.close()
    conn.close()

    for log in logs:
        if log["log_date"]:
            log["log_date"] = str(log["log_date"])

        if log["fullname"] is None:
            log["fullname"] = "Unknown User"

        if log["email"] is None:
            log["email"] = "N/A"

        if log["role"] is None:
            log["role"] = "unknown"

    return jsonify({
        "success": True,
        "logs": logs
    })

@app.route("/api/user/health", methods=["GET"])
def api_user_health():
    return jsonify({
        "success": True,
        "message": "GRAPHISCAN user API is running."
    })


# =========================================================
# 20. LOGOUT
# =========================================================

@app.route("/logout")
def logout():
    if "user_id" in session:
        log_action(session["user_id"], "User logged out")

    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# =========================================================
# 21. RUN APP
# =========================================================


if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
