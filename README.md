# Velopointage - Système de pointage pour PéléVTT

## À propos

Application web pour le suivi en temps réel des équipes de cyclistes lors du PéléVTT.

- **Backend** : FastAPI (Python)
- **Frontend** : HTML5/JavaScript vanilla
- **Temps réel** : WebSocket + Redis
- **Cartes** : Leaflet.js
- **Déploiement** : Docker (Synology compatible)

## Fonctionnalités

✅ Enregistrement des passages GPS
✅ Affichage en temps réel sur carte
✅ Gestion d'équipes avec couleurs
✅ Import de traces GPX
✅ Calcul distance d'après itinéraire
✅ Reverse geocoding (ville au point de passage)
✅ **Deux applications PWA installables** (TTV + anim)
✅ **Mises à jour automatiques**

📱 **Voir [GUIDE_INSTALLATION.md](GUIDE_INSTALLATION.md) pour installer les applications sur mobile**

## Démarrage rapide

Voir aussi le sommaire des modes de déploiement: `deploy/README.md`.


### Mode Installation facile (recommandé)

Installation automatisée par script : 
Guide complet: `deploy/github/README.md`


### Avec Docker Compose
```bash
cp deploy/github/.env.example .env.github-minimal
mkdir -p instances/default/data instances/default/gpx
docker compose --env-file .env.github-minimal -f deploy/github/docker-compose.yml up -d --build
```





## API

### Routes publiques (lectures)

- `GET /` - Page accueil
- `GET /api/passages` - Liste des passages
- `GET /api/summary` - Résumé équipes + derniers passages
- `GET /api/equipes` - Liste équipes
- `GET /api/gpx_files` - Fichiers GPX disponibles
- `WS /ws/passages` - WebSocket temps réel

### Routes admin (nécessitent `X-Admin-Key`)

- `POST /api/equipes` - Mise à jour équipes
- `POST /api/passage` - Enregistrer un passage
- `POST /api/set_active_gpx` - Activer une trace GPX
- `POST /api/upload_gpx` - Importer un fichier GPX
- `POST /api/reset_passages` - Vider la base passages
- `DELETE /api/gpx?filename=...` - Supprimer un GPX
- `DELETE /api/passage/{id}` - Supprimer un passage
- `POST /api/equipe/{nom}/etat` - Changer état équipe

## Structures de données

### Passage
```json
{
  "id": 1,
  "equipe": "Saint Pierre",
  "latitude": 50.5,
  "longitude": 2.1,
  "timestamp": "2025-01-09T14:30:00Z",
  "observateur": "Observer1",
  "ville": "Bruay-la-Buissière"
}
```

### Équipe
```json
{
  "nom": "Saint Pierre",
  "couleur": "#FF0000",
  "etat": "roule"  // ou: temps spi, pause, arrivée, non partie
}
```

## Variables d'environnement

| Variable | Défaut | Description |
|----------|--------|-------------|
| `APP_PORT` | 62000 | Port de l'application |
| `REDIS_URL` | redis://localhost:6379 | URL Redis (optionnel) |
| `REDIS_ENABLED` | true | Activer Redis |
| `ROUTE_NAME` | Route 62 | Nom metier de la route servie par l'instance |
| `ROUTE_SLUG` | route62 | Identifiant technique de la route |
| `REDIS_CHANNEL` | passages:route62 | Canal Redis dedie a l'instance |
| `ADMIN_KEY` | changeme-admin-key-in-production | Clé d'authentification |
| `ALLOWED_ORIGINS` | http://localhost:62000 | CORS origins |

## Fichiers importants

```
.
├── main.py                  # API FastAPI
├── Dockerfile               # Image Docker
├── .env.example            # Configuration exemple
├── deploy/                  # Configs deploiement (dev/prod/github)
│   ├── README.md
│   ├── dev/
│   ├── prod/
│   └── github/
├── requirements.txt        # Dépendances Python
└── static/
    ├── index.html          # Accueil
    ├── carte.html          # Affichage carte
     ├── configuration.html  # Admin panel
     ├── anim.html           # Interface pointage
    └── gpx/               # Traces GPX
```

## Architecture

```
Client (mobile/desktop)
         ↓
    (HTTPS/Reverse proxy)
         ↓
    FastAPI (uvicorn)
    ├─→ SQLite (passages, équipes)
    ├─→ Redis (pub/sub temps réel)
    └─→ Static files (HTML/JS/CSS)
         ↓
    Nominatim/OpenStreetMap (reverse geocoding)
```

## 🔄 Mises à jour PWA

L'application fonctionne en mode PWA (Progressive Web App) avec **deux interfaces distinctes** :

1. **Application TTV** (`/static/index.html`) - Interface complète
2. **Application anim** (`/static/anim.html`) - Interface simplifiée

Les deux applications peuvent être installées séparément sur iOS/Android et partagent le même système de mise à jour.