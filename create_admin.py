from werkzeug.security import generate_password_hash
from db_config import get_db_connection


def create_super_admin():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO departments (name, location_code) VALUES ('Yönetim', 'Kat 5') ON CONFLICT (name) DO NOTHING")
        cur.execute(
            "INSERT INTO roles (name, description) VALUES ('Admin', 'Tam Yetkili Yönetici') ON CONFLICT (name) DO NOTHING")
        conn.commit()
        cur.execute("SELECT id FROM departments WHERE name = 'Yönetim'")
        dept_id = cur.fetchone()[0]
        cur.execute("SELECT id FROM roles WHERE name = 'Admin'")
        role_id = cur.fetchone()[0]
        USERNAME = "admintaha"
        PASSWORD = "123456"
        NAME = "Taha"
        SURNAME = "Admin"
        EMAIL = "admintaha@hastane.com"
        hashed_pw = generate_password_hash(PASSWORD)
        cur.execute("SELECT id FROM users WHERE username = %s", (USERNAME,))
        existing_user = cur.fetchone()
        if existing_user:
            print(f"⚠️  '{USERNAME}' kullanıcısı zaten var. Şifresi ve yetkisi güncelleniyor...")
            cur.execute("""
                UPDATE users 
                SET password_hash = %s, role_id = %s, department_id = %s
                WHERE username = %s
            """, (hashed_pw, role_id, dept_id, USERNAME))
        else:
            print(f"➕ '{USERNAME}' kullanıcısı sıfırdan oluşturuluyor...")
            cur.execute("""
                INSERT INTO users (department_id, role_id, name, surname, username, password_hash, e_mail)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (dept_id, role_id, NAME, SURNAME, USERNAME, hashed_pw, EMAIL))
        conn.commit()
        print(f"   Kullanıcı Adı: {USERNAME}")
        print(f"   Şifre:         {PASSWORD}")
    except Exception as e:
        conn.rollback()
        print(f"{e}")
    finally:
        cur.close()
        conn.close()
if __name__ == "__main__":
    create_super_admin()