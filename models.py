from flask_login import UserMixin
from db_config import get_db_connection


class User(UserMixin):
    def __init__(self, id, username, name, surname, role_name):
        self.id = id
        self.username = username
        self.name = name
        self.surname = surname
        self.role_name = role_name

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id, u.username, u.name, u.surname, r.name 
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.id = %s
        """, (user_id,))

        user_data = cur.fetchone()
        cur.close()
        conn.close()

        if not user_data:
            return None

        return User(
            id=user_data[0],
            username=user_data[1],
            name=user_data[2],
            surname=user_data[3],
            role_name=user_data[4]
        )