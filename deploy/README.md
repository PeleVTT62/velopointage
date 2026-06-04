# Dossiers de deploiement

- `deploy/dev` : mode developpement (reload, code monte en volume)
- `deploy/prod` : mode production multi-route (stable, sans reload)
- `deploy/github` : installation minimale pour une nouvelle route

## Commandes rapides

### Dev

```bash
docker compose -f deploy/dev/docker-compose.yml up -d --build
```

### Prod multi-route

```bash
cp deploy/prod/.env.example .env.multi-route
docker compose --env-file .env.multi-route -f deploy/prod/docker-compose.yml up -d --build
```

Checklist production:

- `deploy/prod/CHECKLIST_PRODUCTION.md`

### GitHub minimal (1 route)

```bash
./deploy/github/install.sh
```
