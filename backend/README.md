# Structure du Backend

Ce document explique l'organisation du code dans le dossier backend du projet SmartContractAnalyser.

## Vue d'ensemble

Le backend est organisé selon une architecture modulaire qui sépare les différentes préoccupations du code :

- **API** : Points d'entrée HTTP de l'application
- **Models** : Définitions des modèles de données
- **Services** : Logique métier
- **Utils** : Fonctions utilitaires
- **Config** : Configuration de l'application

## Structure des dossiers

### `/api`

Ce dossier contient les définitions des routes API (endpoints) de l'application.

- `auth.py` : Routes liées à l'authentification (login, register, etc.)
- `contract.py` : Routes liées aux opérations sur les smart contracts

### `/models`

Ce dossier contient les définitions des modèles de données utilisés par l'application.

- `base.py` : Classe de base pour les modèles et configuration de la connexion à la base de données
- `user.py` : Modèle pour les utilisateurs
- `report.py` : Modèle pour les rapports d'analyse de smart contracts

### `/services`

Ce dossier contient la logique métier de l'application, séparée des routes API.

- `user_service.py` : Services liés aux opérations sur les utilisateurs
- `contract_service.py` : Services liés aux opérations sur les smart contracts

### `/modules`

Ce dossier contient les modules spécialisés pour l'analyse des smart contracts, remplaçant l'ancien fichier agent.py.

- `contract_compiler.py` : Compilation des smart contracts
- `contract_deployer.py` : Déploiement des contrats
- `contract_analyzer.py` : Analyse de la structure des contrats
- `attack_generator.py` : Génération des stratégies d'attaque
- `attack_executor.py` : Exécution des attaques
- `attack_evaluator.py` : Évaluation des résultats d'attaque
- `results_manager.py` : Gestion et sauvegarde des résultats

### `/utils`

Ce dossier contient des fonctions utilitaires réutilisables dans toute l'application.

- `auth.py` : Fonctions liées à l'authentification (gestion des tokens JWT, hachage de mots de passe)
- `responses.py` : Fonctions pour formater les réponses API
- `openai_utils.py` : Fonctions pour l'initialisation et l'utilisation de l'API OpenAI

### `/config`

Ce dossier contient la configuration de l'application.

- `config.py` : Paramètres de configuration (clés secrètes, URLs, etc.)

### Fichiers à la racine du backend

- `app.py` : Point d'entrée principal de l'application Flask
- `requirements.txt` : Liste des dépendances Python
- `Dockerfile` : Instructions pour créer l'image Docker du backend

## Flux d'exécution

1. L'application démarre via `app.py`
2. Les routes API sont enregistrées à partir des blueprints dans le dossier `/api`
3. Quand une requête arrive, elle est dirigée vers la route appropriée
4. La route appelle les services nécessaires pour exécuter la logique métier
5. Les services interagissent avec les modèles pour accéder aux données
6. Les utilitaires sont utilisés selon les besoins tout au long du processus

## Avantages de cette structure

Cette organisation modulaire présente plusieurs avantages :

- **Séparation des préoccupations** : Chaque partie du code a une responsabilité claire
- **Maintenabilité** : Il est plus facile de trouver et modifier du code spécifique
- **Testabilité** : Les composants peuvent être testés indépendamment
- **Évolutivité** : Nouveaux modules peuvent être ajoutés sans perturber l'existant
- **Réutilisabilité** : Les fonctions utilitaires et services peuvent être réutilisés

## Différence avec l'ancienne structure

Auparavant, le backend était organisé en un seul fichier ou quelques fichiers à plat. La nouvelle structure modulaire offre une meilleure organisation et facilite la maintenance du code à mesure que le projet grandit.
