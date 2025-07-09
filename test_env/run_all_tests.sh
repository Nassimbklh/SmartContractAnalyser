#!/bin/bash
# Script pour exécuter tous les tests dans test_env

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Fonction pour afficher une section
print_section() {
    echo -e "\n${YELLOW}=======================================${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}=======================================${NC}\n"
}

# Fonction pour exécuter un test
run_test() {
    local script=$1
    local name=$2

    print_section "🔎 Lancement du test: $name"
    python3 "$script"
    local code=$?

    if [ $code -eq 0 ]; then
        echo -e "${GREEN}✅ $name OK${NC}"
    else
        echo -e "${RED}❌ $name échoué (code $code)${NC}"
        all_ok=false
    fi
}

# Initialiser le statut global
all_ok=true

# Aller dans le dossier du script
cd "$(dirname "$0")" || { echo "Impossible d'accéder au dossier test_env"; exit 1; }

echo -e "${GREEN}🚀 Démarrage de tous les tests...${NC}"

# Tests
run_test "test_environment.py" "Test Environnement"
run_test "test_backend_api.py" "Test API Backend"

if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⚠️ DATABASE_URL non défini, test BDD ignoré.${NC}"
    echo -e "${YELLOW}💡 Pour activer : export DATABASE_URL=\"postgresql://user:password@host:port/db\"${NC}"
else
    run_test "test_database.py" "Test Base de Données"
fi

run_test "test_frontend.py" "Test Frontend"

# Résultat final
print_section "Résumé final"

if [ "$all_ok" = true ]; then
    echo -e "${GREEN}🎉 Tous les tests sont passés avec succès !${NC}"
    exit 0
else
    echo -e "${RED}💥 Certains tests ont échoué. Vérifie les logs ci-dessus.${NC}"
    exit 1
fi