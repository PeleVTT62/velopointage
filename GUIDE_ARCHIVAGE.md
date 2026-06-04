# 🚀 Guide rapide - Système d'Archivage

## ✅ Ce qui a été mis en place

### 1. Table d'archives automatique
- **Table** : `passages_archives` dans `data/db.sqlite`
- **Création** : Automatique au démarrage de l'application
- **Contenu** : Tous les passages archivés avec leur date d'archivage

### 2. Archivage automatique
- **Quand** : Tous les jours à minuit (00h00)
- **Action** : 
  1. Copie tous les passages dans `passages_archives`
  2. Vide la table `passages` principale
- **Résultat** : Les données du jour sont conservées, la table principale reste légère

### 3. Nouvelles APIs

#### API 1: `/api/passages/today`
Affiche tous les passages du jour (actuels + archives)

```bash
# Exemple d'utilisation
curl http://localhost:62000/api/passages/today
```

#### API 2: `/api/passages/archives`
Consulter les archives avec filtres

```bash
# Tous les passages archivés
curl http://localhost:62000/api/passages/archives

# Passages d'une date spécifique
curl "http://localhost:62000/api/passages/archives?date_debut=2026-01-15&date_fin=2026-01-16"

# Passages du mois dernier
curl "http://localhost:62000/api/passages/archives?date_debut=2025-12-01&date_fin=2026-01-01"
```

### 4. Page log.html mise à jour
- ✅ Affiche automatiquement tous les passages du jour
- ✅ Inclut les passages archivés sans distinction visuelle
- ✅ Mise à jour en temps réel toutes les 2 secondes

## 📱 Utilisation quotidienne

### Pour les observateurs
**Rien ne change !** La page log.html affiche automatiquement tous les passages du jour, qu'ils soient archivés ou non.

### Pour les administrateurs

#### Consulter les logs du jour
1. Ouvrir `http://votreserveur:62000/static/log.html`
2. Tous les passages du jour s'affichent automatiquement

#### Consulter les archives d'un jour spécifique
```bash
# Remplacer la date par celle souhaitée
curl "http://localhost:62000/api/passages/archives?date_debut=2026-01-15&date_fin=2026-01-16" > archives_2026-01-15.json
```

#### Voir les statistiques
```bash
# Utiliser le script de test
python3 test_api_archivage.py
```

## 🔍 Vérification

### 1. Vérifier que la table existe
```bash
sqlite3 data/db.sqlite "SELECT name FROM sqlite_master WHERE type='table' AND name='passages_archives';"
```

Résultat attendu : `passages_archives`

### 2. Vérifier le nombre d'archives
```bash
sqlite3 data/db.sqlite "SELECT COUNT(*) FROM passages_archives;"
```

### 3. Voir les dernières archives
```bash
sqlite3 data/db.sqlite "SELECT equipe, timestamp FROM passages_archives ORDER BY timestamp DESC LIMIT 10;"
```

## 📊 Exemple de workflow

### Matin (avant le départ)
- Les observateurs ouvrent la page log
- Table `passages` vide (purge de la nuit)
- Table `passages_archives` contient les données des jours précédents

### Pendant la journée
- Les passages sont enregistrés dans `passages`
- La page log affiche tous les passages du jour
- Mise à jour en temps réel

### Minuit (automatique)
1. Archivage : `passages` → `passages_archives`
2. Log serveur : `[2026-01-20 00:00:00] Purge quotidienne : 247 passages archivés et supprimés.`
3. Purge : Table `passages` vidée
4. Prêt pour le lendemain

### Après l'événement
- Toutes les données sont dans `passages_archives`
- Consultation possible via API
- Export possible en JSON

## 🛠️ Outils de test

### Test complet
```bash
python3 test_api_archivage.py
```

### Test manuel avec curl
```bash
# Passages du jour
curl http://localhost:62000/api/passages/today | jq

# Archives du mois
curl "http://localhost:62000/api/passages/archives?date_debut=2026-01-01&date_fin=2026-02-01&limit=5000" | jq
```

## 💾 Sauvegarde

Pour sauvegarder toutes les données (passages actuels + archives) :

```bash
# Copier la base de données
cp data/db.sqlite data/db.sqlite.backup_$(date +%Y%m%d)

# Ou avec Docker
docker cp velopointage:/app/data/db.sqlite ./backup_db_$(date +%Y%m%d).sqlite
```

## ❓ FAQ

### Les passages s'affichent-ils toujours sur la page log ?
**Oui !** La page log affiche automatiquement tous les passages du jour, y compris ceux qui ont été archivés à minuit.

### Que se passe-t-il à minuit ?
Les passages du jour sont copiés dans la table d'archives, puis la table principale est vidée. Aucune donnée n'est perdue.

### Comment consulter les passages d'hier ?
Utilisez l'API `/api/passages/archives` avec les dates appropriées, ou consultez directement la base SQLite.

### Les archives prennent-elles beaucoup de place ?
Non, environ 200 Ko pour 1000 passages. Même après un an, la base restera légère (< 100 Mo).

### Peut-on désactiver l'archivage ?
Ce n'est pas recommandé, mais vous pouvez modifier la fonction `purge_passages()` dans `main.py` pour supprimer la partie archivage.

## 🎯 Résumé

**Pour l'utilisateur final** : Rien ne change, tout fonctionne comme avant mais mieux !

**Pour l'administrateur** : 
- ✅ Conservation de toutes les données
- ✅ APIs pour consulter l'historique
- ✅ Performances optimales
- ✅ Archivage automatique
- ✅ Export possible

---

**Système opérationnel et prêt à l'emploi** 🎉
