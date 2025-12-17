from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role_name != 'Admin':
            flash("Bu sayfaya sadece Yöneticiler girebilir", "danger")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)

    return decorated_function

def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))

        if current_user.role_name != 'Doktor':
            flash("⛔ Bu işlem sadece doktorlar tarafından yapılabilir!", "danger")
            return redirect(url_for('main.index'))

        return f(*args, **kwargs)

    return decorated_function