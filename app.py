from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime
import os

# === App-Konfiguration
from dotenv import load_dotenv
load_dotenv()  # liest .env

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change_me')
db = SQLAlchemy(app)

# === Datenbankmodell
class License(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schluessel = db.Column(db.String(64), unique=True, nullable=False)
    laufzeit_tage = db.Column(db.Integer, nullable=False)
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)
    gueltig_bis = db.Column(db.DateTime, nullable=False)
    aktiv = db.Column(db.Boolean, default=True)
    hwid = db.Column(db.String(128), nullable=True)

# === Admin-Ansicht
class LicenseModelView(ModelView):
    form_excluded_columns = ['id', 'erstellt_am']
    column_exclude_list = ['id']
    can_view_details = True
    create_modal = False
    edit_modal = False

admin = Admin(app, name='Lizenzverwaltung', template_mode='bootstrap3')
admin.add_view(LicenseModelView(License, db.session))

# === Lizenzprüfungs-API
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

# === Init & Start
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

@app.route('/')
def home():
    return '🔐 Lizenzserver läuft – API erreichbar!', 200

from flask import render_template_string

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "test123")  # .env setzen!

html_form = """
<!doctype html>
<title>Key Generator</title>
<h2>🔐 Lizenz-Key erstellen</h2>
<form method=post>
  Admin-Passwort: <input type=password name=password><br><br>
  Laufzeit (Tage): <input type=number name=days value=30><br><br>
  <input type=submit value="Lizenz erstellen">
</form>
{% if result %}
  <p><strong>✅ Neuer Key:</strong> {{ result }}</p>
{% endif %}
"""

@app.route('/generate', methods=['GET', 'POST'])
def generate_license():
    result = None
    if request.method == 'POST':
        if request.form.get("password") != ADMIN_PASSWORD:
            return "❌ Falsches Passwort", 403
        try:
            days = int(request.form.get("days", 30))
            key = secrets.token_hex(16)
            gueltig_bis = datetime.utcnow() + timedelta(days=days)
            lic = License(
                schluessel=key,
                laufzeit_tage=days,
                gueltig_bis=gueltig_bis
            )
            db.session.add(lic)
            db.session.commit()
            result = key
        except Exception as e:
            return f"Fehler: {str(e)}", 500
    return render_template_string(html_form, result=result)
