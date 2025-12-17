from flask import Blueprint, render_template, request, redirect, url_for, flash
from db_config import get_db_connection
import uuid

# Blueprint oluşturuyoruz (Bir nevi mini app)
admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        # Formdan verileri al
        name = request.form['name']
        surname = request.form['surname']
        username = request.form['username']
        email = request.form['email']
        department_id = request.form['department_id']
        role_id = request.form['role_id']
        password = "123"  # Gerçek projede hashlenmeli! (SHA256 vb.)

        try:
            cur.execute("""
                INSERT INTO users (department_id, role_id, name, surname, username, password_hash, e_mail)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (department_id, role_id, name, surname, username, password, email))
            conn.commit()
            flash("✅ Yeni doktor başarıyla eklendi!", "success")
            return redirect(url_for('admin.add_doctor'))  # Kendine yönlendir
        except Exception as e:
            conn.rollback()
            flash(f"❌ Hata: {e}", "danger")
        finally:
            cur.close()
            conn.close()

    # GET İsteği: Sayfa açılırken Departmanları ve Rolleri listelemeliyiz
    cur.execute("SELECT id, name FROM departments")
    departments = cur.fetchall()

    cur.execute("SELECT id, name FROM roles")
    roles = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('add_doctor.html', departments=departments, roles=roles)