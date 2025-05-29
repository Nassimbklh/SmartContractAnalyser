# SmartContractAnalyser

Un outil pour analyser les contrats intelligents à la recherche de vulnérabilités et d'exploits potentiels.

## Prérequis

- **Docker** : Nécessaire pour exécuter l'application conteneurisée
- **Docker Compose** : Nécessaire pour orchestrer l'application multi-conteneurs
- **Git** : Nécessaire pour cloner le dépôt
- **Navigateur Web** : Chrome, Firefox, Edge ou Safari pour accéder à l'interface web
- **Clé API OpenAI** : Nécessaire pour la fonctionnalité d'analyse des contrats intelligents

## Guide d'installation et de lancement

### 1. Cloner le dépôt

```bash
git clone https://github.com/yourusername/SmartContractAnalyser.git
cd SmartContractAnalyser
```

### 2. Créer le fichier d'environnement

Créez un fichier `.env` à la racine du projet avec le contenu suivant :

```
# Clé API OpenAI (Requise pour l'analyse des contrats intelligents)
OPENAI_API_KEY=votre_clé_api_openai_ici

# Configuration de la base de données
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=mydb
DATABASE_URL=postgresql://user:password@db:5432/mydb

# Configuration du frontend
REACT_APP_API_URL=http://localhost:4455
```

### 3. Rendre le script de démarrage exécutable

```bash
chmod +x start.sh
```

### 4. Lancer l'application

```bash
./start.sh
```

Le script va :
- Vérifier les prérequis (Docker, Docker Compose, fichier .env)
- Arrêter les conteneurs existants
- Construire et démarrer tous les conteneurs
- Vérifier que tous les services fonctionnent correctement
- Afficher les URLs d'accès et les identifiants

## Accès aux services

### Frontend (Interface Web)

- **URL** : http://localhost:4456
- **Description** : Interface web pour analyser les contrats intelligents
- **Fonctionnalités** :
  - Inscription et connexion utilisateur
  - Analyse de contrats intelligents
  - Historique des analyses
  - Téléchargement de rapports

### API Backend

- **URL** : http://localhost:4455
- **Description** : API REST pour l'analyse des contrats intelligents
- **Points d'accès** :
  - `/register` - Inscrire un nouvel utilisateur
  - `/login` - Se connecter et obtenir un jeton d'accès
  - `/analyze` - Analyser un contrat intelligent
  - `/history` - Obtenir l'historique des analyses
  - `/report/<wallet>/<filename>` - Obtenir un rapport d'analyse spécifique

### Gestion de la base de données (pgAdmin)

- **URL** : http://localhost:4457
- **Identifiants** : 
  - Email : admin@admin.com
  - Mot de passe : admin
- **Pour se connecter à la base de données** :
  1. Ajouter un nouveau serveur
  2. Nom : mydb
  3. Onglet Connexion :
     - Hôte : db
     - Port : 5432
     - Base de données : mydb
     - Nom d'utilisateur : user
     - Mot de passe : password

## Comment tester l'application

1. Ouvrez le frontend dans votre navigateur : http://localhost:4456
2. Inscrivez-vous ou connectez-vous avec un compte existant
3. Sur la page d'analyse :
   - Collez directement le code Solidity dans le champ de texte
   - OU téléchargez un fichier .sol
4. Cliquez sur "Lancer l'analyse"
5. Attendez que l'analyse soit terminée
6. Examinez les résultats et téléchargez le rapport si nécessaire
7. Accédez à l'historique de vos analyses via le menu

## Commandes de gestion Docker

### Affichage des logs

```bash
# Afficher les logs de tous les conteneurs
docker-compose logs

# Afficher les logs d'un service spécifique
docker-compose logs [backend|frontend|db|pgadmin]

# Suivre les logs en temps réel
docker-compose logs -f
```

### Gestion des conteneurs

```bash
# Arrêter tous les conteneurs
docker-compose down

# Arrêter les conteneurs et supprimer les volumes
docker-compose down -v

# Arrêter les conteneurs, supprimer les volumes et les images
docker-compose down -v --rmi all

# Redémarrer un service spécifique
docker-compose restart [nom_du_service]
```

## Persistance des données avec les volumes Docker

L'application utilise des volumes Docker pour conserver les données même lorsque les conteneurs sont arrêtés ou reconstruits :

- **pgdata** : Stocke les fichiers de la base de données PostgreSQL
  - Nom du volume : smartcontract-analyser-postgres-data
  - Objectif : Préserve les comptes utilisateurs, les rapports d'analyse et tout le contenu de la base de données

- **pgadmin-data** : Stocke la configuration de pgAdmin
  - Nom du volume : smartcontract-analyser-pgadmin-data
  - Objectif : Préserve les paramètres de pgAdmin, les connexions aux serveurs et les préférences

Cela signifie que vous pouvez arrêter, redémarrer ou même reconstruire les conteneurs sans perdre vos données. Les volumes persisteront jusqu'à ce qu'ils soient explicitement supprimés avec `docker-compose down -v`.

## Dépannage

- **Problème** : Le frontend ne peut pas se connecter au backend
  - **Solution** : Vérifiez que la variable d'environnement REACT_APP_API_URL est correctement définie dans le fichier .env

- **Problème** : L'analyse des contrats échoue
  - **Solution** : Vérifiez que votre clé API OpenAI est valide et correctement définie dans le fichier .env

- **Problème** : Impossible de se connecter à pgAdmin
  - **Solution** : Vérifiez que le conteneur pgAdmin est en cours d'exécution avec `docker-compose ps`

- **Problème** : Erreur OpenSSL dans le frontend
  - **Solution** : Ceci est géré automatiquement dans la configuration Docker. Pour le développement local, utilisez `export NODE_OPTIONS=--openssl-legacy-provider`

Pour un dépannage plus détaillé, consultez les logs des conteneurs avec `docker-compose logs`.

## Structure du projet

- **backend/** : Code backend Flask
  - **api/** : Points d'accès API
  - **models/** : Modèles de base de données
  - **services/** : Logique métier
  - **utils/** : Fonctions utilitaires
  - **config/** : Configuration de l'application
  - **rlhf_agent/** : Logique d'analyse des contrats intelligents

- **react-client/** : Code frontend React
  - **src/components/** : Composants React
  - **src/contexts/** : Contextes React
  - **src/services/** : Services API
  - **src/utils/** : Fonctions utilitaires