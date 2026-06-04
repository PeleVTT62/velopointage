# 🔧 Guide Administrateur - Système d'Archivage

## Vérifications rapides

### 1. Vérifier que la table existe
```bash
sqlite3 data/db.sqlite "SELECT name FROM sqlite_master WHERE type='table' AND name='passages_archives';"
```
✅ Résultat attendu : `passages_archives`

### 2. Statistiques complètes
```bash
sqlite3 data/db.sqlite < check_archives.sql
```

### 3. Test des APIs
```bash
# Test basique
curl http://localhost:62000/api/passages/today | jq 'length'

# Test complet
python3 test_api_archivage.py
```

## Commandes utiles

### Consulter les archives
```bash
# Compter les archives
sqlite3 data/db.sqlite "SELECT COUNT(*) FROM passages_archives;"

# Voir les dernières archives
sqlite3 data/db.sqlite "SELECT equipe, timestamp FROM passages_archives ORDER BY timestamp DESC LIMIT 10;"

# Statistiques par équipe
sqlite3 data/db.sqlite "SELECT equipe, COUNT(*) FROM passages_archives GROUP BY equipe;"
```

### Exporter les archives
```bash
# Export CSV
sqlite3 -header -csv data/db.sqlite "SELECT * FROM passages_archives;" > archives.csv

# Export JSON (via API)
curl "http://localhost:62000/api/passages/archives?limit=10000" > archives.json
```

### Sauvegarder la base
```bash
# Copie locale
cp data/db.sqlite backup/db_$(date +%Y%m%d).sqlite

# Avec Docker
docker cp velopointage:/app/data/db.sqlite ./backup_$(date +%Y%m%d).sqlite
```

## Surveillance du scheduler

### Vérifier les logs d'archivage
```bash
# Logs Docker
docker-compose logs | grep "Purge quotidienne"

# Logs directs
tail -f logs/app.log | grep "Purge quotidienne"
```

### Message attendu à minuit
```
[2026-01-20 00:00:00] Purge quotidienne : 247 passages archivés et supprimés.
```

## Maintenance

### Nettoyer les archives anciennes (si nécessaire)
```bash
# Supprimer les archives de plus de 1 an
sqlite3 data/db.sqlite "DELETE FROM passages_archives WHERE timestamp < date('now', '-1 year');"

# Supprimer les archives avant une date spécifique
sqlite3 data/db.sqlite "DELETE FROM passages_archives WHERE timestamp < '2025-01-01';"
```

### Optimiser la base
```bash
sqlite3 data/db.sqlite "VACUUM;"
```

### Vérifier l'intégrité
```bash
sqlite3 data/db.sqlite "PRAGMA integrity_check;"
```

## Dépannage

### Problème : L'archivage ne se déclenche pas

#### Vérification 1 : Le scheduler tourne-t-il ?
```bash
# Vérifier les logs au démarrage
docker-compose logs | grep "scheduler"
```

#### Vérification 2 : Tester manuellement l'archivage
```python
# Dans un shell Python avec le serveur arrêté
import sqlite3
from datetime import datetime

DB_FILE = "data/db.sqlite"

with sqlite3.connect(DB_FILE) as conn:
    c = conn.cursor()
    
    # Archiver
    date_archivage = datetime.now().isoformat()
    c.execute(
        """
        INSERT INTO passages_archives (equipe, latitude, longitude, timestamp, observateur, ville, date_archivage)
        SELECT equipe, latitude, longitude, timestamp, observateur, ville, ?
        FROM passages
        """,
        (date_archivage,)
    )
    
    print(f"Archives créées : {c.rowcount}")
    
    # Vider la table
    c.execute("DELETE FROM passages")
    print(f"Passages supprimés : {c.rowcount}")
    
    conn.commit()
```

### Problème : La page log ne affiche pas tous les passages

#### Vérification 1 : L'API répond-elle ?
```bash
curl http://localhost:62000/api/passages/today
```

#### Vérification 2 : Vérifier la console du navigateur
Ouvrir les DevTools (F12) et regarder les erreurs JavaScript

#### Vérification 3 : Vérifier la réponse de l'API
```bash
curl http://localhost:62000/api/passages/today | jq '.[0]'
```

Doit contenir `"archived": false` ou `"archived": true`

### Problème : Base de données corrompue

#### Sauvegarde et réparation
```bash
# Sauvegarder
cp data/db.sqlite data/db.sqlite.backup

# Exporter
sqlite3 data/db.sqlite .dump > backup.sql

# Recréer
rm data/db.sqlite
sqlite3 data/db.sqlite < backup.sql
```

## Performances

### Indexer la table archives (optionnel)
```sql
CREATE INDEX IF NOT EXISTS idx_archives_timestamp 
ON passages_archives(timestamp);

CREATE INDEX IF NOT EXISTS idx_archives_equipe 
ON passages_archives(equipe);
```

### Analyser les performances
```bash
sqlite3 data/db.sqlite "EXPLAIN QUERY PLAN SELECT * FROM passages_archives WHERE timestamp >= '2026-01-01';"
```

## Monitoring

### Script de monitoring (à ajouter au cron)
```bash
#!/bin/bash
# monitor_archives.sh

DB="/app/data/db.sqlite"
ALERT_EMAIL="admin@example.com"

# Compter les passages actuels
CURRENT=$(sqlite3 $DB "SELECT COUNT(*) FROM passages;")

# Compter les archives
ARCHIVES=$(sqlite3 $DB "SELECT COUNT(*) FROM passages_archives;")

# Log
echo "[$(date)] Passages actuels: $CURRENT, Archives: $ARCHIVES" >> /var/log/pelevtt_monitor.log

# Alerte si trop de passages actuels (devrait être purgé à minuit)
if [ $CURRENT -gt 1000 ]; then
    echo "ALERTE: $CURRENT passages non archivés" | mail -s "PéléVTT: Archivage problème" $ALERT_EMAIL
fi
```

### Ajouter au crontab
```bash
# Vérifier tous les jours à 9h
0 9 * * * /path/to/monitor_archives.sh
```

## Checklist quotidienne

- [ ] Vérifier les logs : `docker-compose logs | tail -20`
- [ ] Vérifier l'archivage de la nuit : `grep "Purge quotidienne" logs/*`
- [ ] Tester la page log : ouvrir dans le navigateur
- [ ] Vérifier la taille de la base : `ls -lh data/db.sqlite`

## Checklist hebdomadaire

- [ ] Sauvegarder la base : `cp data/db.sqlite backup/`
- [ ] Vérifier les statistiques : `sqlite3 data/db.sqlite < check_archives.sql`
- [ ] Tester les APIs : `python3 test_api_archivage.py`
- [ ] Vérifier l'espace disque : `df -h /app/data`

## Checklist mensuelle

- [ ] Analyser la croissance des archives
- [ ] Nettoyer les archives anciennes si nécessaire
- [ ] Optimiser la base : `VACUUM`
- [ ] Vérifier l'intégrité : `PRAGMA integrity_check`
- [ ] Mettre à jour la documentation si modifications

## Contacts en cas de problème

1. **Vérifier la documentation** : ARCHIVAGE.md, GUIDE_ARCHIVAGE.md
2. **Consulter les logs** : `docker-compose logs -f`
3. **Tester avec les scripts** : `test_api_archivage.py`
4. **Vérifier la base** : `check_archives.sql`

---

**En cas de doute, toujours faire une sauvegarde avant toute manipulation !**
