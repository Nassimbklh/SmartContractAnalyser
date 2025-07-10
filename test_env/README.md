# Test Environment

Ce dossier contient des scripts de test automatisés pour vérifier le bon fonctionnement de l'application SmartContractAnalyser.

## Scripts disponibles

### 1. Test de l'environnement

Le script `test_environment.py` vérifie que tous les conteneurs Docker sont en cours d'exécution et que les services sont accessibles.

**Utilisation :**
```bash
python3 test_environment.py
```

**Ce que le script vérifie :**
- Si Docker est en cours d'exécution
- Si tous les conteneurs Docker sont actifs
- Si les services (Backend, Frontend, PostgreSQL, PGAdmin, Ganache) sont accessibles
- Si les points d'accès HTTP de base fonctionnent

### 2. Test de l'API Backend

Le script `test_backend_api.py` vérifie que les points d'accès de l'API backend répondent correctement.

**Utilisation :**
```bash
python3 test_backend_api.py
```

**Ce que le script vérifie :**
- Si le point d'accès CORS fonctionne
- Si les points d'accès d'authentification (register, login) sont accessibles
- Si les points d'accès protégés (analyze, history, feedback) renvoient bien une erreur 401 sans authentification

### 3. Test de la base de données

Le script `test_database.py` vérifie la connexion à la base de données et la structure des tables.

**Utilisation :**
```bash
# Assurez-vous que la variable d'environnement DATABASE_URL est définie
export DATABASE_URL="postgresql://username:password@localhost:5432/dbname"
python3 test_database.py
```

**Ce que le script vérifie :**
- Si la connexion à la base de données fonctionne
- Si toutes les tables attendues existent (user, report, feedback, analysis_status)
- Si toutes les colonnes attendues existent dans chaque table

### 4. Test du Frontend

Le script `test_frontend.py` vérifie que le frontend est accessible et que la page principale se charge correctement.

**Utilisation :**
```bash
python3 test_frontend.py
```

**Ce que le script vérifie :**
- Si le frontend est accessible à l'URL http://localhost:4456
- Si la réponse contient les éléments HTML de base
- Si la réponse contient l'élément racine React et les balises de script

## Exécution de tous les tests

Pour exécuter tous les tests en une seule commande, vous pouvez utiliser le script shell suivant :

```bash
#!/bin/bash

echo "Exécution des tests d'environnement..."
python3 test_environment.py

echo -e "\nExécution des tests d'API backend..."
python3 test_backend_api.py

echo -e "\nExécution des tests de base de données..."
# Assurez-vous que DATABASE_URL est défini dans votre environnement
python3 test_database.py

echo -e "\nExécution des tests frontend..."
python3 test_frontend.py
```

## Intégration avec GitHub Actions

Ces tests peuvent être facilement intégrés dans un workflow GitHub Actions. Voici un exemple de configuration :

```yaml
name: Tests automatisés

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install requests sqlalchemy
    
    - name: Start environment
      run: |
        docker-compose up -d
        sleep 30  # Attendre que les services démarrent
    
    - name: Run environment tests
      run: python test_env/test_environment.py
    
    - name: Run backend API tests
      run: python test_env/test_backend_api.py
    
    - name: Run database tests
      run: |
        export DATABASE_URL=${{ secrets.DATABASE_URL }}
        python test_env/test_database.py
    
    - name: Run frontend tests
      run: python test_env/test_frontend.py
```

## Dépannage

Si les tests échouent, voici quelques étapes de dépannage :

1. Vérifiez que tous les conteneurs Docker sont en cours d'exécution avec `docker ps`
2. Vérifiez les journaux des conteneurs avec `docker logs <container_name>`
3. Assurez-vous que les variables d'environnement nécessaires sont définies
4. Vérifiez que les ports requis sont disponibles et non bloqués par un pare-feu