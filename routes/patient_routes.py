import psycopg2
from flask import Blueprint, render_template, request, redirect, url_for, flash, json
import uuid

# HATA 1 ÇÖZÜMÜ: App'ten değil, doğrudan sınıftan import ediyoruz
from blockchain import HospitalChain
from db_config import get_db_connection

# Blueprint Tanımlama
patient_bp = Blueprint('patient', __name__)

# Blockchain sistemini burada başlatıyoruz (App'ten çekmiyoruz)
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
            flash(f"✅ {name} {surname} başarıyla sisteme kaydedildi. Şimdi muayene girebilirsiniz.", "success")
            return redirect(url_for('index'))  # 'index' ana app'te olduğu için bu doğru

        except psycopg2.IntegrityError:
            conn.rollback()
            flash("❌ Hata: Bu TC Kimlik Numarası ile zaten bir hasta kayıtlı!", "danger")
        except Exception as e:
            conn.rollback()
            flash(f"❌ Bir hata oluştu: {e}", "danger")
        finally:
            cur.close()
            conn.close()

    return render_template('register_patient.html')


# HATA 2 ÇÖZÜMÜ: URL ismini düzelttik (add-recond -> add_record)
@patient_bp.route('/add_record', methods=['GET', 'POST'])
def add_record():
    if request.method == 'POST':
        national_id = request.form['national_id']
        diagnosis = request.form['diagnosis']
        treatment = request.form['treatment']

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("SELECT id FROM patients WHERE national_id = %s", (national_id,))
            patient = cur.fetchone()

            if not patient:
                flash("Hata: Bu TC ile kayıtlı hasta bulunamadı!", "danger")
                # HATA 3 ÇÖZÜMÜ: Kendi içindeki fonksiyona yönlendirirken 'patient.' ekledik
                return redirect(url_for('patient.add_record'))

            patient_id = patient[0]

            cur.execute("SELECT record_hash, id FROM patient_records ORDER BY created_at DESC LIMIT 1")
            last_record = cur.fetchone()

            if last_record:
                last_hash = last_record[0]
                last_index = 1  # Basitlik için sabit bıraktık
            else:
                last_hash = "0000000000000000"
                last_index = 0

            medical_data = {
                "diagnosis": diagnosis,
                "treatment": treatment
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
            """, (
                patient_id,
                user_id,
                json.dumps(medical_data),
                new_block.hash,
                last_hash
            ))

            conn.commit()
            flash("Kayıt başarıyla Blockchain'e eklendi!", "success")
            return redirect(url_for('index'))

        except Exception as e:
            conn.rollback()
            flash(f"Hata oluştu: {str(e)}", "danger")
        finally:
            cur.close()
            conn.close()

    return render_template('add.html')