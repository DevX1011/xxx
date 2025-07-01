from flask import Flask, request, jsonify, render_template_string, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import secrets

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change_me')
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

class LicenseModelView(ModelView):
    form_excluded_columns = ['id', 'erstellt_am']
    column_exclude_list = ['id']
    can_view_details = True
    create_modal = False
    edit_modal = False

admin = Admin(app, name='Lizenzverwaltung', template_mode='bootstrap3')
admin.add_view(LicenseModelView(License, db.session))

@app.route('/')
def home():
    return '🔐 Lizenzserver läuft – API erreichbar!', 200

@app.route('/api/check_license')
def check_license():
    key = request.args.get('key')
    hwid = request.args.get('hwid')

    lic = License.query.filter_by(schluessel=key).first()
    if not lic:
        return jsonify({"status": "invalid", "message": "Lizenz nicht gefunden."})
    if not lic.aktiv:
        return jsonify({"status": "invalid", "message": "Lizenz deaktiviert."})
    if lic.gueltig_bis < datetime.utcnow():
        return jsonify({"status": "invalid", "message": "Lizenz abgelaufen."})
    if lic.hwid and lic.hwid != hwid:
        return jsonify({"status": "invalid", "message": "HWID stimmt nicht überein."})

    if not lic.hwid:
        lic.hwid = hwid
        db.session.commit()

    return jsonify({
        "status": "valid",
        "gueltig_bis": lic.gueltig_bis.isoformat(),
        "hwid": lic.hwid
    })

# Webformular zum Key-Generieren
HTML_FORM = '''
<h2>🔑 Lizenz-Key generieren</h2>
<form method="post">
  Passwort: <input type="password" name="pw"><br>
  Laufzeit (Tage): <input type="number" name="days"><br>
  <button type="submit">Key generieren</button>
</form>
<p>{{ message }}</p>
'''

@app.route('/gen_key', methods=['GET', 'POST'])
def gen_key():
    msg = ''
    if request.method == 'POST':
        pw = request.form.get('pw')
        if pw != ADMIN_PASSWORD:
            msg = "❌ Falsches Passwort"
        else:
            days = int(request.form.get('days', '30'))
            key = secrets.token_hex(16)
            now = datetime.utcnow()
            license = License(schluessel=key, laufzeit_tage=days, gueltig_bis=now + timedelta(days=days))
            db.session.add(license)
            db.session.commit()
            msg = f"✅ Lizenz erstellt: <code>{key}</code><br>Gültig bis: {license.gueltig_bis.date()}"
    return render_template_string(HTML_FORM, message=msg)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')
