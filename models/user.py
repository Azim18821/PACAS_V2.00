
from flask_login import UserMixin
from utils.database import Database
import bcrypt

class User(UserMixin):
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email 
        self.password_hash = password_hash
        
    @staticmethod
    def get_by_id(user_id):
        db = Database()
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if user:
                return User(user[0], user[1], user[2], user[3])
        return None

    @staticmethod
    def get_by_email(email):
        db = Database()
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            if user:
                return User(user[0], user[1], user[2], user[3])
        return None

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash)
