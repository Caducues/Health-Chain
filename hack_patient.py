# hack_patient.py
from db_config import get_db_connection


def hack_patient_data():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Son eklenen hastayı bul
        cur.execute("SELECT id, name, blood_type FROM patients ORDER BY id DESC LIMIT 1")
        target = cur.fetchone()

        if target:
            p_id, name, old_blood = target
            print(f"🎯 Hedef Hasta: {name} (ID: {p_id})")
            print(f"🩸 Eski Kan Grubu: {old_blood}")

            # KÖTÜ NİYETLİ DEĞİŞİKLİK: Kan grubunu değiştiriyoruz ama HASH'i güncellemiyoruz!
            new_blood = "X Rh-"  # Sahte bir kan grubu

            cur.execute("UPDATE patients SET blood_type = %s WHERE id = %s", (new_blood, p_id))
            conn.commit()

            print(f"😈 SALDIRI BAŞARILI! Kan grubu '{new_blood}' olarak değiştirildi.")
            print("   (Ancak Hash ve Previous Hash güncellenmedi, iz bıraktık!)")
        else:
            print("Hiç hasta yok, saldırı iptal.")

    except Exception as e:
        print(f"Hata: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    hack_patient_data()