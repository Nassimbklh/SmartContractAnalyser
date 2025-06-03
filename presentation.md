# SmartContractAnalyser - Architecture, Déploiement et Configuration

## Architecture du Système

Le SmartContractAnalyser est une application web complète qui permet d'analyser des contrats intelligents Solidity pour détecter des vulnérabilités potentielles. L'application est composée de plusieurs composants qui travaillent ensemble :

### 1. Frontend (React)

Le frontend est développé avec React et offre une interface utilisateur intuitive pour interagir avec le système.

**Composants principaux :**
- **App.js** : Gère le routage de l'application
- **AuthContext.js** : Gère l'état d'authentification
- **Login.js** : Interface de connexion
- **Register.js** : Interface d'inscription
- **Analyze.js** : Interface d'analyse de contrats intelligents
- **History.js** : Interface d'historique des analyses
- **Navbar.js** : Barre de navigation

### 2. Backend (Flask)

Le backend est développé avec Flask (Python) et fournit les API nécessaires pour l'authentification, l'analyse des contrats et la gestion des rapports.

**Endpoints principaux :**
- **/register** : Inscription d'un nouvel utilisateur
- **/login** : Authentification et génération de token JWT
- **/analyze** : Analyse d'un contrat intelligent
- **/history** : Récupération de l'historique des analyses
- **/report/<wallet>/<filename>** : Récupération d'un rapport spécifique

### 3. Base de données (PostgreSQL)

La base de données stocke les informations des utilisateurs et les rapports d'analyse.

**Tables principales :**
- **User** : Stocke les informations des utilisateurs
- **Report** : Stocke les rapports d'analyse

### 4. Services auxiliaires

- **pgAdmin** : Interface d'administration pour PostgreSQL
- **Docker** : Conteneurisation de l'application

## Flux de Communication

1. **Authentification** :
   - L'utilisateur s'inscrit ou se connecte via le frontend
   - Le backend vérifie les identifiants et génère un token JWT
   - Le frontend stocke le token dans localStorage pour les requêtes futures

2. **Analyse de contrat** :
   - L'utilisateur soumet un contrat via le formulaire d'analyse
   - Le frontend envoie le contrat au backend avec le token d'authentification
   - Le backend analyse le contrat à l'aide de l'agent RLHF
   - Le résultat est stocké dans la base de données et renvoyé au frontend

3. **Consultation de l'historique** :
   - L'utilisateur accède à la page d'historique
   - Le frontend demande l'historique au backend avec le token d'authentification
   - Le backend récupère les rapports de l'utilisateur depuis la base de données
   - Les rapports sont affichés dans l'interface utilisateur

## Implémentation Détaillée des API et Communication Frontend-Backend

### 1. Structure du Backend et Création des API

Le backend est organisé selon une architecture modulaire utilisant les **blueprints** de Flask pour organiser les routes API de manière claire et maintenable.

#### 1.1 Organisation des Fichiers Backend

```
backend/
├── api/                  # Définition des endpoints API
│   ├── __init__.py       # Enregistrement des blueprints
│   ├── auth.py           # Endpoints d'authentification
│   └── contract.py       # Endpoints de gestion des contrats
├── models/               # Modèles de données
├── services/             # Logique métier
├── utils/                # Utilitaires
└── app.py                # Point d'entrée de l'application
```

#### 1.2 Création des API avec Flask Blueprints

Les API sont créées en trois étapes principales :

1. **Définition des blueprints** dans des fichiers séparés :

```python
# Exemple de api/auth.py
from flask import Blueprint, request, jsonify
from ..services import register_user, authenticate_user
from ..utils import success_response, error_response

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    wallet = data.get("wallet")
    password = data.get("password")

    try:
        register_user(wallet, password)
        return success_response(message="Inscription réussie")
    except ValueError as e:
        return error_response(str(e), 400)
```

2. **Enregistrement des blueprints** dans le fichier `api/__init__.py` :

```python
from .auth import auth_bp
from .contract import contract_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(contract_bp)
```

3. **Initialisation de l'application** dans `app.py` :

```python
from flask import Flask
from flask_cors import CORS
from .api import register_blueprints
from .models.base import Base, engine

def create_app():
    app = Flask(__name__)
    app.config.update(Config.get_config())
    CORS(app)  # Active CORS pour permettre les requêtes cross-origin

    # Crée les tables dans la base de données
    Base.metadata.create_all(bind=engine)

    # Enregistre les blueprints
    register_blueprints(app)

    return app

app = create_app()
```

#### 1.3 Protection des Routes avec JWT

Les routes protégées utilisent un décorateur `@token_required` qui vérifie la validité du token JWT :

```python
# Dans utils/auth.py
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return error_response("Token manquant", 401)

        try:
            payload = jwt.decode(token, Config.get_config()['SECRET_KEY'], algorithms=["HS256"])
            wallet = payload['wallet']
        except:
            return error_response("Token invalide", 401)

        return f(wallet, *args, **kwargs)
    return decorated

# Utilisation dans les routes
@contract_bp.route("/analyze", methods=["POST"])
@token_required
def analyze(wallet):
    # Le paramètre wallet est automatiquement extrait du token
    # ...
```

### 2. Structure du Frontend et Communication avec le Backend

#### 2.1 Service API Centralisé

Le frontend utilise un service API centralisé (`services/api.js`) basé sur Axios pour communiquer avec le backend :

```javascript
import axios from 'axios';

// URL du backend depuis les variables d'environnement
const BACKEND_URL = process.env.REACT_APP_API_URL || "http://localhost:4455";

// Instance Axios avec configuration par défaut
const api = axios.create({
  baseURL: BACKEND_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token JWT à chaque requête
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// API d'authentification
export const authAPI = {
  login: (credentials) => api.post('/login', credentials),
  register: (userData) => api.post('/register', userData),
};

// API de gestion des contrats
export const contractAPI = {
  analyze: (formData) => api.post('/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob',
  }),
  getHistory: () => api.get('/history'),
  getReport: (wallet, filename) => api.get(`/report/${wallet}/${filename}`, {
    responseType: 'blob',
  }),
};
```

#### 2.2 Gestion de l'Authentification avec AuthContext

L'état d'authentification est géré de manière centralisée avec React Context :

```javascript
// Dans AuthContext.js
import React, { createContext, useState } from "react";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem("token"));

  const login = (newToken) => {
    localStorage.setItem("token", newToken);
    setToken(newToken);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
```

#### 2.3 Protection des Routes Frontend

Le frontend utilise un composant `ProtectedRoute` pour rediriger les utilisateurs non authentifiés :

```javascript
// Dans App.js
function ProtectedRoute({ children }) {
  const { token } = React.useContext(AuthContext);
  return token ? children : <Navigate to="/login" />;
}

// Utilisation dans les routes
<Route path="/analyze" element={<ProtectedRoute><Analyze /></ProtectedRoute>} />
```

### 3. Exemples Concrets de Communication Frontend-Backend

#### 3.1 Authentification (Login.js → /login)

```javascript
// Dans Login.js
const handleSubmit = async (e) => {
  e.preventDefault();
  try {
    const res = await axios.post(`${BACKEND_URL}/login`, form);
    login(res.data.access_token); // Stocke le token dans AuthContext
    navigate("/analyze");
  } catch {
    setMessage("❌ Adresse ou mot de passe invalide");
  }
};
```

Côté backend (api/auth.py) :
```python
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    wallet = data.get("wallet")
    password = data.get("password")

    try:
        auth_data = authenticate_user(wallet, password)
        return success_response(data=auth_data)
    except ValueError:
        return error_response("Identifiants invalides", 401)
```

#### 3.2 Analyse de Contrat (Analyze.js → /analyze)

```javascript
// Dans Analyze.js
const handleSubmit = async (e) => {
  e.preventDefault();
  const formData = new FormData();
  if (file) formData.append("file", file);
  if (code.trim()) formData.append("code", code);

  try {
    const res = await axios.post(`${BACKEND_URL}/analyze`, formData, {
      headers: { Authorization: `Bearer ${token}` },
      responseType: "text",
    });
    setReportContent(res.data);
  } catch (err) {
    setError("❌ Erreur lors de l'analyse");
  }
};
```

Côté backend (api/contract.py) :
```python
@contract_bp.route("/analyze", methods=["POST"])
@token_required
def analyze(wallet):
    file = request.files.get("file")
    code = request.form.get("code")
    content = code or (file.read().decode("utf-8") if file else "")

    # Analyse du contrat
    result = analyze_contract(content, user.id)

    # Génération du rapport
    markdown = generate_report_markdown(result["report"])
    return markdown, 200, {'Content-Type': 'text/markdown; charset=utf-8'}
```

#### 3.3 Consultation de l'Historique (History.js → /history)

```javascript
// Dans History.js
useEffect(() => {
  fetch(`${BACKEND_URL}/history`, {
    headers: { Authorization: `Bearer ${token}` }
  })
    .then(res => res.json())
    .then(data => setHistory(data))
    .catch(err => setError("Erreur lors du chargement de l'historique"));
}, [token, BACKEND_URL]);
```

Côté backend (api/contract.py) :
```python
@contract_bp.route("/history", methods=["GET"])
@token_required
def history(wallet):
    user = get_user_by_wallet(wallet)
    reports = get_user_reports(user.id)
    formatted_reports = [
        {
            "filename": r.filename,
            "date": r.created_at.strftime("%Y-%m-%d %H:%M"),
            "status": r.status,
            "attack": r.attack
        } for r in reports
    ]
    return success_response(data=formatted_reports)
```

## Configuration Docker

### Architecture Docker

L'application est conteneurisée à l'aide de Docker, ce qui permet un déploiement cohérent et isolé. Voici les composants Docker de l'application :

1. **Backend (Flask API)**
   - Construit à partir du Dockerfile dans le répertoire `./backend`
   - Exposé sur le port 4455 (mappé au port 8000 du conteneur)
   - Dépend du service de base de données
   - Utilise des variables d'environnement pour la configuration
   - Connecté aux réseaux web_network et data_network

2. **Frontend (React + Nginx)**
   - Construit à partir du Dockerfile dans le répertoire `./react-client`
   - Exposé sur le port 4456 (mappé au port 80 du conteneur)
   - Dépend du service backend
   - Utilise Nginx comme serveur web pour servir l'application React compilée
   - Connecté au réseau web_network

3. **Base de données (PostgreSQL)**
   - Utilise l'image officielle postgres:15
   - Exposée sur le port 5432
   - Utilise un volume pour la persistance des données
   - Connecté au réseau data_network

4. **pgAdmin (Interface d'administration PostgreSQL)**
   - Utilise l'image dpage/pgadmin4
   - Exposé sur le port 4457 (mappé au port 80 du conteneur)
   - Utilise un volume pour la persistance des données
   - Connecté au réseau data_network

5. **Réseaux Docker**
   - **web_network** : Réseau pour la communication entre le frontend et le backend
   - **data_network** : Réseau pour la communication entre le backend et la base de données

### Fichiers Docker

#### 1. docker-compose.yml

Le fichier `docker-compose.yml` définit l'ensemble des services, leurs dépendances, les volumes et les réseaux nécessaires pour exécuter l'application en environnement local.

```yaml
version: '3.8'

services:
  backend:
    platform: linux/amd64
    build:
      context: ./backend
    ports:
      - "4455:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/mydb
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - FLASK_APP=app.py
      - FLASK_RUN_HOST=0.0.0.0
    depends_on:
      - db
    volumes:
      - ./backend:/app
    restart: always
    networks:
      - web_network
      - data_network

  frontend:
    build:
      context: ./react-client
    ports:
      - "4456:80"
    environment:
      - REACT_APP_API_URL=http://localhost:4455
    depends_on:
      - backend
    restart: always
    networks:
      - web_network

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: always
    networks:
      - data_network

  pgadmin:
    image: dpage/pgadmin4
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@admin.com
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "4457:80"
    depends_on:
      - db
    restart: always
    volumes:
      - pgadmin-data:/var/lib/pgadmin
    networks:
      - data_network

networks:
  web_network:
    driver: bridge
  data_network:
    driver: bridge

volumes:
  pgdata:
    name: smartcontract-analyser-postgres-data
  pgadmin-data:
    name: smartcontract-analyser-pgadmin-data
```

#### 2. Backend Dockerfile

Le Dockerfile du backend configure un environnement Python avec les dépendances nécessaires pour exécuter l'API Flask, y compris le compilateur Solidity.

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install solc (Solidity compiler) via npm
RUN npm install -g solc

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Environment
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8000

EXPOSE 8000

CMD ["flask", "run"]
```

#### 3. Frontend Dockerfile

Le Dockerfile du frontend utilise une approche multi-étapes pour construire l'application React puis la servir via Nginx.

```dockerfile
# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the code
COPY . .

# Set NODE_OPTIONS for OpenSSL compatibility
ENV NODE_OPTIONS=--openssl-legacy-provider

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy the build output to replace the default nginx contents
COPY --from=build /app/build /usr/share/nginx/html

# Copy custom nginx config
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d

# Expose port
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]
```

#### 4. Configuration Nginx (nginx.conf)

La configuration Nginx est optimisée pour servir une application React (Single Page Application).

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Handle React routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico)$ {
        expires 1y;
        add_header Cache-Control "public, max-age=31536000";
    }

    # Don't cache HTML files
    location ~* \.html$ {
        expires -1;
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate";
    }

    # Error pages
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

### Lancement avec Docker Compose

Pour lancer l'application en utilisant Docker Compose, suivez ces étapes :

1. Assurez-vous que Docker et Docker Compose sont installés sur votre machine
2. Créez un fichier `.env` à la racine du projet avec votre clé API OpenAI
3. Exécutez la commande suivante :

```bash
docker-compose up -d
```

L'application sera accessible aux adresses suivantes :
- Frontend : http://localhost:4456
- Backend API : http://localhost:4455
- pgAdmin : http://localhost:4457 (email: admin@admin.com, password: admin)


## État Actuel des Fonctionnalités

### Fonctionnalités opérationnelles

- ✅ Inscription et connexion des utilisateurs
- ✅ Analyse de contrats intelligents (via code ou fichier)
- ✅ Génération de rapports détaillés
- ✅ Interface utilisateur réactive et intuitive
- ✅ Conteneurisation avec Docker pour un déploiement facile

## Conclusion

Le SmartContractAnalyser est une application bien structurée qui offre des fonctionnalités puissantes pour l'analyse de contrats intelligents. La conteneurisation avec Docker permet un déploiement cohérent et isolé. L'architecture multi-tiers assure une séparation claire des responsabilités et facilite la maintenance et l'évolution de l'application.
