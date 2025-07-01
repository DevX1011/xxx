# app.py
from flask import Flask, request, redirect, url_for, render_template_string, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os, secrets

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'please_change')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

db = SQLAlchemy(app)

class License(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schluessel = db.Column(db.String(64), unique=True, nullable=False)
    laufzeit_tage = db.Column(db.Integer, nullable=False)
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)
    gueltig_bis = db.Column(db.DateTime, nullable=False)
    aktiv = db.Column(db.Boolean, default=True)
    hwid = db.Column(db.String(128), nullable=True)

# Geschützter Admin-Index
class MyAdminIndex(AdminIndexView):
    @expose('/')
    def index(self):
        pw = request.args.get('pw')
        if pw != ADMIN_PASSWORD:
            return render_template_string('''
               <form action="" method="get">
                 Admin-Passwort: <input name="pw" type="password"><button>Login</button>
               </form>
            ''')
        return super().index()

class LicenseView(ModelView):
    page_size = 50
    can_create = False
    can_delete = True
    can_view_details = True

admin = Admin(app, index_view=MyAdminIndex(), template_mode='bootstrap3')
admin.add_view(LicenseView(License, db.session, name='Lizenzen'))

@app.route('/')
def home():
    return '🔐 Lizenzserver läuft – API erreichbar!', 200

@app.route('/api/check_license')
def check_license():
    key = request.args.get('key')
    hwid = request.args.get('hwid')
    lic = License.query.filter_by(schluessel=key).first()
    # siehe bereits vorhanden...
    # (Dein bestehender API-Code)

@app.route('/admin/create_license', methods=['GET','POST'])
def create_license():
    pw = request.args.get('pw')
    if pw != ADMIN_PASSWORD:
        abort(403)
    if request.method == 'POST':
        days = int(request.form['days'])
        key = secrets.token_urlsafe(16)
        lic = License(
            schluessel = key,
            laufzeit_tage = days,
            gueltig_bis = datetime.utcnow() + timedelta(days=days),
        )
        db.session.add(lic)
        db.session.commit()
        flash(f"Key erstellt: {key} – gültig für {days} Tage", 'success')
    return render_template_string('''
      <h2>Neuen Lizenz-Key erstellen</h2>
      <form method="post">
        Laufzeit (Tage): <input name="days" type="number" value="30"><br>
        <button type="submit">Key generieren</button>
      </form>
      {% with msgs = get_flashed_messages(with_categories=true) %}
        {% for cat, msg in msgs %}<p><b>{{msg}}</b></p>{% endfor %}
      {% endwith %}
    ''')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
