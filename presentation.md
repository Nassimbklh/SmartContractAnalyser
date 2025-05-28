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
