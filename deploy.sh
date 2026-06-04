#!/bin/bash
# Script de déploiement automatique avec mise à jour de version

set -e  # Arrêter en cas d'erreur

echo "🚀 Déploiement de Velopointage avec mise à jour PWA"
echo ""

# 0. Vérifier la configuration PWA
echo "🔍 Vérification de la configuration PWA..."
python3 verify_pwa.py
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ La vérification PWA a échoué. Corrigez les erreurs avant de continuer."
    exit 1
fi

# 1. Incrémenter la version
echo ""
echo "📦 Incrémentation de la version..."
python3 bump_version.py

# 2. Vérifier les changements
echo ""
echo "📝 Changements de version :"
git diff static/sw.js | grep "CACHE_VERSION"

# 3. Demander confirmation
echo ""
read -p "Voulez-vous continuer le déploiement ? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "❌ Déploiement annulé"
    git checkout static/sw.js  # Annuler les changements
    exit 1
fi

# 4. Commit
echo ""
echo "💾 Commit des changements..."
VERSION=$(grep "CACHE_VERSION = " static/sw.js | sed "s/.*'\(.*\)'.*/\1/")
git add static/sw.js
git commit -m "chore: bump PWA version to $VERSION"

# 5. Push
echo ""
echo "📤 Push vers le dépôt..."
git push

# 6. Rebuild Docker (si stack prod presente)
if [ -f "deploy/prod/docker-compose.yml" ]; then
    echo ""
    echo "🐳 Rebuild Docker..."
    docker compose --env-file .env.multi-route -f deploy/prod/docker-compose.yml up -d --build --remove-orphans
fi

echo ""
echo "✅ Déploiement terminé !"
echo ""
echo "📱 Les utilisateurs verront la mise à jour automatiquement :"
echo "   - Au prochain lancement de l'app"
echo "   - Ou après 1h si l'app est déjà ouverte"
echo "   - Rechargement automatique après 3 secondes"
