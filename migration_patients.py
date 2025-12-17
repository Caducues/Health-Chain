import json
import hashlib  # Hash hesaplamak için
from db_config import get_db_connection


def calculate_hash(data):
    # Veriyi stringe çevirip SHA256 ile şifreler
    block_string = json.dumps(data, sort_keys=True).encode()
    return hashlib.sha256(block_string).hexdigest()


def migrate_patients_table():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        print("🔄 Patients tablosu Blockchain yapısına dönüştürülüyor...")

        # 1. Sütunları Ekle (Eğer yoksa)
        cur.execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS patient_hash VARCHAR(64)")
        cur.execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS previous_hash VARCHAR(64)")
        conn.commit()

        # 2. Mevcut Hastaları Zincirle (Genesis'ten başlayarak)
        cur.execute(
            "SELECT id, name, surname, national_id, date_of_birth, blood_type, gender FROM patients ORDER BY id ASC")
        patients = cur.fetchall()

        previous_hash = "0" * 64  # İlk hastanın önceki hash'i 0'dır (Genesis)

        for p in patients:
            p_id = p[0]
            # Blok Verisi
            patient_data = {
                "name": p[1],
                "surname": p[2],
                "national_id": p[3],
                "date_of_birth": str(p[4]),
                "blood_type": p[5],
                "gender": p[6],
                "previous_hash": previous_hash
            }

            # Hash Hesapla
            current_hash = calculate_hash(patient_data)

            # Veritabanını Güncelle
            cur.execute("""
                UPDATE patients 
                SET patient_hash = %s, previous_hash = %s
                WHERE id = %s
            """, (current_hash, previous_hash, p_id))

            print(f"🔗 Hasta #{p_id} zincire eklendi. Hash: {current_hash[:10]}...")

            # Bir sonraki tur için bu hash'i sakla
            previous_hash = current_hash

        conn.commit()
        print("✅ Başarılı! Tüm hastalar artık bir Blockchain zinciri oluşturuyor.")

    except Exception as e:
        print(f"❌ Hata: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    migrate_patients_table()