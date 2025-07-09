#!/usr/bin/env python3
"""
Script simple pour vérifier que le frontend est accessible et contient les éléments clés.
"""

import requests
import sys
import re

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
    print_info("Démarrage du test du frontend...")

    url = "http://localhost:4456"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print_success(f"Frontend accessible ({url})")
        else:
            print_error(f"Frontend retour statut inattendu: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print_error(f"Erreur d'accès au frontend: {str(e)}")
        sys.exit(1)

    content = response.text

    if '<!DOCTYPE html>' in content:
        print_success("Le DOCTYPE est présent ✅")
    else:
        print_error("DOCTYPE manquant ❌")
        sys.exit(1)

    if 'id="root"' in content:
        print_success("L'élément racine React est présent ✅")
    else:
        print_error("Élément racine React manquant ❌")
        sys.exit(1)

    print_success("Test frontend terminé avec succès ✅")

if __name__ == "__main__":
    main()