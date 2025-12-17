import psycopg2
from flask import Blueprint, render_template, request, redirect, url_for, flash, json, current_app
import uuid
import os
import json
from blockchain import HospitalChain

from flask_login import current_user, login_required

from blockchain import HospitalChain
from db_config import get_db_connection
from decorators import doctor_required
from utils import get_file_hash, allowed_file
from werkzeug.utils import secure_filename


patient_bp = Blueprint('patient', __name__)

blockchain_system = HospitalChain()


@patient_bp.route('/register_patient', methods=['GET', 'POST'])
@login_required
def register_patient():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        national_id = request.form['national_id']
        gender = request.form['gender']
        date_of_birth = request.form['date_of_birth']
        blood_type = request.form.get('blood_type', 'Bilinmiyor')

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # 1. ZİNCİRİN SON HALKASINI BUL
            # En son eklenen hastanın hash'ini çekiyoruz
            cur.execute("SELECT patient_hash FROM patients ORDER BY id DESC LIMIT 1")
            last_patient = cur.fetchone()

            # Eğer hiç hasta yoksa önceki hash "000..." dır (Genesis)
            previous_hash = last_patient[0] if last_patient and last_patient[0] else "0" * 64

            # 2. YENİ BLOK VERİSİNİ HAZIRLA
            # Blockchain sınıfındaki 'calculate_hash' metodunu kullanmak için:
            # (HospitalChain sınıfının instance'ını kullanabiliriz veya manuel hesaplayabiliriz)
            # Tutarlılık için manuel paketleyip hashleyeceğiz.

            patient_data_block = {
                "name": name,
                "surname": surname,
                "national_id": national_id,
                "date_of_birth": date_of_birth,  # String olarak gelir
                "blood_type": blood_type,
                "gender": gender,
                "previous_hash": previous_hash
            }

            # Hash Hesapla (Blockchain sınıfındaki logic'i simüle ediyoruz)
            import hashlib
            block_string = json.dumps(patient_data_block, sort_keys=True).encode()
            current_hash = hashlib.sha256(block_string).hexdigest()

            # 3. VERİTABANINA KAYDET (Hash'lerle Birlikte!)
            cur.execute("""
                INSERT INTO patients 
                (name, surname, national_id, date_of_birth, gender, blood_type, patient_hash, previous_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, surname, national_id, date_of_birth, gender, blood_type, current_hash, previous_hash))

            conn.commit()
            flash('Hasta Kimlik Zincirine eklendi ve güvenle saklandı!', 'success')
            return redirect(url_for('main.index'))

        except psycopg2.IntegrityError:
            conn.rollback()
            flash('Bu TC Kimlik numarası ile kayıtlı bir hasta zaten var.', 'danger')
        except Exception as e:
            conn.rollback()
            flash(f'Bir hata oluştu: {e}', 'danger')
        finally:
            cur.close()
            conn.close()

    return render_template('register_patient.html')


@patient_bp.route('/add_record', methods=['GET', 'POST'])
@login_required
def add_record():
    if request.method == 'POST':
        national_id = request.form['national_id']
        diagnosis = request.form['diagnosis']
        treatment = request.form['treatment']
        file = request.files.get('file')
        filename = None
        file_hash = None
        file_path = None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            file_hash = get_file_hash(file_path)

        conn = get_db_connection()

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, name, surname, blood_type FROM patients WHERE national_id = %s",
                                (national_id,))
                    patient = cur.fetchone()
                    if not patient:
                        flash("Hata: Bu TC ile kayıtlı hasta bulunamadı!", "danger")
                        return redirect(url_for('patient.add_record'))
                    patient_id = patient[0]
                    patient_name = patient[1]
                    patient_surname = patient[2]
                    # Kan grubu boşsa 'Bilinmiyor' yazsın
                    patient_blood = patient[3] if patient[3] else "Bilinmiyor"
                    cur.execute("SELECT record_hash FROM patient_records ORDER BY created_at DESC LIMIT 1")
                    last_record = cur.fetchone()
                    last_hash = last_record[0] if last_record else "0" * 16
                    last_index = 1
                    medical_data = {
                        "patient_tc": national_id,
                        "patient_name": f"{patient_name} {patient_surname}",
                        "blood_type": patient_blood,  # <--- İşte buraya ekledik!
                        "diagnosis": diagnosis,
                        "treatment": treatment,
                        "doctor": f"{current_user.name} {current_user.surname}",
                        "file_hash": file_hash if file_hash else "Yok"
                    }
                    new_block = blockchain_system.create_new_block(
                        data=medical_data,
                        last_block_hash=last_hash,
                        last_index=last_index
                    )
                    cur.execute("""
                        INSERT INTO patient_records 
                        (patient_id, created_by, record_type, record_data, record_hash, previous_record_hash)
                        VALUES (%s, %s, 'Muayene', %s, %s, %s)
                        RETURNING id
                    """, (
                        patient_id, current_user.id, json.dumps(medical_data), new_block.hash, last_hash
                    ))
                    record_id = cur.fetchone()[0]
                    if filename:
                        cur.execute("""
                            INSERT INTO record_files (record_id, file_name, file_hash, storage_path)
                            VALUES (%s, %s, %s, %s)
                        """, (record_id, unique_filename, file_hash, file_path))

            flash("Kayıt, kimlik ve kan grubu bilgileriyle mühürlendi!", "success")
            return redirect(url_for('main.index'))

        except Exception as e:
            flash(f"Hata oluştu: {str(e)}", "danger")
        finally:
            if conn:
                conn.close()

    return render_template('add.html')


@patient_bp.route('/add_patient', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        national_id = request.form['national_id']
        birth_year = request.form['birth_year']
        gender = request.form['gender']
        blood_type = request.form.get('blood_type', 'Bilinmiyor')
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO patients (name, surname, national_id, birth_year, gender, blood_type)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, surname, national_id, birth_year, gender, blood_type))

            conn.commit()
            flash('Hasta ve Kan Grubu başarıyla eklendi!', 'success')
            return redirect(url_for('main.index'))

        except psycopg2.IntegrityError:
            conn.rollback()
            flash('Bu TC Kimlik numarası ile kayıtlı bir hasta zaten var.', 'danger')
        finally:
            cur.close()
            conn.close()

    return render_template('add_patient.html')


@patient_bp.route('/patient/<string:patient_id>')
@login_required
@doctor_required
def patient_detail(patient_id):

    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Hasta bilgilerini çek
    cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cur.fetchone()

    if not patient:
        flash("Hasta bulunamadı.", "danger")
        return redirect(url_for('main.index'))

    # 2. Hastanın kayıtlarını çek
    # DÜZELTME: 'u.title' kaldırıldı.
    # DÜZELTME: Dosya bilgileri (rf.file_name) eklendi.
    cur.execute("""
        SELECT pr.record_data, pr.record_hash, pr.previous_record_hash, pr.created_at, 
               u.name, u.surname, rf.file_name, rf.storage_path, r.name as role_name
        FROM patient_records pr
        JOIN users u ON pr.created_by = u.id
        LEFT JOIN record_files rf ON pr.id = rf.record_id
        JOIN roles r ON u.role_id = r.id  -- <--- BU SATIR EKLENDİ (Rol ismini çekmek için)
        WHERE pr.patient_id = %s
        ORDER BY pr.created_at DESC
    """, (patient_id,))

    records = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('patient_detail.html', patient=patient, records=records)

@patient_bp.route('/patients')
@login_required
def all_patients():
    conn = get_db_connection()
    cur = conn.cursor()

    # Sadece hastalar tablosunu çekiyoruz (Blockchain kaydı olsun olmasın)
    cur.execute(
        "SELECT id, name, surname, national_id, date_of_birth, blood_type, gender FROM patients ORDER BY id DESC")
    patients = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('patients.html', patients=patients)