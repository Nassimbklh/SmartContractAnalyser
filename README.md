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

