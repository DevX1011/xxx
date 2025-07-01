# Lizenzserver für DarkSystem Tools

## Funktionen
- Lizenzverwaltung (Key, Ablaufdatum, Aktivierung nach HWID)
- Adminpanel über `/admin`
- REST-API zur Lizenzprüfung für den Client

## Nutzung

1. Installiere die Abhängigkeiten:
```bash
pip install -r requirements.txt
```

2. Starte den Server:
```bash
python app.py
```

3. Öffne das Adminpanel:
`http://localhost:5000/admin`

## API-Endpunkt

Lizenzprüfung:
```
GET /api/check_license?key=DEMO123&hwid=XYZ
```

Antworten: `VALID`, `EXPIRED`, `INVALID`
