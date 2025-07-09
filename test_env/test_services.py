#!/usr/bin/env python3
import socket, sys

# Couleurs
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

services = [
    ("Backend", "localhost", 4455),
    ("Frontend", "localhost", 4456),
    ("PostgreSQL", "localhost", 5432),
]

def check(host, port, name):
    try:
        with socket.create_connection((host, port), timeout=5):
            print(f"{GREEN}✅ {name} UP sur {host}:{port}{RESET}")
            return True
    except Exception as e:
        print(f"{RED}❌ {name} KO sur {host}:{port} ({e}){RESET}")
        return False

def main():
    all_ok = True
    for name, host, port in services:
        if not check(host, port, name):
            all_ok = False
    if all_ok:
        print(f"{GREEN}✅ Tous les services principaux sont UP{RESET}")
        sys.exit(0)
    else:
        print(f"{RED}❌ Un ou plusieurs services sont DOWN{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()