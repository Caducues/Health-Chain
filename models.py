from flask_login import UserMixin
from db_config import get_db_connection

class User(UserMixin):
    def __init__(self, id, username, name, role_id):
        self.id = id
        self.username = username
        self.name = name
        self.role_id = role_id

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, name, role_id FROM users WHERE id = %s", (user_id,))
        user_data = cur.fetchone()
        cur.close()
        conn.close()

        if not user_data:
            return None
        return User(
            id=user_data[0],
            username=user_data[1],
            name=user_data[2],
            role_id=user_data[3]
        )