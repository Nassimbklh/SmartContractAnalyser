#!/usr/bin/env python3
"""
Script simple pour vérifier la connexion à la base et la présence des tables importantes.
"""

import os
import sys
from sqlalchemy import create_engine, inspect
# Importer les modules nécessaires


# Couleurs terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_info(msg):
    print(f"{YELLOW}ℹ️ {msg}{RESET}")

def main():
    print_info("Démarrage du test de la base de données...")

    # URL base
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print_error("La variable d'environnement DATABASE_URL n'est pas définie.")
        sys.exit(1)

    try:
        engine = create_engine(database_url)
        conn = engine.connect()
        conn.close()
        print_success("Connexion à la base de données réussie.")
    except Exception as e:
        print_error(f"Échec de la connexion : {str(e)}")
        sys.exit(1)

    # Tables à vérifier
    expected_tables = ["user", "report", "feedback", "analysis_status"]

    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        all_ok = True
        for table in expected_tables:
            if table in existing_tables:
                print_success(f"Table '{table}' présente.")
            else:
                print_error(f"Table '{table}' manquante.")
                all_ok = False

        if all_ok:
            print_success("Toutes les tables requises sont présentes.")
        else:
            print_error("Certaines tables manquent.")
            sys.exit(1)

    except Exception as e:
        print_error(f"Erreur lors de la vérification des tables : {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()