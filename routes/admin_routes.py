from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from db_config import get_db_connection
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    conn = get_db_connection()
    departments = []
    roles = []

    try:
        if request.method == 'POST':
            name = request.form['name']
            surname = request.form['surname']
            username = request.form['username']
            email = request.form['email']
            department_id = request.form['department_id']
            role_id = request.form['role_id']
            plain_password = request.form['password']
            hashed_password = generate_password_hash(plain_password)
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO users (department_id, role_id, name, surname, username, password_hash, e_mail)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (department_id, role_id, name, surname, username, hashed_password, email))

            flash(f"Kullanıcı '{username}' başarıyla oluşturuldu.", "success")
            return redirect(url_for('admin.add_doctor'))
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM departments")
            departments = cur.fetchall()
            cur.execute("SELECT id, name FROM roles")
            roles = cur.fetchall()
    except Exception as e:
        flash(f"Hata: {e}", "danger")

    finally:
        if conn:
            conn.close()

    return render_template('add_doctor.html', departments=departments, roles=roles)