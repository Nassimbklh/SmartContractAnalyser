#!/usr/bin/env python3
"""
Script simple pour vérifier que les conteneurs Docker sont en cours d'exécution et rappeler les ports.
"""

import subprocess
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

services = {
    "Backend": 4455,
    "Frontend": 4456,
    "PostgreSQL": 5432,
    "PGAdmin": 4457,
    "Ganache": 8545
}

def check_docker():
    """Vérifie si Docker tourne et que des conteneurs sont actifs."""
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, check=True, text=True)
        if "Up" in result.stdout:
            print_success("Tous les conteneurs Docker semblent démarrés.")
            return True
        else:
            print_error("Aucun conteneur actif trouvé. Lance d'abord docker compose.")
            return False
    except subprocess.CalledProcessError:
        print_error("Erreur lors de la vérification de Docker. Est-il bien installé et démarré ?")
        return False

def main():
    print_info("Vérification basique de l'environnement Docker...")
    ok = check_docker()
    if not ok:
        sys.exit(1)

    print_info("Rappel des ports attendus (à tester manuellement si besoin) :")
    for name, port in services.items():
        print(f" - {name}: localhost:{port}")

    print_success("Vérification terminée.")

if __name__ == "__main__":
    main()