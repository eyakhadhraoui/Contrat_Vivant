#!/bin/sh
set -e

echo "🚀 [Backend] Démarrage de l'agent d'assurance..."

# Attente que MySQL soit prêt si MYSQL_HOST est configuré
if [ -n "$MYSQL_HOST" ] && [ "$MYSQL_HOST" != "localhost" ]; then
    echo "⏳ Attente de la disponibilité de MySQL sur ${MYSQL_HOST}:${MYSQL_PORT:-3306}..."
    max_retries=30
    counter=0
    until mysqladmin ping -h "$MYSQL_HOST" -P "${MYSQL_PORT:-3306}" -u "$MYSQL_USER" --password="$MYSQL_PASSWORD" --silent 2>/dev/null; do
        counter=$((counter + 1))
        if [ $counter -gt $max_retries ]; then
            echo "⚠️ Avertissement: MySQL n'a pas répondu à temps, poursuite du démarrage..."
            break
        fi
        sleep 2
    done
    echo "✅ MySQL est connecté et opérationnel !"
fi

# Lancement du serveur FastAPI avec Uvicorn
echo "🔥 Lancement du serveur Uvicorn sur le port 8000..."
exec uvicorn api.main_api:app --host 0.0.0.0 --port 8000
