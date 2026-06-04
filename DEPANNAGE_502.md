# 🔧 Dépannage - Erreurs 502 Bad Gateway

## Symptômes

```
GET https://api.pelevtt.cloud/api/equipes 502 (Bad Gateway)
GET https://api.pelevtt.cloud/api/passages/today 502 (Bad Gateway)
Erreur: SyntaxError: Unexpected token '<', "<!DOCTYPE "... is not valid JSON
```

## Causes possibles

### 1. Le serveur backend n'est pas démarré
**Vérification** :
```bash
# Vérifier si le conteneur tourne
docker ps | grep velopointage

# Vérifier les logs
docker-compose logs -f
```

**Solution** :
```bash
# Démarrer le serveur
docker-compose up -d

# Ou en mode développement
python3 main.py
```

### 2. Configuration reverse proxy incorrecte (Nginx/Traefik)
**Vérification** :
```bash
# Tester directement l'API backend
curl http://localhost:62000/api/equipes

# Tester via le reverse proxy
curl https://api.pelevtt.cloud/api/equipes
```

**Solution** : Vérifier la configuration du reverse proxy

#### Exemple Nginx
```nginx
location /api/ {
    proxy_pass http://localhost:62000/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /static/ {
    proxy_pass http://localhost:62000/static/;
}
```

### 3. Port du backend inaccessible
**Vérification** :
```bash
# Vérifier que le port 62000 est ouvert
netstat -tlnp | grep 62000

# Ou avec ss
ss -tlnp | grep 62000

# Tester la connexion
curl http://localhost:62000/api/equipes
```

**Solution** : Vérifier le firewall et les règles de routage

### 4. Base de données corrompue ou verrouillée
**Vérification** :
```bash
# Vérifier l'intégrité de la base
sqlite3 data/db.sqlite "PRAGMA integrity_check;"

# Vérifier les permissions
ls -la data/db.sqlite
```

**Solution** :
```bash
# Corriger les permissions
chmod 644 data/db.sqlite
chown www-data:www-data data/db.sqlite

# Ou dans Docker
docker-compose exec app chown app:app /app/data/db.sqlite
```

### 5. Erreur de démarrage de l'application
**Vérification** :
```bash
# Regarder les logs au démarrage
docker-compose logs | head -50

# Ou
python3 main.py
```

**Erreurs courantes** :
- Module Python manquant
- Erreur de syntaxe Python
- Port déjà utilisé
- Permissions insuffisantes

## Solutions par ordre de priorité

### ✅ Solution 1 : Vérifier le serveur
```bash
# 1. Vérifier que le serveur tourne
docker-compose ps

# 2. Si arrêté, redémarrer
docker-compose restart

# 3. Vérifier les logs
docker-compose logs -f | tail -20
```

### ✅ Solution 2 : Tester l'API directement
```bash
# Tester en local (bypass le reverse proxy)
curl http://localhost:62000/api/equipes

# Si ça marche, le problème est le reverse proxy
# Si ça ne marche pas, le problème est le backend
```

### ✅ Solution 3 : Redémarrer complètement
```bash
# Arrêter tout
docker-compose down

# Nettoyer les containers orphelins
docker-compose down --remove-orphans

# Redémarrer
docker-compose up -d

# Suivre les logs
docker-compose logs -f
```

### ✅ Solution 4 : Vérifier la configuration
```bash
# Vérifier les variables d'environnement
docker-compose config

# Vérifier le port exposé
docker-compose ps
```

### ✅ Solution 5 : Tester avec curl
```bash
# Test basique
curl -v http://localhost:62000/api/equipes

# Test avec headers
curl -v -H "Accept: application/json" http://localhost:62000/api/equipes

# Test via le reverse proxy
curl -v https://api.pelevtt.cloud/api/equipes
```

## Checklist de diagnostic

- [ ] Le conteneur Docker est démarré
- [ ] Les logs ne montrent pas d'erreur
- [ ] Le port 62000 est accessible en local
- [ ] L'API répond en local (`curl http://localhost:62000/api/equipes`)
- [ ] La base de données existe et est accessible
- [ ] Les permissions sont correctes
- [ ] Le reverse proxy est configuré correctement
- [ ] Le DNS pointe vers le bon serveur
- [ ] Les certificats SSL sont valides
- [ ] Aucun firewall ne bloque les connexions

## Erreurs spécifiques

### "Unexpected token '<', "<!DOCTYPE "... is not valid JSON"

**Signification** : Le serveur retourne du HTML au lieu de JSON

**Cause** : Le reverse proxy retourne une page d'erreur HTML

**Solution** :
1. Vérifier que le backend répond correctement
2. Vérifier la configuration du reverse proxy
3. Regarder les logs du reverse proxy

### "502 Bad Gateway"

**Signification** : Le reverse proxy ne peut pas joindre le backend

**Causes possibles** :
- Backend arrêté
- Port incorrect dans la config du reverse proxy
- Timeout trop court
- Backend en cours de redémarrage

**Solution** :
```bash
# 1. Vérifier le backend
docker-compose ps

# 2. Tester directement
curl http://localhost:62000/api/equipes

# 3. Vérifier la config du reverse proxy
nginx -t
# ou
traefik config
```

## Configuration recommandée

### Docker Compose
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "62000:62000"
    volumes:
      - ./data:/app/data
    environment:
      - APP_PORT=62000
      - REDIS_ENABLED=false
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:62000/api/equipes"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Nginx
```nginx
upstream backend {
    server localhost:62000;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name api.pelevtt.cloud;

    # SSL config...

    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
    }
}
```

## Monitoring

### Script de surveillance
```bash
#!/bin/bash
# monitor_api.sh

API_URL="https://api.pelevtt.cloud/api/equipes"
LOCAL_URL="http://localhost:62000/api/equipes"

# Test local
if curl -s -f "$LOCAL_URL" > /dev/null; then
    echo "✅ Backend OK"
else
    echo "❌ Backend DOWN"
    docker-compose restart
fi

# Test via reverse proxy
if curl -s -f "$API_URL" > /dev/null; then
    echo "✅ Reverse proxy OK"
else
    echo "❌ Reverse proxy DOWN"
    systemctl restart nginx
fi
```

### Ajouter au crontab
```bash
*/5 * * * * /path/to/monitor_api.sh >> /var/log/pelevtt_monitor.log 2>&1
```

## Logs utiles

### Backend
```bash
# Logs Docker
docker-compose logs -f --tail=100

# Logs Python
tail -f logs/app.log
```

### Reverse Proxy
```bash
# Nginx
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# Traefik
docker logs traefik -f
```

### Système
```bash
# Journal système
journalctl -u docker -f

# Logs kernel
dmesg | tail
```

## Contact support

Si le problème persiste après avoir suivi ce guide :

1. Collecter les informations :
   ```bash
   # Statut des containers
   docker-compose ps > debug_info.txt
   
   # Logs
   docker-compose logs --tail=200 >> debug_info.txt
   
   # Test API
   curl -v http://localhost:62000/api/equipes >> debug_info.txt 2>&1
   ```

2. Vérifier la documentation :
   - `ARCHIVAGE.md`
   - `ADMIN_ARCHIVAGE.md`
   - `GUIDE_ARCHIVAGE.md`

---

**En cas d'urgence : redémarrer le système complet**
```bash
docker-compose down && docker-compose up -d
```
