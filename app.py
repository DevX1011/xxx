from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime, timedelta
import hashlib
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///licenses.db'
app.config['SECRET_KEY'] = 'supersecret'
db = SQLAlchemy(app)

class License(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schluessel = db.Column(db.String(64), unique=True, nullable=False)
    laufzeit_tage = db.Column(db.Integer, nullable=False)
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)
    gueltig_bis = db.Column(db.DateTime, nullable=False)
    aktiv = db.Column(db.Boolean, default=True)
    hwid = db.Column(db.String(128), nullable=True)

admin = Admin(app, name='Lizenzverwaltung', template_mode='bootstrap3')
admin.add_view(ModelView(License, db.session))

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
        return jsonify({"status": "invalid", "message": "HWID nicht gültig."})

    if not lic.hwid:
        lic.hwid = hwid
        db.session.commit()

    return jsonify({
        "status": "valid",
        "gueltig_bis": lic.gueltig_bis.isoformat(),
        "hwid": lic.hwid
    })

# Nur beim ersten Start nötig, um Datenbank anzulegen
@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
