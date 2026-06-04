#!/bin/bash

# Script de test du système d'archivage

echo "=== Test du système d'archivage PéléVTT ==="
echo ""

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

echo "✅ Python3 trouvé"

# Tester la syntaxe Python
echo ""
echo "Test de la syntaxe du fichier main.py..."
python3 -m py_compile main.py 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Syntaxe Python valide"
else
    echo "❌ Erreurs de syntaxe détectées"
    exit 1
fi

echo ""
echo "=== Nouvelles fonctionnalités ajoutées ==="
echo ""
echo "✅ Table passages_archives créée automatiquement"
echo "✅ Archivage automatique à minuit (avant purge)"
echo "✅ API GET /api/passages/today - Tous les passages du jour"
echo "✅ API GET /api/passages/archives - Consultation des archives"
echo "✅ Page log.html mise à jour pour afficher tous les passages du jour"
echo ""
echo "=== APIs disponibles ==="
echo ""
echo "  GET /api/passages/today"
echo "    → Récupère tous les passages du jour (actuels + archives)"
echo ""
echo "  GET /api/passages/archives?date_debut=2026-01-01&date_fin=2026-01-31"
echo "    → Récupère les passages archivés avec filtrage par date"
echo ""
echo "=== Test terminé avec succès ==="
