# 🩹 Patch Python 3.12 pour inspect.getargspec (utilisé par parsimonious)
import inspect
from inspect import signature, Parameter

if not hasattr(inspect, "getargspec"):
    def getargspec(func):
        sig = signature(func)
        args = [p.name for p in sig.parameters.values()
                if p.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)]
        varargs = next((p.name for p in sig.parameters.values()
                        if p.kind == Parameter.VAR_POSITIONAL), None)
        varkw = next((p.name for p in sig.parameters.values()
                      if p.kind == Parameter.VAR_KEYWORD), None)
        return type('ArgSpec', (), {
            'args': args,
            'varargs': varargs,
            'keywords': varkw,
            'defaults': None
        })()
    inspect.getargspec = getargspec

# --- Imports ---
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from functools import wraps
import jwt
import datetime
import io
import os
from rlhf_agent.agent import analyze_contract_from_code

app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = "supersecret"

# --- Utilisateurs & Historique ---
users = {"admin": {"password": "admin"}}
user_analyses = {}

# --- Répertoire pour les rapports ---
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")

# --- Auth token ---
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

# --- Auth routes ---
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    wallet = data.get("wallet")
    password = data.get("password")
    if not wallet or not isinstance(wallet, str):
        return jsonify({"error": "Adresse invalide"}), 400
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

# --- Analyse ---
@app.route("/analyze", methods=["POST"])
@token_required
def analyze(wallet):
    file = request.files.get("file")
    code = request.form.get("code")
    content = code or (file.read().decode("utf-8") if file else "")
    filename = file.filename if file else "code_saisi.sol"
    print(f"Contenu reçu = {content[:100]}")

    if not content:
        return jsonify({"error": "Aucun code fourni"}), 400

    analysis_result = analyze_contract_from_code(content)
    status = analysis_result.get("status", "OK")
    attack = analysis_result.get("attack")
    contract_info = analysis_result.get("contract_info", {})
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    contract_name = contract_info.get("contract_name", "Contract")
    if file:
        base_filename = file.filename.rsplit(".", 1)[0]  # sans l'extension
        generated_filename = base_filename
    else:
        generated_filename = f"{contract_name}_{now}"
    reasoning = analysis_result.get("reasoning", "")
    summary = analysis_result.get("summary", "")
    code_type = analysis_result.get("code_type", "solidity")
    exploit_code = analysis_result.get("code", "")
    attack_result = analysis_result.get("attack_result", {})

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    markdown_block = "```"

    if attack_result.get("success"):
        exploit_section = f"""
## ⚔️ Code d'exploit proposé

{markdown_block}{code_type}
{exploit_code}
{markdown_block}
"""
    else:
        exploit_section = """
## ⚔️ Code d'exploit proposé

Aucun exploit exécutable généré. Code incomplet ou invalide.
"""

    report_content = f"""# 📄 Rapport d'analyse de contrat intelligent

**Nom du fichier :** {generated_filename}  
**Nom du contrat :** {contract_info.get('contract_name', '—')}  
**Adresse déployée :** {contract_info.get('address', '—')}  
**Compilateur Solidity :** {contract_info.get('solc_version', '—')}  
**Date d’analyse :** {now}  

---

## ✅ Résultat global

**Statut :** {'❌ KO – Vulnérabilité détectée' if status == 'KO' else '✅ OK – Aucun comportement anormal détecté'}  
**Type de vulnérabilité :** {attack or "Aucune"}

---

## 🔍 Résumé de l’analyse

{summary or "Aucune vulnérabilité évidente détectée dans ce contrat."}

---

## 🧠 Raisonnement du modèle

{reasoning or "Aucun raisonnement généré."}

---

{exploit_section}

---

⚠️ **Note :** Ce rapport est généré automatiquement. Il ne garantit pas l'absence totale de failles. Une revue humaine reste recommandée.
"""

    # Créer le répertoire utilisateur s'il n'existe pas
    user_dir = os.path.join(REPORTS_DIR, wallet)
    os.makedirs(user_dir, exist_ok=True)

    # Générer un nom de fichier unique avec timestamp si nécessaire
    file_path = os.path.join(user_dir, f"{generated_filename}.md")
    if os.path.exists(file_path):
        generated_filename = f"{generated_filename}_{now}"
        file_path = os.path.join(user_dir, f"{generated_filename}.md")

    # Enregistrer le rapport dans un fichier
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    # Stocker les métadonnées en mémoire (pour compatibilité)
    user_analyses.setdefault(wallet, []).append({
        "filename": generated_filename,
        "date": now,
        "status": status,
        "attack": attack,
        "report_path": file_path
    })

    # Envoyer le fichier au client
    return send_file(file_path, as_attachment=True, download_name=f"{generated_filename}.md", mimetype="text/markdown")

# --- Historique utilisateur ---
@app.route("/history", methods=["GET"])
@token_required
def history(wallet):
    # Vérifier si le répertoire utilisateur existe
    user_dir = os.path.join(REPORTS_DIR, wallet)
    if not os.path.exists(user_dir):
        return jsonify([])

    # Lister tous les fichiers de rapport dans le répertoire utilisateur
    reports = []
    for filename in os.listdir(user_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(user_dir, filename)
            # Extraire les métadonnées du fichier
            stat = os.stat(file_path)
            created_date = datetime.datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M")

            # Extraire le nom du fichier sans extension
            base_filename = filename.rsplit('.', 1)[0]

            # Extraire le statut et l'attaque du contenu du fichier
            status = "Unknown"
            attack = ""
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Chercher la ligne de statut
                    if "❌ KO – Vulnérabilité détectée" in content:
                        status = "KO"
                    elif "✅ OK – Aucun comportement anormal détecté" in content:
                        status = "OK"

                    # Chercher le type de vulnérabilité
                    for line in content.split('\n'):
                        if "**Type de vulnérabilité :**" in line:
                            attack_info = line.split(":**")[1].strip()
                            if attack_info != "Aucune":
                                attack = attack_info
                            break
            except Exception as e:
                print(f"Erreur lors de la lecture du fichier {file_path}: {e}")

            # Ajouter à la liste des rapports
            reports.append({
                "filename": base_filename,
                "date": created_date,
                "status": status,
                "attack": attack,
                "report_path": file_path
            })

    # Trier par date de création (plus récent en premier)
    reports.sort(key=lambda x: x["date"], reverse=True)

    return jsonify(reports)

@app.route("/report/<wallet>/<filename>", methods=["GET"])
@token_required
def download_report(token_wallet, wallet, filename):
    if token_wallet != wallet:
        return jsonify({"error": "Accès interdit à ce wallet"}), 403

    # Construire le chemin du fichier
    file_path = os.path.join(REPORTS_DIR, wallet, f"{filename}.md")

    # Vérifier si le fichier existe
    if not os.path.exists(file_path):
        return jsonify({"error": "Rapport introuvable"}), 404

    # Envoyer le fichier au client
    return send_file(file_path, as_attachment=True,
                     download_name=f"{filename}.md",
                     mimetype="text/markdown")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
