import psycopg2
from dotenv import load_dotenv
import os
load_dotenv()
DB_HOST = "localhost"
DB_NAME =  os.getenv("DATABASE_NAME")
DB_USER = "postgres"
DB_PASS =  os.getenv("DATABASE_PASS")


def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        return conn
    except Exception as e:
        print(f"Veritabanı bağlantı hatası: {e}")
        return None


def init_db_test():
    conn = get_db_connection()
    if conn:
        print("Başarılı: Veritabanına bağlanıldı!")
        cur = conn.cursor()
        cur.execute('SELECT version();')
        db_version = cur.fetchone()
        print(f"Veritabanı Versiyonu: {db_version[0]}")

        cur.close()
        conn.close()
    else:
        print("Bağlantı kurulamadı.")
if __name__ == "__main__":
    init_db_test()