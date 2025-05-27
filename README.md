# 🔐 SmartContractAnalyser

Application web permettant d’analyser automatiquement des smart contracts Solidity à l’aide de GPT et de générer un rapport markdown interactif.

---

## 🧱 Structure du projet

```bash
SmartContractAnalyser/
├── backend/
│   ├── app.py              ← Backend Flask
│   ├── models.py           ← Définition des tables User et Report
│   ├── database.py         ← Connexion à PostgreSQL
│   ├── requirements.txt    ← Dépendances Python
│   └── rlhf_agent/
│       └── agent.py        ← Fonction GPT d’analyse du contrat
├── react-client/
│   ├── src/                ← Code React
│   ├── start-react.bat     ← Script de démarrage frontend (Windows)
```

---

## ⚙️ Prérequis

- Python 3.12+
- Node.js 18+
- PostgreSQL en local (ou hébergée sur Azure)
- Une clé API OpenAI (`sk-...`) valide

---

## 🔧 Installation backend

1. Ouvre un terminal et va dans le dossier backend :

```bash
cd backend
```
2.	Active un environnement virtuel :
```
python -m venv .venv
source .venv/bin/activate    # macOS/Linux
.venv\Scripts\activate       # Windows
```
3.	Installe les dépendances Python :

```bash
pip install -r requirements.txt
```

4.	Lance le backend :
```bash
cd backend
python app.py
```

5. Dans un nouveau terminal, va dans le dossier React :
```bash
cd react-client
npm install
npm start ou start-react.bat (c'est mieux)

```
L’interface sera dispo ici : http://localhost:3000



