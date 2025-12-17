from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from db_config import get_db_connection
from blockchain import HospitalChain
from flask import request

main_bp = Blueprint('main', __name__)
blockchain_system = HospitalChain()

@main_bp.route('/')
@login_required
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    search_query = request.args.get('q')

    if search_query:
        query = """
            SELECT p.name, p.surname, pr.record_data, pr.record_hash, pr.previous_record_hash, pr.created_at, p.id, p.national_id
            FROM patient_records pr
            JOIN patients p ON pr.patient_id = p.id
            WHERE p.name ILIKE %s OR p.surname ILIKE %s OR p.national_id LIKE %s
            ORDER BY pr.created_at DESC
        """
        search_term = f"%{search_query}%"
        cur.execute(query, (search_term, search_term, search_term))
    else:
        cur.execute("""
            SELECT p.name, p.surname, pr.record_data, pr.record_hash, pr.previous_record_hash, pr.created_at, p.id, p.national_id
            FROM patient_records pr
            JOIN patients p ON pr.patient_id = p.id
            ORDER BY pr.created_at DESC
            LIMIT 20
        """)

    records = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('index.html', records=records, user=current_user)

@main_bp.route('/verify')
@login_required
def verify_chain():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT pr.record_data, pr.record_hash, pr.previous_record_hash, pr.created_at, pr.id
        FROM patient_records pr
        ORDER BY pr.created_at ASC
    """)
    records = cur.fetchall()
    cur.close()
    conn.close()
    chain_data = []
    for index, row in enumerate(records):
        chain_data.append({
            'index': index,
            'timestamp': row[3].timestamp(),
            'data': row[0],
            'hash': row[1].strip(),
            'previous_hash': row[2].strip() if row[2] else "0"
        })
    is_valid, message = blockchain_system.is_chain_valid(chain_data)

    if is_valid:
        flash("Tüm zincir ve veriler doğrulandı.", "success")
    else:
        flash(f"{message}", "danger")

    return redirect(url_for('main.index'))