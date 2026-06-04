#!/bin/bash
# api-test-examples.sh - Exemples d'appels API Velopointage

# Configuration
API_URL="http://localhost:62000"
ADMIN_KEY="test-key-12345"  # À changer en production

echo "🧪 Velopointage API Test Examples"
echo "==================================="
echo ""
echo "Configuration:"
echo "  API: $API_URL"
echo "  Admin Key: $ADMIN_KEY"
echo ""
echo "Note: Remplacer l'Admin Key par la vraie en production"
echo ""

# ─────────────────────────────────────────────────────────────────
# 📖 LECTURES PUBLIQUES (pas besoin d'authentification)
# ─────────────────────────────────────────────────────────────────

echo "1️⃣  GET - Récupérer tous les passages"
echo "───────────────────────────────────"
# curl -s "$API_URL/api/passages" | jq .

echo "2️⃣  GET - Récupérer le résumé des équipes"
echo "──────────────────────────────────────"
# curl -s "$API_URL/api/summary" | jq .

echo "3️⃣  GET - Récupérer la liste des équipes"
echo "─────────────────────────────────────"
# curl -s "$API_URL/api/equipes" | jq .

echo "4️⃣  GET - Récupérer les fichiers GPX disponibles"
echo "────────────────────────────────────────────"
# curl -s "$API_URL/api/gpx_files" | jq .

echo "5️⃣  WS - Se connecter en WebSocket"
echo "──────────────────────────────────"
# wscat -c "ws://localhost:62000/ws/passages"

echo ""
echo "─────────────────────────────────────────────────────────────────"
echo "🔐 ÉCRITURES PROTÉGÉES (nécessitent X-Admin-Key)"
echo "─────────────────────────────────────────────────────────────────"

echo "6️⃣  POST - Ajouter un nouveau passage"
echo "────────────────────────────────"
cat << 'EOF'
curl -s -X POST "$API_URL/api/passage" \
  -H "Content-Type: application/json" \
  -d '{
    "equipe": "Saint Pierre",
    "latitude": 50.5,
    "longitude": 2.1,
    "observateur": "Observateur1"
  }'
EOF
echo ""

echo "7️⃣  POST - Mettre à jour les équipes"
echo "──────────────────────────────────"
cat << 'EOF'
curl -s -X POST "$API_URL/api/equipes" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $ADMIN_KEY" \
  -d '{
    "equipes": [
      {"nom": "Saint Pierre", "couleur": "#FF0000", "etat": "roule"},
      {"nom": "Saint Paul", "couleur": "#0000FF", "etat": "pause"}
    ]
  }'
EOF
echo ""

echo "8️⃣  POST - Changer l'état d'une équipe"
echo "─────────────────────────────────────"
cat << 'EOF'
curl -s -X POST "$API_URL/api/equipe/Saint Pierre/etat" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $ADMIN_KEY" \
  -d '{"etat": "arrivée"}'
EOF
echo ""

echo "9️⃣  POST - Upload d'un fichier GPX"
echo "──────────────────────────────────"
cat << 'EOF'
curl -s -X POST "$API_URL/api/upload_gpx" \
  -H "X-Admin-Key: $ADMIN_KEY" \
  -F "file=@/chemin/vers/trace.gpx"
EOF
echo ""

echo "🔟 POST - Activer un fichier GPX"
echo "───────────────────────────────"
cat << 'EOF'
curl -s -X POST "$API_URL/api/set_active_gpx" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $ADMIN_KEY" \
  -d '{"filename": "trace.gpx"}'
EOF
echo ""

echo "1️⃣1️⃣  DELETE - Supprimer un passage"
echo "─────────────────────────────────"
cat << 'EOF'
curl -s -X DELETE "$API_URL/api/passage/123" \
  -H "X-Admin-Key: $ADMIN_KEY"
EOF
echo ""

echo "1️⃣2️⃣  DELETE - Supprimer un fichier GPX"
echo "──────────────────────────────────────"
cat << 'EOF'
curl -s -X DELETE "$API_URL/api/gpx?filename=trace.gpx" \
  -H "X-Admin-Key: $ADMIN_KEY"
EOF
echo ""

echo "1️⃣3️⃣  POST - Reset complet (vider passages & réinitialiser états)"
echo "─────────────────────────────────────────────────────────"
cat << 'EOF'
curl -s -X POST "$API_URL/api/reset_passages" \
  -H "X-Admin-Key: $ADMIN_KEY"
EOF
echo ""

# ─────────────────────────────────────────────────────────────────
# 🔍 TESTS RECOMMANDÉS
# ─────────────────────────────────────────────────────────────────

echo ""
echo "📋 Quick Test Script (décommenter pour exécuter)"
echo "───────────────────────────────────────────────"
cat << 'EOF'

# Tester une lecture
# curl -s "$API_URL/api/equipes" | jq .

# Tester une écriture avec authentification
# curl -s -X POST "$API_URL/api/reset_passages" \
#   -H "X-Admin-Key: $ADMIN_KEY" | jq .

# Tester WebSocket avec wscat
# npm install -g wscat
# wscat -c "ws://localhost:62000/ws/passages"

EOF

# ─────────────────────────────────────────────────────────────────
# 🚨 TROUBLESHOOTING
# ─────────────────────────────────────────────────────────────────

echo ""
echo "🚨 Troubleshooting"
echo "─────────────────"
echo ""
echo "❌ Error 403 - Forbidden"
echo "  → X-Admin-Key invalide ou manquant"
echo "  → Vérifier la valeur de ADMIN_KEY"
echo ""
echo "❌ Error 400 - Bad Request"
echo "  → JSON malformé ou champ manquant"
echo "  → Vérifier la syntaxe JSON"
echo ""
echo "❌ Impossible de se connecter"
echo "  → Vérifier que le serveur tourne: curl $API_URL/"
echo "  → Vérifier le port (62000 par défaut)"
echo ""
echo "❌ WebSocket refuse connexion"
echo "  → CORS non configuré correctement"
echo "  → Vérifier ALLOWED_ORIGINS en .env"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "✅ Pour exécuter les tests, enlever le '#' devant 'curl'"
echo "═══════════════════════════════════════════════════════════════"
