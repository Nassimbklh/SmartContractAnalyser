# Communication entre le Backend et le Frontend

## Architecture Globale

L'application SmartContractAnalyser est composée de deux parties principales :

1. **Frontend** : Une application React qui fournit l'interface utilisateur
2. **Backend** : Une API Flask qui gère l'authentification, l'analyse des contrats intelligents et le stockage des données

La communication entre ces deux parties se fait via des requêtes HTTP, avec le frontend qui appelle les endpoints de l'API backend.

## Endpoints API et Communication

### 1. Authentification

#### Inscription (`/register`)

- **Type de requête** : POST
- **Contenu de la requête** : JSON avec `wallet` (adresse du portefeuille) et `password` (mot de passe)
- **Réponse attendue** : JSON avec `success` (booléen) et `message` (texte de confirmation)
- **Fonction frontend** : `authAPI.register(userData)`
- **Fonction backend** : `register()` dans `auth.py`
- **Flux de données** :
  1. Le frontend envoie les informations d'inscription
  2. Le backend valide les données
  3. Le backend crée un nouvel utilisateur avec le mot de passe hashé
  4. Le backend renvoie une confirmation

#### Connexion (`/login`)

- **Type de requête** : POST
- **Contenu de la requête** : JSON avec `wallet` (adresse du portefeuille) et `password` (mot de passe)
- **Réponse attendue** : JSON avec `success` (booléen) et `data.access_token` (token JWT)
- **Fonction frontend** : `authAPI.login(credentials)`
- **Fonction backend** : `login()` dans `auth.py`
- **Flux de données** :
  1. Le frontend envoie les identifiants
  2. Le backend vérifie les identifiants
  3. Le backend génère un token JWT
  4. Le backend renvoie le token
  5. Le frontend stocke le token dans localStorage

### 2. Analyse de Contrats Intelligents

#### Analyse de contrat (`/analyze`)

- **Type de requête** : POST
- **Contenu de la requête** : FormData avec `file` (fichier .sol) ou `code` (code Solidity)
- **En-têtes** : `Authorization: Bearer <token>` et `Content-Type: multipart/form-data`
- **Réponse attendue** : Texte brut (rapport d'analyse au format markdown)
- **Fonction frontend** : `contractAPI.analyze(formData)`
- **Fonction backend** : `analyze(wallet)` dans `contract.py`
- **Flux de données** :
  1. Le frontend envoie le code ou le fichier Solidity
  2. Le backend extrait le wallet du token JWT
  3. Le backend compile et déploie le contrat sur Ganache
  4. Le backend analyse le contrat avec l'API OpenAI
  5. Le backend génère et sauvegarde un rapport
  6. Le backend renvoie le rapport au format texte

#### Historique des analyses (`/history`)

- **Type de requête** : GET
- **En-têtes** : `Authorization: Bearer <token>`
- **Réponse attendue** : JSON avec `success` (booléen) et `data` (liste de rapports)
- **Fonction frontend** : `contractAPI.getHistory()`
- **Fonction backend** : `history(wallet)` dans `contract.py`
- **Flux de données** :
  1. Le frontend demande l'historique
  2. Le backend extrait le wallet du token JWT
  3. Le backend récupère tous les rapports de l'utilisateur
  4. Le backend renvoie la liste formatée des rapports

#### Téléchargement de rapport (`/report/<wallet>/<filename>`)

- **Type de requête** : GET
- **En-têtes** : `Authorization: Bearer <token>`
- **Paramètres d'URL** : `wallet` (adresse du portefeuille) et `filename` (nom du fichier)
- **Réponse attendue** : Blob (contenu du rapport)
- **Fonction frontend** : `contractAPI.getReport(wallet, filename)`
- **Fonction backend** : `download_report(token_wallet, wallet, filename)` dans `contract.py`
- **Flux de données** :
  1. Le frontend demande un rapport spécifique
  2. Le backend vérifie que le wallet du token correspond au wallet demandé
  3. Le backend récupère le rapport
  4. Le backend renvoie le contenu du rapport

## Processus d'Analyse de Contrat

Le processus d'analyse d'un contrat intelligent est le suivant :

1. **Frontend** : L'utilisateur soumet du code Solidity ou un fichier .sol via le formulaire d'analyse
2. **Backend** :
   - Reçoit la requête et extrait le contenu du contrat
   - Crée un fichier temporaire avec le code
   - Établit une connexion à Ganache (blockchain locale)
   - Compile le contrat avec solc
   - Déploie le contrat sur Ganache
   - Configure le contrat (appelle les fonctions d'initialisation)
   - Finance le contrat pour les tests d'attaque
   - Construit une observation du contrat (structure, fonctions, état)
   - Génère une stratégie d'attaque en utilisant l'API OpenAI (GPT-4)
   - Détermine si des vulnérabilités ont été trouvées
   - Crée et sauvegarde un rapport d'analyse
   - Génère un rapport markdown
   - Renvoie le rapport au frontend
3. **Frontend** :
   - Affiche le rapport d'analyse
   - Permet à l'utilisateur de télécharger le rapport

## Modules Backend Spécialisés

Le backend utilise plusieurs modules spécialisés pour l'analyse des contrats :

1. **contract_compiler.py** : Compile les contrats Solidity
2. **contract_deployer.py** : Déploie les contrats sur Ganache
3. **contract_analyzer.py** : Analyse la structure des contrats
4. **attack_generator.py** : Génère des stratégies d'attaque avec l'API OpenAI
5. **attack_executor.py** : Exécute les attaques sur les contrats
6. **attack_evaluator.py** : Évalue les résultats des attaques
7. **results_manager.py** : Gère et sauvegarde les résultats

## Gestion de l'Authentification

L'authentification utilise des tokens JWT (JSON Web Tokens) :

1. **Création du token** : Lors de la connexion, le backend génère un token JWT contenant l'adresse du portefeuille de l'utilisateur
2. **Stockage du token** : Le frontend stocke le token dans localStorage
3. **Utilisation du token** : Le frontend inclut le token dans l'en-tête Authorization de chaque requête
4. **Vérification du token** : Le backend vérifie le token avec le décorateur @token_required
5. **Extraction du wallet** : Le backend extrait l'adresse du portefeuille du token pour identifier l'utilisateur

## Modifications Récentes

### 1. Refactorisation du Backend

Le backend a été refactorisé pour utiliser une architecture modulaire :

- **Ancien système** : Un fichier unique `agent.py` contenait toutes les fonctionnalités
- **Nouveau système** : Le code a été divisé en modules spécialisés dans le dossier `backend/modules/`

### 2. Correction des Fichiers Dupliqués dans le Frontend

Les fichiers dupliqués entre `src/` et `src/components/` ont été corrigés :

- Les imports dans les fichiers du répertoire racine `src/` ont été mis à jour pour utiliser les composants depuis `src/components/`
- Le fichier `AuthContext.js` a été déplacé dans `src/contexts/`

### 3. Intégration de Ganache

Une instance Ganache a été ajoutée pour permettre la compilation et le déploiement des contrats :

- Ajout d'un service Ganache dans docker-compose.yml
- Configuration de GANACHE_URL dans Config

### 4. Correction du Traitement des Réponses API

Le traitement des réponses API a été corrigé :

- Modification du responseType dans contractAPI.analyze de 'blob' à 'text'
- Mise à jour des composants Analyze.js pour utiliser directement res.data
- Changement du type MIME et de l'extension de fichier pour les rapports téléchargés

### 5. Amélioration des Logs

Les logs ont été améliorés pour faciliter le débogage :

- Configuration de logging dans app.py
- Ajout de logs détaillés dans les modules d'analyse de contrat
- Création d'un guide pour visualiser les logs

## Conclusion

L'architecture de communication entre le frontend et le backend est basée sur des appels API RESTful, avec une authentification par token JWT. Le frontend utilise axios pour effectuer les requêtes, tandis que le backend utilise Flask pour gérer les routes API. Cette architecture permet une séparation claire des responsabilités et facilite la maintenance et l'évolution de l'application.