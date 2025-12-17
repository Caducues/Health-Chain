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
                cur.execute("SELECT id, username, name, role_id, password_hash FROM users WHERE username = %s",
                            (username,))
                user_data = cur.fetchone()
        conn.close()

        if user_data:
            stored_password = user_data[4]

            is_valid = False
            try:
                if check_password_hash(stored_password, input_password):
                    is_valid = True
            except:
                pass
            if not is_valid and stored_password == input_password:
                is_valid = True

            if is_valid:
                user_obj = User(
                    id=user_data[0],
                    username=user_data[1],
                    name=user_data[2],
                    role_id=user_data[3]
                )
                login_user(user_obj)
                flash('Giriş başarılı!', 'success')
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