import os

from flask import Flask, redirect, url_for
from flask_login import LoginManager
from models import User

from routes.admin_routes import admin_bp
from routes.patient_routes import patient_bp
from routes.auth_routes import auth_bp
from routes.main_routes import main_bp

app = Flask(__name__)
app.secret_key = "gizli_anahtar"


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

app.register_blueprint(admin_bp)
app.register_blueprint(patient_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(debug=True)