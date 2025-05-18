from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from functools import wraps
import jwt
import datetime
import io

app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = "supersecret"

# 🔐 Base utilisateurs (temporaire)
users = {"admin": {"password": "admin"}}

# 📊 Historique enrichi
user_analyses = {
    "admin": [
        {
            "filename": "VestingWallet.sol",
            "date": "2025-05-10 18:45",
            "status": "KO",
            "attack": "Reentrancy Attack"
        },
        {
            "filename": "SimpleStorage.sol",
            "date": "2025-05-10 19:02",
            "status": "OK",
            "attack": None
        },
        {
            "filename": "Token.sol",
            "date": "2025-05-11 09:14",
            "status": "KO",
            "attack": "Integer Overflow"
        },
        {
            "filename": "Crowdsale.sol",
            "date": "2025-05-11 10:00",
            "status": "OK",
            "attack": None
        },
        {
            "filename": "DAOClone.sol",
            "date": "2025-05-11 10:42",
            "status": "KO",
            "attack": "Delegatecall Injection"
        },
        {
            "filename": "TimeLock.sol",
            "date": "2025-05-11 11:18",
            "status": "KO",
            "attack": "Timestamp Manipulation"
        }
    ]
}


# 🔐 Authentification token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', "").replace("Bearer ", "")
        if not token:
            return jsonify({"error": "Token manquant"}), 401
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            return f(data["wallet"], *args, **kwargs)
        except:
            return jsonify({"error": "Token invalide"}), 401
    return decorated

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    wallet = data.get("wallet")
    password = data.get("password")

    if wallet in users:
        return jsonify({"error": "Adresse déjà utilisée"}), 400

    users[wallet] = {"password": password}
    return jsonify({"message": "Inscription réussie"})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    wallet = data.get("wallet")
    password = data.get("password")

    user = users.get(wallet)
    if user and user["password"] == password:
        token = jwt.encode({
            "wallet": wallet,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, app.config["SECRET_KEY"], algorithm="HS256")
        return jsonify({"access_token": token})

    return jsonify({"error": "Identifiants invalides"}), 401

# ✅ Route principale d’analyse
@app.route("/analyze", methods=["POST"])
@token_required
def analyze(wallet):
    file = request.files.get("file")
    code = request.form.get("code")
    content = code or (file.read().decode() if file else "")
    filename = file.filename if file else "code_saisi.sol"

    if not content:
        return jsonify({"error": "Aucun code fourni"}), 400

    # 💥 Simule détection d’attaque
    attack_detected = "Reentrancy Attack" if "call.value" in content else None
    status = "KO" if attack_detected else "OK"
    attack = attack_detected or None

    user_analyses.setdefault(wallet, []).append({
        "filename": filename,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": status,
        "attack": attack
    })

    report_content = f"# Rapport d’analyse\n\n"
    report_content += f"**Statut :** {'❌ KO' if status == 'KO' else '✅ OK'}\n\n"
    if status == "KO":
        report_content += f"**Vulnérabilité détectée :** {attack}\n"
    else:
        report_content += "Aucune vulnérabilité détectée."

    report_file = io.BytesIO(report_content.encode("utf-8"))
    return send_file(report_file, as_attachment=True, download_name="rapport.md", mimetype="text/markdown")

# 📜 Route historique
@app.route("/history", methods=["GET"])
@token_required
def history(wallet):
    return jsonify(user_analyses.get(wallet, []))

# 🔁 Toujours recréer admin
users["admin"] = {"password": "admin"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
