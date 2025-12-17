from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from db_config import get_db_connection
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        input_password = request.form['password']
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:

                cur.execute("""
                    SELECT u.id, u.username, u.name, u.surname, u.role_id, u.password_hash, r.name
                    FROM users u
                    JOIN roles r ON u.role_id = r.id
                    WHERE u.username = %s
                """, (username,))
                user_data = cur.fetchone()

        if conn:
            conn.close()
        if user_data:
            stored_password_hash = user_data[5]

            if check_password_hash(stored_password_hash, input_password):
                user_obj = User(
                    id=user_data[0],
                    username=user_data[1],
                    name=user_data[2],
                    surname=user_data[3],
                    role_name=user_data[6]
                )
                login_user(user_obj)
                flash(f'Hoşgeldiniz, {user_data[2]}!', 'success')
                return redirect(url_for('main.index'))
            else:
                flash('Hatalı şifre.', 'danger')
        else:
            flash('Kullanıcı bulunamadı.', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Çıkış yapıldı.', 'info')
    return redirect(url_for('auth.login'))