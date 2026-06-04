# Configuration Hot-Reload sur Synology

## Déploiement avec hot-reload pour les tests

Le fichier `deploy/dev/docker-compose.yml` a ete configure pour monter le code source en volume, ce qui permet de **modifier le code sans reconstruire l'image Docker**.

### Étapes sur votre Synology

#### 1. Connexion SSH au Synology

```bash
ssh admin@votre-synology-ip
```

#### 2. Navigation vers le dossier du projet

```bash
cd /volume1/docker/velopointage  # Adaptez le chemin selon votre configuration
```

#### 3. Premier déploiement (build initial)

```bash
sudo /usr/local/bin/docker compose -f deploy/dev/docker-compose.yml build
sudo /usr/local/bin/docker compose -f deploy/dev/docker-compose.yml up -d
```

#### 4. Pour appliquer vos modifications (sans rebuild)

Après avoir modifié `main.py` ou des fichiers dans `static/` :

```bash
# Option 1 : Redémarrer juste le conteneur app (rapide, 2-3 secondes)
sudo /usr/local/bin/docker compose -f deploy/dev/docker-compose.yml restart app

# Option 2 : Le hot-reload détecte automatiquement les changements
# Attendez 1-2 secondes, uvicorn rechargera automatiquement
```

### Vérifier les logs pour voir le rechargement

```bash
sudo /usr/local/bin/docker compose -f deploy/dev/docker-compose.yml logs -f app
```

Vous verrez :
```
INFO:     Will watch for changes in these directories: ['/app']
INFO:     Uvicorn running on http://0.0.0.0:62000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Detected file change in '/app/main.py'
INFO:     Reloading...
```

### Synchronisation des fichiers

#### Option A : Éditer via File Station (interface web)

1. Ouvrez File Station sur DSM
2. Naviguez vers `/docker/velopointage`
3. Éditez `main.py` ou les fichiers dans `static/`
4. Sauvegardez → Le hot-reload se déclenche automatiquement

#### Option B : Éditer localement et synchroniser

**Avec VS Code + SSH Remote** (recommandé) :

1. Installez l'extension "Remote - SSH" dans VS Code
2. Connectez-vous à votre Synology
3. Ouvrez le dossier `/volume1/docker/velopointage`
4. Éditez les fichiers → Sauvegarde automatique → Hot-reload

**Avec rsync** :

```bash
# Depuis votre Mac
rsync -avz --exclude 'data' --exclude '__pycache__' \
  /Volumes/docker/velopointage/ \
  admin@votre-synology-ip:/volume1/docker/velopointage/
```

**Avec scp** :

```bash
# Copier main.py après modification
scp main.py admin@votre-synology-ip:/volume1/docker/velopointage/

# Copier un fichier HTML
scp static/configuration.html admin@votre-synology-ip:/volume1/docker/velopointage/static/
```

### Rebuild complet (seulement si vous modifiez requirements.txt)

```bash
sudo /usr/local/bin/docker compose -f deploy/dev/docker-compose.yml down
sudo /usr/local/bin/docker compose -f deploy/dev/docker-compose.yml build --no-cache
sudo /usr/local/bin/docker compose -f deploy/dev/docker-compose.yml up -d
```

### Commandes utiles

```bash
# Voir les conteneurs en cours
sudo /usr/local/bin/docker compose -f deploy/dev/docker-compose.yml ps

# Voir les logs en temps réel
sudo /usr/local/bin/docker compose -f deploy/dev/docker-compose.yml logs -f

# Redémarrer uniquement l'app (sans Redis)
sudo /usr/local/bin/docker compose -f deploy/dev/docker-compose.yml restart app

# Arrêter tout
sudo /usr/local/bin/docker compose -f deploy/dev/docker-compose.yml down

# Relancer apres modification de deploy/dev/docker-compose.yml
sudo /usr/local/bin/docker compose -f deploy/dev/docker-compose.yml up -d
```

### Fichiers montés en volume (modifiables sans rebuild)

- ✅ `main.py` → modification détectée automatiquement
- ✅ `wsgi.py` → modification détectée automatiquement  
- ✅ `static/*` → tous les fichiers HTML/CSS/JS
- ✅ `data/` → base de données et config
- ❌ `requirements.txt` → nécessite un rebuild

### Désactiver le hot-reload en production

Quand vous passez en production, éditez le [Dockerfile](Dockerfile) :

```dockerfile
# Remplacer cette ligne :
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "62000", "--reload"]

# Par :
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "62000", "--workers", "4"]
```

Puis rebuild :
```bash
sudo /usr/local/bin/docker compose -f deploy/dev/docker-compose.yml build --no-cache
sudo /usr/local/bin/docker compose -f deploy/dev/docker-compose.yml up -d
```

### Troubleshooting

**Le hot-reload ne fonctionne pas ?**

1. Vérifiez que les volumes sont bien montés :
   ```bash
   sudo /usr/local/bin/docker compose -f deploy/dev/docker-compose.yml exec app ls -la /app/
   ```

2. Vérifiez les logs :
   ```bash
   sudo /usr/local/bin/docker compose -f deploy/dev/docker-compose.yml logs app | grep -i reload
   ```

3. Permissions : si vous avez des erreurs de permissions, assurez-vous que les fichiers appartiennent à l'utilisateur Docker :
   ```bash
   sudo chown -R 1000:1000 /volume1/docker/velopointage
   ```

**Les modifications ne sont pas visibles ?**

- Videz le cache du navigateur (Ctrl+Shift+R)
- Vérifiez que vous modifiez bien les fichiers sur le Synology (pas en local)
- Attendez 1-2 secondes après la sauvegarde

**Le conteneur ne démarre pas après modification ?**

```bash
# Voir l'erreur exacte
sudo /usr/local/bin/docker compose -f deploy/dev/docker-compose.yml logs app

# Revenir à la version précédente via git (si configuré)
git checkout main.py

# Ou restaurer depuis un backup
```
