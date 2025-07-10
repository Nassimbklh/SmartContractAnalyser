#!/usr/bin/env python3
"""
Script simple pour tester les principaux points d'accès de l'API backend sans authentification.
"""

import requests
import sys

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

def test_endpoint(url, expected_status=200, method="GET", data=None):
    try:
        if method == "GET":
            response = requests.get(url)
        else:
            response = requests.post(url, json=data)

        if response.status_code == expected_status:
            print_success(f"{method} {url} → {response.status_code} OK")
            return True
        else:
            print_error(f"{method} {url} → Statut inattendu: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"{method} {url} → Erreur: {str(e)}")
        return False

def main():
    print_info("Démarrage des tests rapides de l'API backend...")

    base_url = "http://localhost:4455"
    all_ok = True

    # Points d'accès principaux
    all_ok &= test_endpoint(f"{base_url}/cors-test")
    all_ok &= test_endpoint(f"{base_url}/analyze", expected_status=401, method="POST")
    all_ok &= test_endpoint(f"{base_url}/history", expected_status=401)
    all_ok &= test_endpoint(f"{base_url}/feedback", expected_status=401, method="POST")

    print("\n" + "="*50)
    print_info("Résumé des tests API backend:")
    print("="*50)

    if all_ok:
        print_success("Tous les points d'accès principaux répondent comme attendu ✅")
    else:
        print_error("Certains points d'accès ont échoué ❌")
        sys.exit(1)

if __name__ == "__main__":
    main()