# Velopointage - Système de pointage pour cyclistes

## À propos

Application web pour le suivi en temps réel des équipes de cyclistes lors d'événements (type pèlerinage VTT).

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
✅ Authentification simple pour opérations sensibles
✅ Responsive mobile
✅ **Deux applications PWA installables** (organisateurs + animateurs)
✅ **Mises à jour automatiques** du cache

📱 **Voir [GUIDE_INSTALLATION.md](GUIDE_INSTALLATION.md) pour installer les applications sur mobile**

## Démarrage rapide

Voir aussi le sommaire des modes de déploiement: `deploy/README.md`.

### Avec Docker Compose (recommandé)

```bash
cp .env.example .env
# Éditer .env avec votre ADMIN_KEY
docker-compose up -d
```

Puis accédez à `http://localhost:62000`

### Mode développement (reload à chaud)

Pour développer sans rebuild à chaque modification:

```bash
docker compose -f deploy/dev/docker-compose.yml up -d --build
```

Ce mode monte le code en volume et active `UVICORN_RELOAD=1`.

### Mode multi-route (instances dediees)

Pour executer plusieurs routes en parallele avec isolation des donnees:

```bash
cp deploy/prod/.env.example .env.multi-route
docker compose --env-file .env.multi-route -f deploy/prod/docker-compose.yml up -d --build
```

Documentation detaillee: `deploy/prod/README.md`

### Mode GitHub minimal (1 route, defaults)

Pour permettre à une autre route d'installer rapidement avec configuration minimale:

```bash
cp deploy/github/.env.example .env.github-minimal
mkdir -p instances/default/data instances/default/gpx
docker compose --env-file .env.github-minimal -f deploy/github/docker-compose.yml up -d --build
```

Guide complet: `deploy/github/README.md`

### Sans Docker

```bash
pip install -r requirements.txt
export ADMIN_KEY="votreClé"
export ALLOWED_ORIGINS="http://localhost:62000"
uvicorn main:app --host 0.0.0.0 --port 62000
```

## Configuration de sécurité

**IMPORTANT** : Avant production

1. Changer `ADMIN_KEY` dans `.env`
2. Configurer `ALLOWED_ORIGINS` (voir [deploy/prod/README.md](deploy/prod/README.md))
3. Utiliser HTTPS via reverse proxy

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

## Développement

### Installer dépendances
```bash
pip install -r requirements.txt
```

### Lancer en dev (avec reload)
```bash
export REDIS_ENABLED=false
uvicorn main:app --reload
```

### Tests
```bash
# WebSocket test
python -m pytest static/test-ws.html
```

## Production

Voir [deploy/prod/README.md](deploy/prod/README.md) et [deploy/dev/SYNOLOGY.md](deploy/dev/SYNOLOGY.md) pour :
- Reverse proxy HTTPS
- Gestion Redis
- Backups
- Monitoring

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

1. **Application Organisateurs** (`/static/index.html`) - Interface complète
2. **Application Animateurs** (`/static/anim.html`) - Interface simplifiée

Les deux applications peuvent être installées séparément sur iOS/Android et partagent le même système de mise à jour.

### 📚 Documentation complète

- 📱 **[QUELLE_APP.md](QUELLE_APP.md)** - Quelle application installer selon votre rôle ?
- 🚀 **[GUIDE_INSTALLATION.md](GUIDE_INSTALLATION.md)** - Guide rapide d'installation mobile
- 📖 **[INSTALL_PWA.md](INSTALL_PWA.md)** - Documentation détaillée des deux applications
- 🔄 **[UPDATE_PROCESS.md](UPDATE_PROCESS.md)** - Processus de mise à jour (pour admins)
- 🔧 **[TECHNICAL_PWA.md](TECHNICAL_PWA.md)** - Architecture technique (pour devs)

### Déploiement

**Avant chaque déploiement**, exécutez :

```bash
python3 bump_version.py
```

Cela incrémente automatiquement la version du cache et force la mise à jour sur **toutes les applications installées**. Les utilisateurs verront "Nouvelle version disponible" et l'application se rechargera automatiquement après 3 secondes.

## Problèmes connus

- **Redis non disponible** : App fonctionne en fallback mémoire
- **Nominatim lent** : Appels réseau à chaque passage

## Licence

À définir

## Contact/Support

Voir issues GitHub ou documentation locale.
