# Étape 1 : base Python slim sécurisée
FROM python:3.10-slim

# Étape 2 : installation des dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Étape 3 : copie du code
WORKDIR /app
COPY .. .

# Étape 4 : installation des dépendances Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Installation de solc 0.8.20
RUN python3 -c "import solcx; solcx.install_solc('0.8.20')"


# Étape 5 : installation de solc
RUN python3 -c "import solcx; solcx.install_solc('0.8.20')"

# Étape 6 : port exposé (si tu lances un serveur plus tard, ex: Flask)
EXPOSE 8000

# Étape 7 : commande d'entraînement par défaut
CMD ["python3", "agent/train_agent.py"]
