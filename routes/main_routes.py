from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from db_config import get_db_connection
from blockchain import HospitalChain
from flask import request

from migration_patients import calculate_hash

main_bp = Blueprint('main', __name__)
blockchain_system = HospitalChain()


# routes/main_routes.py


@main_bp.route('/')
# DİKKAT: @login_required BURADAN KALDIRILDI!
def index():
    # SENARYO 1: Kullanıcı giriş yapmamışsa (Misafir) -> Havalı Tanıtım Sayfasını Göster
    if not current_user.is_authenticated:
        return render_template('landing.html')

    # SENARYO 2: Kullanıcı giriş yapmışsa (Doktor) -> Blockchain Panelini Göster
    # (Aşağısı eski kodunun aynısı)
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Hasta Sayısı (Aynı zamanda Identity Chain Blok Sayısıdır)
    cur.execute("SELECT COUNT(*) FROM patients")
    total_patients = cur.fetchone()[0]

    # 2. Muayene Sayısı (Medical Chain Blok Sayısı)
    cur.execute("SELECT COUNT(*) FROM patient_records")
    total_records = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users")
    total_doctors = cur.fetchone()[0]

    # 3. YENİ HESAPLAMA: Toplam Blok Sayısı (İkisinin Toplamı)
    total_blocks = total_patients + total_records

    # --- ARAMA ve LİSTELEME ---
    search_query = request.args.get('q')

    if search_query:
        search_term = f"%{search_query}%"

        # 1. Muayene Kayıtlarını Ara
        # (Muayeneler tarihe göre sıralı kalmalı, burayı ellemiyoruz)
        cur.execute("""
                SELECT p.name, p.surname, pr.record_data, pr.record_hash, pr.previous_record_hash, pr.created_at, p.id, p.national_id
                FROM patient_records pr
                JOIN patients p ON pr.patient_id = p.id
                WHERE 
                    p.name ILIKE %s OR 
                    p.surname ILIKE %s OR 
                    p.national_id LIKE %s OR
                    CONCAT(p.name, ' ', p.surname) ILIKE %s
                ORDER BY pr.created_at DESC
            """, (search_term, search_term, search_term, search_term))
        records = cur.fetchall()

        # 2. Hasta Listesini Ara (A-Z SIRALAMA BURADA)
        cur.execute("""
                SELECT id, name, surname, national_id, blood_type, gender, date_of_birth 
                FROM patients 
                WHERE 
                    name ILIKE %s OR 
                    surname ILIKE %s OR 
                    national_id LIKE %s OR
                    CONCAT(name, ' ', surname) ILIKE %s
                ORDER BY name ASC, surname ASC  -- <--- DEĞİŞİKLİK 1 (İsim A-Z, sonra Soyisim A-Z)
            """, (search_term, search_term, search_term, search_term))
        patients = cur.fetchall()

    else:
        # Arama yoksa varsayılan listeler

        # Son Muayeneler (Tarihe göre kalmalı)
        cur.execute("""
                SELECT p.name, p.surname, pr.record_data, pr.record_hash, pr.previous_record_hash, pr.created_at, p.id, p.national_id
                FROM patient_records pr
                JOIN patients p ON pr.patient_id = p.id
                ORDER BY pr.created_at DESC
                LIMIT 20
            """)
        records = cur.fetchall()

        # Tüm Hastalar (A-Z SIRALAMA BURADA)
        # Not: LIMIT'i kaldırdım ki 'A' ile başlayan ama eski kayıt olanlar da görünsün.
        cur.execute("""
                SELECT id, name, surname, national_id, blood_type, gender, date_of_birth 
                FROM patients 
                ORDER BY name ASC, surname ASC -- <--- DEĞİŞİKLİK 2
            """)
        patients = cur.fetchall()

    cur.close()
    conn.close()

    # ... (Return kısmı aynı kalsın) ...
    return render_template('index.html',
                           records=records,
                           patients=patients,
                           user=current_user,
                           stats={
                               'patients': total_patients,
                               'records': total_records,
                               'doctors': total_doctors,
                               'blocks': total_blocks
                           })

@main_bp.route('/verify')
@login_required
def verify_system():
    conn = get_db_connection()
    cur = conn.cursor()

    # --- 1. HASTA KİMLİK ZİNCİRİ KONTROLÜ ---
    patient_results = []
    patients_chain_valid = True

    cur.execute(
        "SELECT id, name, surname, national_id, date_of_birth, blood_type, gender, patient_hash, previous_hash FROM patients ORDER BY id ASC")
    patients = cur.fetchall()

    expected_prev_patient = "0" * 64  # Genesis Hash

    for p in patients:
        p_id = p[0]
        p_name = f"{p[1]} {p[2]}"
        stored_hash = p[7]
        stored_prev = p[8]

        status = "Geçerli"
        is_valid = True
        error_msg = ""

        # A) Zincir Bağlantısı Kontrolü
        if stored_prev != expected_prev_patient:
            status = "KIRILDI"
            is_valid = False
            error_msg = "Zincir kopukluğu tespit edildi! (Previous Hash uyuşmazlığı)"
            patients_chain_valid = False

        # B) Veri Bütünlüğü Kontrolü (Hash Hesaplama)
        if is_valid:  # Zincir zaten koptuysa bunu kontrol etmeye gerek yok
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
                status = "DEĞİŞTİRİLDİ"
                is_valid = False
                error_msg = "Veri bütünlüğü bozulmuş! (Hash uyuşmuyor, veritabanına müdahale edilmiş)"
                patients_chain_valid = False

        patient_results.append({
            "id": p_id,
            "name": p_name,
            "status": status,
            "valid": is_valid,
            "error": error_msg
        })

        expected_prev_patient = stored_hash

    # --- 2. MUAYENE ZİNCİRİ KONTROLÜ ---
    record_results = []
    records_chain_valid = True

    cur.execute("""
        SELECT pr.id, p.name, p.surname, pr.record_hash, pr.previous_record_hash 
        FROM patient_records pr
        JOIN patients p ON pr.patient_id = p.id
        ORDER BY pr.created_at ASC
    """)
    records = cur.fetchall()

    expected_prev_record = "0" * 16  # Genesis Hash (Record için 16 karakter kullanmıştık)

    for r in records:
        r_id = r[0]
        r_patient_name = f"{r[1]} {r[2]}"
        stored_hash = r[3]
        stored_prev = r[4]

        status = "Geçerli"
        is_valid = True
        error_msg = ""

        # Zincir Kontrolü
        if stored_prev != expected_prev_record:
            status = "KIRILDI"
            is_valid = False
            error_msg = "Muayene zinciri kopmuş!"
            records_chain_valid = False

        record_results.append({
            "id": r_id,
            "patient": r_patient_name,
            "status": status,
            "valid": is_valid,
            "error": error_msg
        })

        expected_prev_record = stored_hash

    cur.close()
    conn.close()

    return render_template('verify.html',
                           patient_results=patient_results,
                           record_results=record_results,
                           patients_valid=patients_chain_valid,
                           records_valid=records_chain_valid)