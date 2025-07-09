#!/bin/bash

# Détecter la branche git actuelle
branche=$(git rev-parse --abbrev-ref HEAD)

# Vérifier si le fichier .env existe
if [ ! -f .env ]; then
  echo "Erreur : le fichier .env est introuvable. Veuillez en créer un avec les variables d'environnement nécessaires."
  exit 1
fi

# Charger les variables d'environnement
export $(grep -v '^#' .env | xargs)

# Vérifier Docker
if ! command -v docker &> /dev/null; then
  echo "Erreur : Docker n'est pas installé. Veuillez l'installer et réessayer."
  exit 1
fi

if ! command -v docker compose &> /dev/null; then
  echo "Erreur : Docker Compose n'est pas installé. Veuillez l'installer et réessayer."
  exit 1
fi

# Construire et démarrer les conteneurs
echo "Construction et démarrage des conteneurs sur la branche : $branche"
docker compose down
docker compose up --build -d

echo "Patientez, les conteneurs démarrent..."
sleep 5

nb_running=$(docker compose ps -q | wc -l)
if [ "$nb_running" -lt 5 ]; then
  echo "Erreur : tous les conteneurs ne sont pas démarrés. Veuillez vérifier les logs avec 'docker-compose logs'."
  exit 1
fi

echo ""
echo "✅ Tous les conteneurs sont démarrés sur la branche : $branche"
echo ""

# Affichage selon la branche
if [ "$branche" = "main" ]; then
  echo "🌐 Frontend : https://www.sca.ovh"
  echo "🔌 Backend : https://www.sca.ovh/api"
  echo "🗄️ pgAdmin : https://pgadmin.sca.ovh"
else
  echo "✅ Vous êtes sur la branche '$branche', voici les informations pour la base de données :"
  echo ""
  echo "🌐 Frontend : http://localhost:4456"
  echo "🔌 Backend : http://localhost:4455"
  echo "🗄️ pgAdmin : http://localhost:4457"
  echo "   - Email : admin@admin.com"
  echo "   - Mot de passe : admin"
  echo "   Connexion BDD :"
  echo "   - Host      : $POSTGRES_HOST"
  echo "   - Port      : 5432"
  echo "   - Base      : $POSTGRES_DB"
  echo "   - Utilisateur : $POSTGRES_USER"
  echo "   - Mot de passe : $POSTGRES_PASSWORD"
  echo ""
fi

echo "📝 Pour consulter les logs :"
echo "   docker-compose logs"
echo ""
echo "🛑 Pour arrêter les conteneurs :"
echo "   docker-compose down"
echo ""