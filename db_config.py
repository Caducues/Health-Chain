import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
load_dotenv()
# Veritabanı Ayarları
DB_HOST = "localhost"
DB_NAME =  os.getenv("DATABASE_NAME")  # Veritabanını oluştururken verdiğin isim
DB_USER = "postgres"  # Genelde varsayılan kullanıcı 'postgres'tir
DB_PASS =  os.getenv("DATABASE_PASS") # BURAYA KENDİ ŞİFRENİ YAZ


def get_db_connection():
    """
    Veritabanına bağlanır ve bağlantı nesnesini döndürür.
    """
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
    """
    Bağlantıyı test etmek için basit bir fonksiyon.
    """
    conn = get_db_connection()
    if conn:
        print("✅ Başarılı: Veritabanına bağlanıldı!")

        # Basit bir sorgu ile versiyon kontrolü yapalım
        cur = conn.cursor()
        cur.execute('SELECT version();')
        db_version = cur.fetchone()
        print(f"Veritabanı Versiyonu: {db_version[0]}")

        cur.close()
        conn.close()
    else:
        print("❌ Hata: Bağlantı kurulamadı.")


# Bu dosya doğrudan çalıştırılırsa testi başlat
if __name__ == "__main__":
    init_db_test()