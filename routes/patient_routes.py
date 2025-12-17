import psycopg2
from flask import Blueprint, render_template, request, redirect, url_for, flash, json, current_app
import uuid
import os
from blockchain import HospitalChain
from db_config import get_db_connection
from utils import get_file_hash, allowed_file
from werkzeug.utils import secure_filename

patient_bp = Blueprint('patient', __name__)

blockchain_system = HospitalChain()


@patient_bp.route('/register_patient', methods=['GET', 'POST'])
def register_patient():
    if request.method == 'POST':
        national_id = request.form['national_id']
        name = request.form['name']
        surname = request.form['surname']
        date_of_birth = request.form['date_of_birth']
        gender = request.form['gender']
        blood_type = request.form['blood_type']

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO patients (national_id, name, surname, date_of_birth, gender, blood_type)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (national_id, name, surname, date_of_birth, gender, blood_type))

            conn.commit()
            flash(f"{name} {surname} başarıyla sisteme kaydedildi. Şimdi muayene girebilirsiniz.", "success")
            return redirect(url_for('main.index'))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash("Hata: Bu TC Kimlik Numarası ile zaten bir hasta kayıtlı!", "danger")
        except Exception as e:
            conn.rollback()
            flash(f"Bir hata oluştu: {e}", "danger")
        finally:
            cur.close()
            conn.close()

    return render_template('register_patient.html')

@patient_bp.route('/add_record', methods=['GET', 'POST'])
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
                    cur.execute("SELECT id FROM patients WHERE national_id = %s", (national_id,))
                    patient = cur.fetchone()
                    if not patient:
                        flash("Hata: Bu TC ile kayıtlı hasta bulunamadı!", "danger")
                        return redirect(url_for('patient.add_record'))
                    patient_id = patient[0]
                    cur.execute("SELECT record_hash FROM patient_records ORDER BY created_at DESC LIMIT 1")
                    last_record = cur.fetchone()
                    last_hash = last_record[0] if last_record else "0" * 16
                    last_index = 1
                    medical_data = {
                        "diagnosis": diagnosis,
                        "treatment": treatment,
                        "file_hash": file_hash if file_hash else "Yok"
                    }
                    new_block = blockchain_system.create_new_block(
                        data=medical_data,
                        last_block_hash=last_hash,
                        last_index=last_index
                    )
                    cur.execute("SELECT id FROM users LIMIT 1")
                    user_id = cur.fetchone()[0]
                    cur.execute("""
                        INSERT INTO patient_records 
                        (patient_id, created_by, record_type, record_data, record_hash, previous_record_hash)
                        VALUES (%s, %s, 'Muayene', %s, %s, %s)
                        RETURNING id
                    """, (
                        patient_id, user_id, json.dumps(medical_data), new_block.hash, last_hash
                    ))
                    record_id = cur.fetchone()[0]
                    if filename:
                        cur.execute("""
                            INSERT INTO record_files (record_id, file_name, file_hash, storage_path)
                            VALUES (%s, %s, %s, %s)
                        """, (record_id, unique_filename, file_hash, file_path))
            flash("Kayıt ve dosya başarıyla Blockchain'e işlendi!", "success")
            return redirect(url_for('main.index'))

        except Exception as e:
            flash(f"Hata oluştu: {str(e)}", "danger")
        finally:
            if conn:
                conn.close()

    return render_template('add.html')

@patient_bp.route('/patient/<string:patient_id>')
def patient_detail(patient_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cur.fetchone()

    if not patient:
        flash("Hasta bulunamadı.", "danger")
        return redirect(url_for('main.index'))
    cur.execute("""
        SELECT pr.record_data, pr.record_hash, pr.previous_record_hash, pr.created_at, 
               u.name, u.surname, u.title -- title (unvan) tablonuzda varsa ekleyin, yoksa kaldırın
        FROM patient_records pr
        JOIN users u ON pr.created_by = u.id
        WHERE pr.patient_id = %s
        ORDER BY pr.created_at DESC
    """, (patient_id,))

    records = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('patient_detail.html', patient=patient, records=records)