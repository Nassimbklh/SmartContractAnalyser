# Guide d'utilisation de SmartContractAnalyser

Ce guide explique comment accéder et utiliser les différentes composantes du projet SmartContractAnalyser.

## Prérequis

- Docker et Docker Compose installés sur votre machine
- Un terminal pour exécuter les commandes
- Un navigateur web moderne (Chrome, Firefox, Edge, etc.)
- Une clé API OpenAI (pour l'analyse des contrats intelligents)
- Git (pour cloner le dépôt)

## Lancement du projet

1. Clonez le dépôt GitHub :
   ```bash
   git clone <url-du-dépôt>
   cd SmartContractAnalyser
   ```

2. Créez un fichier `.env` à la racine du projet avec le contenu suivant :
   ```
   # OpenAI API Key
   OPENAI_API_KEY=votre_clé_api_openai_ici

   # Database Configuration
   POSTGRES_USER=user
   POSTGRES_PASSWORD=password
   POSTGRES_DB=mydb
   DATABASE_URL=postgresql://user:password@db:5432/mydb

   # Frontend Configuration
   REACT_APP_API_URL=http://localhost:4455
   ```

3. Rendez le script de démarrage exécutable :
   ```bash
   chmod +x start.sh
   ```

4. Lancez le projet avec le script de démarrage :
   ```bash
   ./start.sh
   ```

5. Attendez que tous les conteneurs soient démarrés. Vous verrez un message de confirmation lorsque tout est prêt.

## Accès aux services

### Frontend (Interface utilisateur)

- **URL** : http://localhost:4456
- **Description** : Interface web pour interagir avec l'analyseur de contrats intelligents
- **Fonctionnalités** :
  - Inscription et connexion
  - Analyse de contrats intelligents
  - Historique des analyses
  - Téléchargement des rapports

### Backend (API)

- **URL** : http://localhost:4455
- **Description** : API REST pour l'analyse des contrats intelligents
- **Endpoints** :
  - `/register` - Inscription d'un nouvel utilisateur
  - `/login` - Connexion et obtention d'un token d'accès
  - `/analyze` - Analyse d'un contrat intelligent
  - `/history` - Récupération de l'historique des analyses
  - `/report/<wallet>/<filename>` - Récupération d'un rapport spécifique

### Base de données (PostgreSQL)

- **Port** : 5432
- **Utilisateur** : user
- **Mot de passe** : password
- **Base de données** : mydb
- **Description** : Stocke les utilisateurs et les rapports d'analyse

### pgAdmin (Interface d'administration de la base de données)

- **URL** : http://localhost:4457
- **Email** : admin@admin.com
- **Mot de passe** : admin
- **Description** : Interface web pour gérer la base de données PostgreSQL
- **Configuration de la connexion à la base de données** :
  1. Cliquez sur "Add New Server"
  2. Onglet "General" :
     - Name : mydb
  3. Onglet "Connection" :
     - Host : db
     - Port : 5432
     - Maintenance database : mydb
     - Username : user
     - Password : password

## Utilisation du frontend

1. Ouvrez http://localhost:4456 dans votre navigateur
2. Créez un compte en cliquant sur "S'inscrire"
3. Connectez-vous avec vos identifiants
4. Sur la page d'analyse :
   - Collez le code Solidity directement dans le champ de texte
   - OU téléchargez un fichier .sol
5. Cliquez sur "Lancer l'analyse"
6. Attendez que l'analyse soit terminée
7. Consultez les résultats et téléchargez le rapport si nécessaire
8. Accédez à l'historique des analyses via le menu

## Gestion des conteneurs Docker

- **Afficher les logs** :
  ```bash
  docker-compose logs
  ```

- **Afficher les logs d'un service spécifique** :
  ```bash
  docker-compose logs [backend|frontend|db|pgadmin]
  ```

- **Redémarrer les services** :
  ```bash
  docker-compose down
  docker-compose up -d
  ```

- **Arrêter les services** :
  ```bash
  docker-compose down
  ```

## Développement local

Si vous souhaitez développer localement sans utiliser Docker, voici les étapes à suivre :

### Structure du projet

Le projet est organisé selon une architecture modulaire pour faciliter la maintenance et l'évolution du code :

#### Backend (Flask)

- **api/** : Contient les endpoints de l'API REST
- **models/** : Définit les modèles de données pour la base de données
- **services/** : Contient la logique métier
- **utils/** : Fonctions utilitaires (authentification, réponses HTTP, etc.)
- **config/** : Configuration de l'application
- **rlhf_agent/** : Agent d'analyse des contrats intelligents

#### Frontend (React)

- **src/components/** : Composants React réutilisables
- **src/contexts/** : Contextes React (authentification, etc.)
- **src/services/** : Services pour les appels API
- **src/utils/** : Fonctions utilitaires
- **src/assets/** : Ressources statiques (images, etc.)
- **src/styles/** : Fichiers CSS

### Backend (Flask)

1. Naviguez vers le répertoire backend :
   ```bash
   cd backend
   ```

2. Créez un environnement virtuel Python :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows : venv\Scripts\activate
   ```

3. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

4. Configurez les variables d'environnement :
   ```bash
   export OPENAI_API_KEY=votre_clé_api_openai_ici
   export DATABASE_URL=postgresql://user:password@localhost:5432/mydb
   ```

5. Lancez le serveur Flask :
   ```bash
   flask run --host=0.0.0.0 --port=8000
   ```

### Frontend (React)

1. Naviguez vers le répertoire react-client :
   ```bash
   cd react-client
   ```

2. Installez les dépendances :
   ```bash
   npm install
   ```

3. Pour éviter les erreurs OpenSSL avec Node.js v18, utilisez le script fourni :
   ```bash
   chmod +x start-react.sh
   ./start-react.sh
   ```

   Ou définissez manuellement la variable d'environnement :
   ```bash
   export NODE_OPTIONS=--openssl-legacy-provider
   npm start
   ```

4. Le frontend sera accessible à l'adresse http://localhost:3000

## Dépannage

- **Problème** : Le frontend ne peut pas se connecter au backend
  - **Solution** : Vérifiez que la variable d'environnement REACT_APP_API_URL est correctement définie dans le fichier .env

- **Problème** : L'analyse des contrats échoue
  - **Solution** : Vérifiez que la clé API OpenAI est correctement définie dans le fichier .env

- **Problème** : Impossible de se connecter à pgAdmin
  - **Solution** : Vérifiez que le conteneur pgAdmin est en cours d'exécution avec `docker-compose ps`

- **Problème** : Les conteneurs ne démarrent pas
  - **Solution** : Vérifiez les logs avec `docker-compose logs` pour identifier le problème

- **Problème** : Problèmes de base de données
  - **Solution** : 
    - Vérifiez que le conteneur db est en cours d'exécution
    - Vérifiez les logs de la base de données avec `docker-compose logs db`
    - Utilisez pgAdmin pour vérifier l'état de la base de données

- **Problème** : Erreurs d'API dans le frontend
  - **Solution** :
    - Vérifiez que le backend est accessible
    - Vérifiez les logs du backend avec `docker-compose logs backend`

- **Problème** : Erreur OpenSSL lors du build du frontend
  - **Solution** :
    - Cette erreur peut survenir avec Node.js v18 et les versions récentes d'OpenSSL
    - Le message d'erreur typique est : `error:0308010C:digital envelope routines::unsupported`
    - La solution est déjà implémentée dans le Dockerfile du frontend avec `ENV NODE_OPTIONS=--openssl-legacy-provider`
    - Si vous rencontrez cette erreur en développement local, exécutez : `export NODE_OPTIONS=--openssl-legacy-provider` avant de lancer le frontend

- **Problème** : Erreur qemu-x86_64 dans le backend
  - **Solution** :
    - Cette erreur peut survenir lors de l'exécution de binaires x86_64 sur une architecture différente (comme ARM)
    - Le message d'erreur typique est : `qemu-x86_64: Could not open '/lib64/ld-linux-x86-64.so.2': No such file or directory`
    - La solution est d'installer qemu-user-static dans le conteneur, ce qui est maintenant implémenté dans le Dockerfile du backend

- **Problème** : Avertissements de dépréciation dans les logs du backend
  - **Solution** :
    - Les avertissements concernant `datetime.datetime.utcnow()` et `pkg_resources` ont été corrigés
    - Si vous voyez d'autres avertissements, ils sont généralement informatifs et n'affectent pas le fonctionnement de l'application

- **Problème** : Erreur de dépendance Python lors du build du backend
  - **Solution** :
    - Si vous rencontrez une erreur `ERROR: ResolutionImpossible` ou `ERROR: No matching distribution found for py-evm==0.5.0a4`, c'est un problème de conflit de dépendances
    - Modifiez le fichier `backend/requirements.txt` pour remplacer `py-evm==0.5.0a4` ou `py-evm==0.5.0a3` par simplement `py-evm` sans contrainte de version
    - Nettoyez les images Docker avec `docker-compose down -v --rmi all` avant de reconstruire

- **Problème** : "No response from server" dans le frontend
  - **Solution** :
    - Vérifiez que le backend est en cours d'exécution avec `docker-compose ps`
    - Si le backend est en état "restarting", vérifiez les logs avec `docker-compose logs backend`
    - Si vous voyez une erreur d'importation comme `ModuleNotFoundError: No module named 'api'`, c'est un problème de chemin d'importation
    - Modifiez les imports dans `backend/app.py` pour utiliser des imports relatifs (par exemple, changez `from api import register_blueprints` en `from .api import register_blueprints`)
    - Redémarrez le backend avec `docker-compose restart backend`
