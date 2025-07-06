# SmartContractAnalyser - Documentation Complète du Projet

## 📋 Vue d'ensemble

SmartContractAnalyser est une application web complète conçue pour analyser les smart contracts Solidity, détecter les vulnérabilités potentielles et générer des rapports détaillés. Le système utilise l'intelligence artificielle (via l'API OpenAI) pour analyser le code et identifier les failles de sécurité possibles.

## 🏗️ Architecture du Système

Le projet est construit sur une architecture microservices, avec les composants suivants:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│  Database   │
│   (React)   │◀────│   (Flask)   │◀────│ (Postgres)  │
└─────────────┘     └─────────────┘     └─────────────┘
                          │  ▲                 ▲
                          │  │                 │
                          ▼  │                 │
                    ┌─────────────┐    ┌──────────────┐
                    │   OpenAI    │    │   pgAdmin    │
                    │     API     │    │ (DB Manager) │
                    └─────────────┘    └──────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │   Ganache   │
                    │ (Eth Test)  │
                    └─────────────┘
```

### 🔄 Réseaux Docker

Le système utilise deux réseaux Docker pour isoler et sécuriser les communications:

1. **web_network**: Connecte le frontend et le backend
2. **data_network**: Connecte le backend, la base de données, pgAdmin et Ganache

## 🧩 Composants du Système

### 1. Frontend (React)

- **Port**: 80 (exposé sur 4456)
- **Fonctionnalités**:
  - Interface utilisateur pour soumettre des smart contracts
  - Affichage des étapes d'analyse en temps réel
  - Visualisation des rapports d'analyse
  - Système de feedback sur les résultats d'analyse
  - Historique des analyses précédentes

### 2. Backend (Flask)

- **Port**: 8000 (exposé sur 4455)
- **Fonctionnalités**:
  - API RESTful pour l'analyse de smart contracts
  - Authentification et gestion des utilisateurs
  - Compilation et déploiement des contrats sur Ganache
  - Intégration avec l'API OpenAI pour l'analyse avancée
  - Génération de rapports détaillés
  - Stockage des résultats dans la base de données

### 3. Base de données (PostgreSQL)

- **Port**: 5432
- **Fonctionnalités**:
  - Stockage des informations utilisateurs
  - Historique des analyses de contrats
  - Rapports générés
  - Feedback des utilisateurs

### 4. pgAdmin

- **Port**: 80 (exposé sur 4457)
- **Fonctionnalités**:
  - Interface web pour gérer la base de données
  - Visualisation des tables et des données
  - Exécution de requêtes SQL

### 5. Ganache

- **Port**: 8545
- **Fonctionnalités**:
  - Blockchain Ethereum locale pour les tests
  - Déploiement et test des smart contracts
  - Simulation d'attaques potentielles
  - Environnement isolé et déterministe

## 🔄 Flux de Travail: Analyse d'un Smart Contract

### Côté Frontend

1. **Soumission du contrat**:
   - L'utilisateur colle le code Solidity ou télécharge un fichier .sol
   - Le frontend valide le format basique (présence de code)
   - L'interface affiche un tableau d'avancement avec les étapes à venir

2. **Envoi au backend**:
   - Le code est envoyé via une requête POST à l'endpoint `/analyze`
   - Le token JWT d'authentification est inclus dans l'en-tête

3. **Affichage de la progression**:
   - Le frontend simule les étapes initiales (vérification du format)
   - À mesure que le backend progresse, le tableau est mis à jour
   - Les étapes complétées sont marquées avec ✅, les étapes en cours avec ⏳

4. **Affichage des résultats**:
   - Une fois l'analyse terminée, le rapport est affiché
   - L'utilisateur peut télécharger le rapport au format Markdown
   - Un formulaire de feedback est présenté pour évaluer la qualité de l'analyse

### Côté Backend

1. **Réception et validation**:
   - Le backend reçoit le code via l'endpoint `/analyze`
   - L'authentification de l'utilisateur est vérifiée via le token JWT
   - Le code est validé pour s'assurer qu'il s'agit bien de Solidity

2. **Compilation du contrat**:
   - Le code est sauvegardé dans un fichier temporaire
   - Le contrat est compilé pour vérifier sa syntaxe
   - Si la compilation échoue, une erreur est renvoyée

3. **Déploiement sur Ganache**:
   - Le contrat compilé est déployé sur la blockchain Ganache
   - Les fonctions d'initialisation sont appelées automatiquement
   - Le contrat est financé avec des ETH de test pour simuler des interactions

4. **Analyse de sécurité**:
   - Le backend utilise Slither (un analyseur statique) pour une première analyse
   - Les résultats de Slither sont combinés avec des observations du contrat déployé
   - Ces informations sont envoyées à l'API OpenAI pour une analyse approfondie

5. **Génération du rapport**:
   - OpenAI analyse le contrat et génère:
     - Un résumé des vulnérabilités potentielles
     - Un raisonnement détaillé sur les problèmes identifiés
     - Un code d'exploit si une vulnérabilité est détectée
   - Le backend détermine si le contrat est sécurisé (OK) ou vulnérable (KO)
   - Un rapport complet est généré au format Markdown

6. **Sauvegarde des résultats**:
   - Le rapport est sauvegardé dans la base de données PostgreSQL
   - Il est associé à l'utilisateur qui a soumis le contrat
   - Le rapport est renvoyé au frontend pour affichage

## 🔐 Rôle des Variables d'Environnement

- **OPENAI_API_KEY**: Clé d'API pour accéder aux services OpenAI (GPT-4)
- **DATABASE_URL**: URL de connexion à la base de données PostgreSQL
- **FLASK_APP**: Point d'entrée de l'application Flask
- **FLASK_RUN_HOST**: Adresse IP sur laquelle Flask écoute (0.0.0.0 pour Docker)
- **REACT_APP_API_URL**: URL du backend pour les requêtes API du frontend
- **POSTGRES_USER/PASSWORD/DB**: Identifiants pour la base de données
- **PGADMIN_DEFAULT_EMAIL/PASSWORD**: Identifiants pour pgAdmin
- **GANACHE_URL**: URL de connexion à Ganache (http://ganache:8545 par défaut)

## 🔄 Utilisation de Ganache dans le Projet

### Intégration de Ganache

SmartContractAnalyser utilise **activement Ganache** comme composant essentiel de son architecture. Ganache fournit une blockchain Ethereum locale qui permet:

- Le déploiement des smart contracts soumis pour analyse
- L'exécution des tests de vulnérabilité en environnement contrôlé
- La simulation d'attaques potentielles sans risque financier
- L'observation du comportement des contrats en conditions réelles simulées

Lorsqu'un utilisateur soumet un contrat pour analyse, le backend:
1. Compile le contrat Solidity
2. Déploie automatiquement le contrat sur l'instance Ganache
3. Interagit avec le contrat pour observer son comportement
4. Utilise ces observations pour alimenter l'analyse de sécurité

Cette approche permet d'analyser non seulement le code statique, mais aussi le comportement dynamique du contrat en situation d'exécution.

### Configuration de Ganache

Ganache est configuré dans le fichier docker-compose.yml avec les paramètres suivants:
- Réseau déterministe (même seed à chaque démarrage)
- 10 comptes pré-financés avec 100 ETH chacun
- NetworkID et ChainID fixés à 1337
- Accessible via l'URL `http://ganache:8545` dans le réseau Docker

Le backend se connecte à Ganache via la variable d'environnement `GANACHE_URL` définie dans la configuration.

## 🔄 Ganache vs. Réseau Ethereum Réel

### Ganache (Environnement Local)

- **Avantages**:
  - Environnement contrôlé et déterministe
  - Transactions gratuites et instantanées
  - Possibilité de réinitialiser l'état facilement
  - Comptes pré-financés pour les tests
  - Pas de risque financier réel

- **Limitations**:
  - Ne reproduit pas exactement les conditions du réseau principal
  - Pas d'interaction avec d'autres contrats déployés
  - Latence et coûts de gaz non réalistes

### Réseau Ethereum Principal (Mainnet)

- **Différences**:
  - Transactions coûteuses (frais de gaz réels)
  - Temps de confirmation variables (15 secondes à plusieurs minutes)
  - Environnement non déterministe avec d'autres acteurs
  - Risques financiers réels en cas de vulnérabilité
  - Interaction possible avec l'écosystème complet des contrats déployés

## 📊 Modèles de Données

### Utilisateur (User)
- **id**: Identifiant unique
- **wallet**: Adresse du portefeuille Ethereum (identifiant unique)
- **hashed_password**: Mot de passe hashé
- **technical_score**: Score technique de l'utilisateur (0-5)
- **technical_level**: Niveau technique basé sur le score

### Rapport (Report)
- **id**: Identifiant unique
- **user_id**: ID de l'utilisateur qui a soumis le contrat
- **filename**: Nom du fichier généré
- **status**: Statut de l'analyse (OK, KO, ERROR)
- **attack**: Type de vulnérabilité détectée
- **contract_name**: Nom du contrat analysé
- **contract_address**: Adresse de déploiement sur Ganache
- **solc_version**: Version du compilateur Solidity
- **summary**: Résumé de l'analyse
- **reasoning**: Raisonnement détaillé
- **exploit_code**: Code d'exploit généré
- **code_result**: Résultat binaire (1 pour OK, 0 pour KO)
- **created_at**: Date de création

### Feedback
- **id**: Identifiant unique
- **user_id**: ID de l'utilisateur qui a donné le feedback
- **report_id**: ID du rapport concerné
- **status**: Évaluation de l'utilisateur (OK ou KO)
- **comment**: Commentaire optionnel
- **code_result**: Résultat binaire (1 pour OK, 0 pour KO)
- **weight_request**: Poids calculé en fonction du niveau technique
- **created_at**: Date de création

## 🛠️ Modules Techniques Clés

### Authentification
- Système basé sur JWT (JSON Web Tokens)
- Tokens avec expiration d'une heure
- Middleware de vérification des tokens pour les routes protégées

### Analyse de Contrats
- Compilation via solc (compilateur Solidity)
- Analyse statique avec Slither
- Déploiement et test sur Ganache
- Analyse avancée via l'API OpenAI

### Génération de Rapports
- Format Markdown structuré
- Sections détaillées (résumé, raisonnement, code d'exploit)
- Stockage dans la base de données

## 🚀 Conclusion

SmartContractAnalyser est une plateforme complète qui combine des technologies modernes pour offrir une analyse approfondie des smart contracts Solidity. En utilisant l'IA, la blockchain et une architecture microservices, le système permet aux développeurs de détecter les vulnérabilités potentielles avant le déploiement sur le réseau principal Ethereum, réduisant ainsi les risques financiers et de sécurité.
