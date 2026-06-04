# 📚 Système d'Archivage - Documentation

## Vue d'ensemble

Le système d'archivage permet de conserver l'historique complet de tous les passages enregistrés, même après la purge quotidienne automatique.

## 🗄️ Structure de la base de données

### Table `passages` (table principale - données du jour)
- Contient les passages en cours
- Purgée automatiquement à minuit (00h00)
- Données archivées avant suppression

### Table `passages_archives` (nouvelle table)
```sql
CREATE TABLE passages_archives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipe TEXT,
    latitude REAL,
    longitude REAL,
    timestamp TEXT,
    observateur TEXT,
    ville TEXT,
    date_archivage TEXT
)
```

## 🔄 Processus d'archivage automatique

### Déclenchement
- **Heure** : Tous les jours à 00h00 (minuit)
- **Action automatique** : Exécutée par le scheduler APScheduler

### Étapes
1. **Archivage** : Copie tous les passages de `passages` vers `passages_archives`
2. **Suppression** : Vide la table `passages`
3. **Log** : Enregistre le nombre d'entrées archivées

```python
# Exemple de log
[2026-01-20 00:00:00] Purge quotidienne : 247 passages archivés et supprimés.
```

## 🌐 Nouvelles APIs

### 1. GET `/api/passages/today`
Récupère tous les passages du jour (actuels + archives)

**Paramètres** :
- `include_archives` (optional, default: true) : Inclure les archives

**Réponse** :
```json
[
  {
    "id": 123,
    "equipe": "Saint Pierre",
    "latitude": 50.123,
    "longitude": 2.456,
    "timestamp": "2026-01-20T14:30:00",
    "observateur": "Jean",
    "ville": "Bruay",
    "archived": false
  },
  {
    "id": 456,
    "equipe": "Saint Paul",
    "latitude": 50.234,
    "longitude": 2.567,
    "timestamp": "2026-01-20T08:15:00",
    "observateur": "Marie",
    "ville": "Aire-sur-la-Lys",
    "archived": true,
    "date_archivage": "2026-01-20T00:00:00"
  }
]
```

**Usage** :
```javascript
// Récupérer tous les passages du jour
const response = await fetch('/api/passages/today');
const passages = await response.json();

// Récupérer uniquement les passages actuels (sans archives)
const response = await fetch('/api/passages/today?include_archives=false');
```

### 2. GET `/api/passages/archives`
Récupère les passages archivés avec filtrage par date

**Paramètres** :
- `date_debut` (optional) : Date de début au format ISO (YYYY-MM-DD)
- `date_fin` (optional) : Date de fin au format ISO (YYYY-MM-DD)
- `limit` (optional, default: 1000) : Nombre maximum de résultats

**Exemples d'utilisation** :

```bash
# Tous les passages archivés (limité à 1000)
curl http://localhost:62000/api/passages/archives

# Passages d'une journée spécifique
curl "http://localhost:62000/api/passages/archives?date_debut=2026-01-15&date_fin=2026-01-16"

# Passages d'un mois
curl "http://localhost:62000/api/passages/archives?date_debut=2026-01-01&date_fin=2026-01-31"

# Depuis une date jusqu'à aujourd'hui
curl "http://localhost:62000/api/passages/archives?date_debut=2026-01-01"

# Limiter à 500 résultats
curl "http://localhost:62000/api/passages/archives?limit=500"
```

### 3. GET `/api/passages` (existant)
Récupère les passages récents (table principale)

**Paramètres** :
- `limit` (optional, default: 100) : Nombre maximum de résultats

## 📱 Page log.html mise à jour

### Changements
- ✅ Affiche automatiquement tous les passages du jour (actuels + archives)
- ✅ Mise à jour en temps réel toutes les 2 secondes
- ✅ Les passages archivés sont inclus dans les statistiques
- ✅ Pas de différence visuelle entre passages actuels et archivés

### Comportement
1. Au chargement : affiche tous les passages du jour
2. Mise à jour automatique : toutes les 2 secondes
3. Filtres : fonctionnent sur tous les passages (actuels + archives)

## 🔍 Exemple de cas d'usage

### Scénario 1 : Consultation des logs en cours de journée
```javascript
// La page log.html récupère automatiquement
const response = await fetch('/api/passages/today');
const passages = await response.json();
// Affiche tous les passages du jour
```

### Scénario 2 : Analyse d'une journée passée
```javascript
// Récupérer les passages du 15 janvier 2026
const response = await fetch('/api/passages/archives?date_debut=2026-01-15&date_fin=2026-01-16');
const passages = await response.json();
```

### Scénario 3 : Export mensuel
```javascript
// Récupérer tous les passages de janvier 2026
const response = await fetch('/api/passages/archives?date_debut=2026-01-01&date_fin=2026-02-01&limit=10000');
const passages = await response.json();
// Exporter en CSV, JSON, etc.
```

## 📊 Statistiques et capacité

### Estimation de la taille
- 1 passage ≈ 200 octets
- 1000 passages ≈ 200 Ko
- 10000 passages ≈ 2 Mo
- SQLite peut gérer plusieurs millions d'entrées sans problème

### Performances
- **Requêtes** : Indexées par timestamp pour des recherches rapides
- **Archivage** : Opération rapide (< 1 seconde pour 1000 passages)
- **Consultation** : Pas d'impact sur les performances en temps réel

## 🛠️ Maintenance

### Vérifier les archives
```python
import sqlite3

conn = sqlite3.connect('data/db.sqlite')
c = conn.cursor()

# Nombre d'entrées archivées
c.execute("SELECT COUNT(*) FROM passages_archives")
print(f"Passages archivés : {c.fetchone()[0]}")

# Plus ancien et plus récent
c.execute("SELECT MIN(timestamp), MAX(timestamp) FROM passages_archives")
oldest, newest = c.fetchone()
print(f"Période : {oldest} à {newest}")

conn.close()
```

### Nettoyer les anciennes archives (si nécessaire)
```python
# Supprimer les archives de plus de 1 an
conn = sqlite3.connect('data/db.sqlite')
c = conn.cursor()
c.execute("DELETE FROM passages_archives WHERE timestamp < date('now', '-1 year')")
conn.commit()
print(f"{c.rowcount} entrées supprimées")
conn.close()
```

## ✅ Avantages du système

1. **Conservation des données** : Aucune perte d'information
2. **Performance** : Table principale toujours légère
3. **Flexibilité** : Requêtes par date sur les archives
4. **Transparence** : La page log affiche automatiquement tout le jour
5. **Automatique** : Aucune intervention manuelle nécessaire

## 🔐 Sécurité

- Les données archivées sont stockées dans la même base SQLite
- Sauvegarder régulièrement `data/db.sqlite` pour préserver les archives
- Les archives ne sont jamais supprimées automatiquement

## 📝 Notes importantes

- La page log.html affiche maintenant **tous les passages du jour** incluant les archives
- L'archivage se fait **avant minuit** du jour suivant
- Les passages enregistrés avant minuit sont archivés à minuit
- Les archives sont consultables via l'API `/api/passages/archives`
