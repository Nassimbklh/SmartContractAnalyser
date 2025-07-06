# Guide de Déploiement sur Azure Container Apps

Ce guide détaille les étapes pour migrer le projet SmartContractAnalyser vers Azure, en utilisant Azure Container Apps pour chaque composant et Azure Database for PostgreSQL.

## Introduction

Le projet SmartContractAnalyser est composé de plusieurs services qui doivent être migrés vers Azure :

1. **Frontend React** : Interface utilisateur qui permet d'interagir avec l'application
2. **Backend Flask/Python** : API qui gère l'analyse des contrats intelligents, l'authentification et les interactions avec la base de données
3. **Ganache** : Blockchain Ethereum locale utilisée pour le déploiement et les tests des contrats intelligents
4. **PostgreSQL** : Base de données relationnelle pour stocker les utilisateurs, les rapports et autres données

La migration vers Azure Container Apps offre plusieurs avantages :
- Déploiement simplifié et standardisé des conteneurs
- Mise à l'échelle automatique en fonction de la charge
- Intégration avec d'autres services Azure comme Azure Database for PostgreSQL
- Surveillance et journalisation centralisées
- Haute disponibilité et fiabilité

Ce guide vous accompagne à travers toutes les étapes nécessaires, de la préparation des images Docker jusqu'à la configuration des variables d'environnement et la vérification de la compatibilité du code.

## Table des matières

1. [Préparation des images Docker](#1-préparation-des-images-docker)
2. [Déploiement des services sur Azure Container Apps](#2-déploiement-des-services-sur-azure-container-apps)
3. [Configuration de la base de données PostgreSQL Azure](#3-configuration-de-la-base-de-données-postgresql-azure)
4. [Configuration des variables d'environnement](#4-configuration-des-variables-denvironnement)
5. [Commandes Azure CLI pour la gestion](#5-commandes-azure-cli-pour-la-gestion)
6. [Stratégies de mise à jour des applications](#6-stratégies-de-mise-à-jour-des-applications)
7. [Vérification de compatibilité du code](#7-vérification-de-compatibilité-du-code)

## 1. Préparation des images Docker

### 1.1 Backend (Flask/Python)

```bash
# Se positionner dans le répertoire du backend
cd backend

# Construire l'image Docker
docker build -t smartcontract-backend:latest .

# Tagger l'image pour Azure Container Registry (ACR)
docker tag smartcontract-backend:latest <your-acr-name>.azurecr.io/smartcontract-backend:latest

# Pousser l'image vers ACR
docker push <your-acr-name>.azurecr.io/smartcontract-backend:latest
```

### 1.2 Frontend (React)

```bash
# Se positionner dans le répertoire du frontend
cd ../react-client

# Construire l'image Docker
docker build -t smartcontract-frontend:latest .

# Tagger l'image pour Azure Container Registry
docker tag smartcontract-frontend:latest <your-acr-name>.azurecr.io/smartcontract-frontend:latest

# Pousser l'image vers ACR
docker push <your-acr-name>.azurecr.io/smartcontract-frontend:latest
```

### 1.3 Ganache (Blockchain locale)

```bash
# Tagger l'image Ganache pour Azure Container Registry
docker pull trufflesuite/ganache-cli:latest
docker tag trufflesuite/ganache-cli:latest <your-acr-name>.azurecr.io/ganache:latest

# Pousser l'image vers ACR
docker push <your-acr-name>.azurecr.io/ganache:latest
```

## 2. Déploiement des services sur Azure Container Apps

### 2.1 Création d'un environnement Azure Container Apps

```bash
# Créer un groupe de ressources
az group create --name smartcontract-rg --location francecentral

# Créer un environnement Container Apps
az containerapp env create \
  --name smartcontract-env \
  --resource-group smartcontract-rg \
  --location francecentral
```

### 2.2 Déploiement du service Ganache

```bash
az containerapp create \
  --name smartcontract-ganache \
  --resource-group smartcontract-rg \
  --environment smartcontract-env \
  --image <your-acr-name>.azurecr.io/ganache:latest \
  --target-port 8545 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 1 \
  --command "--deterministic --networkId 1337 --chainId 1337 --accounts 10 --defaultBalanceEther 100" \
  --registry-server <your-acr-name>.azurecr.io \
  --registry-username <your-acr-username> \
  --registry-password <your-acr-password>
```

### 2.3 Déploiement du service Backend

```bash
az containerapp create \
  --name smartcontract-backend \
  --resource-group smartcontract-rg \
  --environment smartcontract-env \
  --image <your-acr-name>.azurecr.io/smartcontract-backend:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --env-vars "DATABASE_URL=postgresql://<username>:<password>@<postgresql-server-name>.postgres.database.azure.com:5432/<database-name>?sslmode=require" "GANACHE_URL=https://smartcontract-ganache.internal.<env-domain>" "OPENAI_API_KEY=<your-openai-api-key>" \
  --registry-server <your-acr-name>.azurecr.io \
  --registry-username <your-acr-username> \
  --registry-password <your-acr-password>
```

### 2.4 Déploiement du service Frontend

```bash
az containerapp create \
  --name smartcontract-frontend \
  --resource-group smartcontract-rg \
  --environment smartcontract-env \
  --image <your-acr-name>.azurecr.io/smartcontract-frontend:latest \
  --target-port 80 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --env-vars "REACT_APP_API_URL=https://smartcontract-backend.<env-domain>" \
  --registry-server <your-acr-name>.azurecr.io \
  --registry-username <your-acr-username> \
  --registry-password <your-acr-password>
```

## 3. Configuration de la base de données PostgreSQL Azure

### 3.1 Création d'une instance PostgreSQL

```bash
# Créer un serveur PostgreSQL
az postgres flexible-server create \
  --name smartcontract-postgres \
  --resource-group smartcontract-rg \
  --location francecentral \
  --admin-user <admin-username> \
  --admin-password <admin-password> \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 15

# Créer une base de données
az postgres flexible-server db create \
  --resource-group smartcontract-rg \
  --server-name smartcontract-postgres \
  --database-name mydb
```

### 3.2 Configuration des règles de pare-feu

```bash
# Autoriser l'accès depuis les services Azure
az postgres flexible-server firewall-rule create \
  --resource-group smartcontract-rg \
  --name smartcontract-postgres \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### 3.3 Connexion du backend à PostgreSQL

La chaîne de connexion à PostgreSQL est fournie via la variable d'environnement `DATABASE_URL` lors de la création du service backend. Assurez-vous que le format est correct :

```
postgresql://<username>:<password>@<postgresql-server-name>.postgres.database.azure.com:5432/<database-name>?sslmode=require
```

## 4. Configuration des variables d'environnement

### 4.1 Variables d'environnement pour le Backend

| Variable | Description | Exemple |
|----------|-------------|---------|
| DATABASE_URL | URL de connexion à PostgreSQL | postgresql://user:password@smartcontract-postgres.postgres.database.azure.com:5432/mydb?sslmode=require |
| GANACHE_URL | URL du service Ganache | https://smartcontract-ganache.internal.<env-domain> |
| OPENAI_API_KEY | Clé API OpenAI | sk-... |
| SECRET_KEY | Clé secrète pour Flask | votre-clé-secrète |

### 4.2 Variables d'environnement pour le Frontend

| Variable | Description | Exemple |
|----------|-------------|---------|
| REACT_APP_API_URL | URL du backend | https://smartcontract-backend.<env-domain> |
| NODE_OPTIONS | Options Node.js | --openssl-legacy-provider |

## 5. Commandes Azure CLI pour la gestion

### 5.1 Création et configuration

```bash
# Créer un Azure Container Registry (ACR)
az acr create --name <your-acr-name> --resource-group smartcontract-rg --sku Basic --admin-enabled true

# Récupérer les informations d'identification ACR
az acr credential show --name <your-acr-name>
```

### 5.2 Mise à jour des applications

```bash
# Mettre à jour une application container
az containerapp update \
  --name smartcontract-backend \
  --resource-group smartcontract-rg \
  --image <your-acr-name>.azurecr.io/smartcontract-backend:latest
```

### 5.3 Surveillance et journaux

```bash
# Afficher les journaux d'une application
az containerapp logs show \
  --name smartcontract-backend \
  --resource-group smartcontract-rg \
  --follow

# Obtenir des informations sur une révision spécifique
az containerapp revision list \
  --name smartcontract-backend \
  --resource-group smartcontract-rg
```

### 5.4 Mise à l'échelle

```bash
# Configurer la mise à l'échelle automatique
az containerapp update \
  --name smartcontract-backend \
  --resource-group smartcontract-rg \
  --min-replicas 1 \
  --max-replicas 5
```

## 6. Stratégies de mise à jour des applications

### 6.1 Forcer un rafraîchissement avec une nouvelle image

```bash
# Mettre à jour l'image avec le tag latest
az containerapp update \
  --name smartcontract-backend \
  --resource-group smartcontract-rg \
  --image <your-acr-name>.azurecr.io/smartcontract-backend:latest
```

### 6.2 Utiliser un suffixe de révision

Pour éviter les problèmes de cache avec le tag `latest`, utilisez des tags spécifiques :

```bash
# Construire et pousser avec un tag de version
docker build -t <your-acr-name>.azurecr.io/smartcontract-backend:v1.0.1 .
docker push <your-acr-name>.azurecr.io/smartcontract-backend:v1.0.1

# Mettre à jour l'application avec le nouveau tag
az containerapp update \
  --name smartcontract-backend \
  --resource-group smartcontract-rg \
  --image <your-acr-name>.azurecr.io/smartcontract-backend:v1.0.1
```

### 6.3 Gestion des révisions

```bash
# Lister toutes les révisions
az containerapp revision list \
  --name smartcontract-backend \
  --resource-group smartcontract-rg

# Activer une révision spécifique
az containerapp revision activate \
  --name smartcontract-backend \
  --resource-group smartcontract-rg \
  --revision <revision-name>
```

## 7. Vérification de compatibilité du code

### 7.1 Backend (Flask)

Le code backend est compatible avec Azure Container Apps avec quelques ajustements mineurs :
- Utilise Gunicorn comme serveur WSGI avec un timeout approprié
- Écoute sur 0.0.0.0:8000
- Utilise des variables d'environnement pour la configuration
- Gère correctement les connexions à PostgreSQL et Ganache

#### Ajustements recommandés pour le backend

1. **Modification de la configuration de logging**

   Dans `app.py`, remplacez la configuration de logging qui utilise un fichier local par une configuration qui n'écrit que sur la console standard :

   ```python
   # Configuration actuelle
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.StreamHandler(),  # Log to console
           logging.FileHandler('backend.log')  # Also log to file
       ]
   )

   # Configuration recommandée pour Azure
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.StreamHandler(),  # Log to console only
       ]
   )
   ```

   Cette modification permet de s'assurer que les logs sont correctement capturés par Azure Container Apps sans dépendre d'un système de fichiers persistant.

### 7.2 Frontend (React)

Le frontend React est servi correctement via le package `serve` :
- L'application est construite avec `npm run build`
- Le serveur `serve` distribue les fichiers statiques
- Les variables d'environnement sont correctement configurées

#### Ajustements recommandés pour le frontend

1. **Mise à jour de la configuration des variables d'environnement**

   Dans le Dockerfile du frontend, la variable d'environnement REACT_APP_API_URL est définie au moment du build. Pour Azure, assurez-vous que cette variable pointe vers l'URL du backend déployé :

   ```dockerfile
   # Décommenter et mettre à jour cette ligne dans le Dockerfile du frontend
   ENV REACT_APP_API_URL="https://smartcontract-backend.<env-domain>"
   ```

   Alternativement, vous pouvez définir cette variable lors du déploiement de l'application container, comme indiqué dans la section 2.4.

2. **Configuration CORS pour le backend**

   Assurez-vous que la configuration CORS du backend autorise les requêtes depuis le domaine du frontend déployé sur Azure. La configuration actuelle autorise toutes les origines (`"*"`), ce qui est acceptable pour un environnement de test, mais vous pourriez vouloir la restreindre en production.

### 7.3 Ganache

Ganache fonctionne correctement dans un container Linux amd64 sur Azure :
- L'image trufflesuite/ganache-cli est compatible
- Les paramètres de ligne de commande sont correctement configurés
- Le port 8545 est exposé pour les connexions

#### Considérations importantes pour Ganache

1. **Persistance des données**

   Par défaut, Ganache ne persiste pas les données entre les redémarrages du container. Dans Azure Container Apps, cela signifie que l'état de la blockchain sera réinitialisé si le container est redémarré ou si une nouvelle révision est déployée. Cela peut être acceptable pour un environnement de test, mais pour un environnement de production ou de développement plus stable, considérez les options suivantes :

   - Utiliser le mode déterministe de Ganache (comme configuré actuellement avec `--deterministic`) pour garantir que les mêmes comptes et clés privées sont générés à chaque démarrage
   - Si une persistance plus robuste est nécessaire, envisagez d'utiliser un service blockchain géré comme Azure Blockchain Service ou de configurer un nœud Ethereum plus robuste

2. **Communication interne**

   Dans la configuration Azure Container Apps, Ganache est configuré avec `--ingress internal`, ce qui signifie qu'il n'est accessible que depuis d'autres services dans le même environnement Container Apps. Assurez-vous que le backend utilise l'URL interne correcte pour se connecter à Ganache :

   ```
   GANACHE_URL=https://smartcontract-ganache.internal.<env-domain>
   ```

### 7.4 Dépendances

Toutes les dépendances sont supportées dans Azure Container Apps :
- py-solc-x et solcx fonctionnent correctement dans l'environnement containerisé
- Les dépendances système nécessaires sont installées dans le Dockerfile
- La version de Python (3.12-slim) est compatible

#### Considérations pour py-solc-x et Slither

1. **Installation de solc**

   Le Dockerfile du backend installe déjà la version 0.8.20 de solc via py-solc-x :

   ```dockerfile
   # Installer uniquement la version 0.8.20
   RUN python -c "from solcx import install_solc; install_solc('0.8.20')"
   ```

   Cette approche fonctionne correctement dans Azure Container Apps. Cependant, si vous avez besoin de plusieurs versions de solc, assurez-vous de les installer explicitement dans le Dockerfile.

2. **Dépendances système pour Slither**

   Si vous utilisez Slither pour l'analyse de sécurité, assurez-vous que toutes les dépendances système nécessaires sont installées. Le Dockerfile actuel installe déjà les packages essentiels :

   ```dockerfile
   RUN apt-get update && apt-get install -y \
       build-essential \
       gcc \
       python3-dev \
       curl \
       git \
       qemu-user-static \
       && rm -rf /var/lib/apt/lists/*
   ```

   Ces dépendances devraient être suffisantes pour exécuter Slither dans Azure Container Apps.

3. **Optimisation de la taille de l'image**

   Pour optimiser la taille de l'image Docker et améliorer les performances de déploiement sur Azure, considérez l'utilisation d'images multi-étapes. Par exemple :

   ```dockerfile
   # Étape de build
   FROM python:3.12-slim AS builder
   RUN apt-get update && apt-get install -y \
       build-essential gcc python3-dev curl git
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   RUN pip install --no-cache-dir py-solc-x
   RUN python -c "from solcx import install_solc; install_solc('0.8.20')"

   # Étape finale
   FROM python:3.12-slim
   RUN apt-get update && apt-get install -y \
       gcc python3-dev && rm -rf /var/lib/apt/lists/*
   WORKDIR /app
   COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
   COPY --from=builder /root/.solcx /root/.solcx
   COPY . .
   CMD ["gunicorn", "--timeout", "180", "-b", "0.0.0.0:8000", "app:app"]
   ```

   Cette approche peut réduire significativement la taille de l'image finale.

## Conclusion

Ce guide vous a fourni toutes les étapes nécessaires pour migrer votre application SmartContractAnalyser vers Azure Container Apps. En suivant ces instructions, vous aurez une architecture cloud robuste et évolutive pour votre application d'analyse de contrats intelligents.

N'oubliez pas de surveiller régulièrement vos applications déployées et d'ajuster les paramètres de mise à l'échelle en fonction de vos besoins.
