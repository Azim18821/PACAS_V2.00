
import sqlite3
from flask_login import UserMixin
from utils.database import Database
import bcrypt

class User(UserMixin):
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        # Ensure password_hash is bytes
        self.password_hash = password_hash if isinstance(password_hash, bytes) else bytes(password_hash)
        
    @staticmethod
    def get_by_id(user_id):
        db = Database()
        try:
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
                user = cursor.fetchone()
                if user:
                    return User(user[0], user[1], user[2], user[3])
        except Exception as e:
            print(f"Error getting user by ID: {e}")
        return None

    @staticmethod
    def get_by_email(email):
        db = Database()
        try:
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
                user = cursor.fetchone()
                if user:
                    return User(user[0], user[1], user[2], user[3])
        except Exception as e:
            print(f"Error getting user by email: {e}")
        return None

    @staticmethod
    def create_user(username, email, password):
        db = Database()
        try:
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.cursor()
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                             (username, email, password_hash))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash)
