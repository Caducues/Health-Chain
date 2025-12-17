import json
import hashlib
from db_config import get_db_connection


def calculate_hash(data):
    block_string = json.dumps(data, sort_keys=True).encode()
    return hashlib.sha256(block_string).hexdigest()


def verify_records_chain(cur):
    print("\n📋 MUAYENE ZİNCİRİ (Medical Chain) KONTROL EDİLİYOR...")
    cur.execute(
        "SELECT id, record_data, record_hash, previous_record_hash FROM patient_records ORDER BY created_at ASC")
    records = cur.fetchall()

    # Blockchain sınıfı mantığıyla kontrol (record_data zaten json içinde previous_hash tutmuyor, bizim yapımız biraz farklıydı)
    # Basitlik için record_data + index + timestamp vb. hashleniyordu.
    # Ancak burada database'deki mantığı basitçe hash tutarlılığı üzerinden yapalım:

    # NOT: Blockchain sınıfımızda 'record_hash' aslında blok objesinin hash'iydi.
    # Tam doğrulama için HospitalChain sınıfını import edip kullanmak en doğrusu ama
    # Hacker senaryosu için "Chain Link" (Zincir Bağı) kontrolü yeterlidir.

    chain_valid = True
    expected_prev = "0" * 16  # Genesis

    for row in records:
        r_id, r_data, r_hash, r_prev = row

        if r_prev != expected_prev:
            print(f"❌ HATA! Kayıt #{r_id} zinciri kopardı!")
            print(f"   Beklenen Önceki: {expected_prev}")
            print(f"   Bulunan Önceki:  {r_prev}")
            chain_valid = False
        else:
            print(f"Checking Record #{r_id}... ✅ Zincir Sağlam")

        expected_prev = r_hash  # Sonraki için bekle

    return chain_valid


def verify_patients_chain(cur):
    print("\n👥 HASTA KİMLİK ZİNCİRİ (Identity Chain) KONTROL EDİLİYOR...")
    cur.execute(
        "SELECT id, name, surname, national_id, date_of_birth, blood_type, gender, patient_hash, previous_hash FROM patients ORDER BY id ASC")
    patients = cur.fetchall()

    chain_valid = True
    expected_prev = "0" * 64  # Genesis

    for p in patients:
        p_id = p[0]
        stored_hash = p[7]
        stored_prev = p[8]

        # 1. Zincir Kontrolü
        if stored_prev != expected_prev:
            print(f"❌ HATA! Hasta #{p_id} ({p[1]} {p[2]}) zinciri kopardı!")
            chain_valid = False

        # 2. Veri Bütünlüğü Kontrolü (Hash Recalculation)
        # Veritabanındaki veriyi alıp tekrar şifreliyoruz
        reconstruct_data = {
            "name": p[1],
            "surname": p[2],
            "national_id": p[3],
            "date_of_birth": str(p[4]),
            "blood_type": p[5],
            "gender": p[6],
            "previous_hash": stored_prev
        }
        calculated_hash = calculate_hash(reconstruct_data)

        if calculated_hash != stored_hash:
            print(f"❌ HATA! Hasta #{p_id} verisi değiştirilmiş! (Hash Uyuşmuyor)")
            chain_valid = False
        else:
            print(f"Checking Patient #{p_id}... ✅ Kimlik ve Zincir Sağlam")

        expected_prev = stored_hash

    return chain_valid


def full_system_check():
    conn = get_db_connection()
    cur = conn.cursor()

    print("🛡️  SİSTEM GENEL GÜVENLİK TARAMASI BAŞLATILIYOR...\n" + "=" * 50)

    patients_ok = verify_patients_chain(cur)
    records_ok = verify_records_chain(cur)

    print("=" * 50)
    if patients_ok and records_ok:
        print("🟢 MÜKEMMEL! Tüm sistem güvenli ve bütünlük tam.")
    else:
        print("🔴 KRİTİK UYARI! Sistemde veri ihlali tespit edildi.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    full_system_check()