# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
import json
import uuid
from db_config import get_db_connection
from blockchain import HospitalChain
from routes.admin_routes import admin_bp
from routes.patient_routes import patient_bp

app = Flask(__name__)
app.secret_key = "cok_gizli_anahtar"
blockchain_system = HospitalChain()

app.register_blueprint(admin_bp)
app.register_blueprint(patient_bp)


@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.name, p.surname, pr.record_data, pr.record_hash, pr.previous_record_hash, pr.created_at
        FROM patient_records pr
        JOIN patients p ON pr.patient_id = p.id
        ORDER BY pr.created_at DESC
    """)
    records = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('index.html', records=records)






@app.route('/verify')
def verify_chain():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT pr.record_data, pr.record_hash, pr.previous_record_hash, pr.created_at
        FROM patient_records pr
        ORDER BY pr.created_at ASC
    """)
    records = cur.fetchall()
    cur.close()
    conn.close()

    # Veritabanından gelen veriyi Blockchain modülümüzün anlayacağı formata çevirelim
    chain_data = []
    for index, row in enumerate(records):
        chain_data.append({
            'index': index,
            'timestamp': row[3].timestamp(),
            'data': row[0],
            'hash': row[1],
            'previous_hash': row[2]
        })

    is_valid = True
    error_message = ""

    for i in range(1, len(chain_data)):
        current = chain_data[i]
        previous = chain_data[i - 1]

        if current['previous_hash'] != previous['hash']:
            is_valid = False
            error_message = f"HATA: Zincir kopuk! Kayıt sırası {i + 1} ile {i} eşleşmiyor."
            break
        pass

    if is_valid:
        flash("✅ Sistem Güvenli: Tüm zincir ve veriler doğrulandı.", "success")
    else:
        flash(f"❌ GÜVENLİK UYARISI: {error_message}", "danger")

    return redirect(url_for('index'))







if __name__ == '__main__':
    app.run(debug=True)