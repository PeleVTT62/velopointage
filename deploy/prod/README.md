# Deploiement Multi-Route (instances dediees)

Ce mode lance une instance independante par route pour isoler les pannes et les donnees.

## Fichiers fournis

- `deploy/prod/docker-compose.yml`: stack de reference avec deux routes.
- `deploy/prod/.env.example`: variables d'environnement a copier en `.env.multi-route`.

## Etapes

1. Copier les variables:
   - `cp deploy/prod/.env.example .env.multi-route`
2. Renseigner les secrets et origines CORS.
3. Lancer:
   - `docker compose --env-file .env.multi-route -f deploy/prod/docker-compose.yml up -d --build`
4. Verifier les deux instances:
   - Route 62: `http://localhost:62000`
   - Route 11: `http://localhost:62010`

## Isolation par route

Chaque route dispose de:

- son volume donnees (`/app/data`)
- son volume GPX (`/app/static/gpx`)
- son canal Redis dedie (`passages:<route_slug>`)
- ses secrets propres (admin, session, mot de passe config)

## Ajout d'une nouvelle route

1. Dupliquer un service `app_*` dans `deploy/prod/docker-compose.yml`.
2. Changer:
   - `ROUTE_NAME`
   - `ROUTE_SLUG`
   - mapping de port externe
   - volumes dedies
   - variables de secrets dediees
3. Ajouter les nouvelles variables dans `.env.multi-route`.
4. Redeployer la stack.

## Stabilite recommandee

- Garder des `healthcheck` actifs sur chaque route.
- Mettre des limites CPU/RAM par service selon le contexte serveur.
- Sauvegarder les volumes de donnees route par route.
- Migrer vers PostgreSQL par route si vous ajoutez de la replication applicative.

Checklist operationnelle recommandee: `deploy/prod/CHECKLIST_PRODUCTION.md`.

## Exploitation Synology

Les commandes ci-dessous utilisent le binaire Docker Synology:

- Supervision:
   - `sudo /usr/local/bin/docker compose --env-file .env.multi-route -f deploy/prod/docker-compose.yml ps`
- Logs Route 11:
   - `sudo /usr/local/bin/docker compose --env-file .env.multi-route -f deploy/prod/docker-compose.yml logs -f app_route11`
- Logs Route 62:
   - `sudo /usr/local/bin/docker compose --env-file .env.multi-route -f deploy/prod/docker-compose.yml logs -f app_route62`
- Redemarrage Route 11:
   - `sudo /usr/local/bin/docker compose --env-file .env.multi-route -f deploy/prod/docker-compose.yml restart app_route11`
- Redemarrage Route 62:
   - `sudo /usr/local/bin/docker compose --env-file .env.multi-route -f deploy/prod/docker-compose.yml restart app_route62`
