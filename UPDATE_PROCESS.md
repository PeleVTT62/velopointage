# 🔄 Gestion des Mises à Jour PWA

## Problème résolu

L'application PWA utilise le cache du Service Worker, ce qui empêchait les mises à jour d'être déployées automatiquement sur les appareils iOS et Android.

## Architecture des applications

Le système comporte **deux applications PWA distinctes** :

1. **Application Organisateurs** ([static/index.html](static/index.html))
   - Interface complète pour les organisateurs
   - Accès à la carte, configuration, observateurs
   - Manifest : [site.webmanifest](site.webmanifest)

2. **Application Animateurs** ([static/anim.html](static/anim.html))
   - Interface simplifiée pour les animateurs d'équipes
   - Déclaration d'états, demandes d'assistance
   - Manifest : [site_anim.webmanifest](site_anim.webmanifest)

**Les deux applications partagent le même Service Worker** ([static/sw.js](static/sw.js)), donc une seule mise à jour de version suffit pour les deux !

## Solution mise en place

### 1. Mise à jour automatique côté client

- **Détection automatique** : L'application vérifie les nouvelles versions toutes les heures
- **Rechargement automatique** : Quand une mise à jour est détectée, l'application se recharge automatiquement après 3 secondes
- **Notification utilisateur** : L'utilisateur est prévenu avant le rechargement

### 2. Système de versioning

Le fichier [static/sw.js](static/sw.js#L6-L8) contient une variable `CACHE_VERSION` qui contrôle le cache.

```javascript
const CACHE_VERSION = '1.0.2';
```

## 📦 Processus de déploiement

### Option 1 : Script automatique (recommandé)

```bash
# Incrémenter la version patch (1.0.2 → 1.0.3)
python bump_version.py

# Incrémenter la version minor (1.0.2 → 1.1.0)
python bump_version.py minor

# Incrémenter la version major (1.0.2 → 2.0.0)
python bump_version.py major
```

Puis déployez normalement :

```bash
git add static/sw.js
git commit -m "Bump version to X.X.X"
git push
# ... votre processus de déploiement habituel
```

### Option 2 : Modification manuelle

1. Ouvrir [static/sw.js](static/sw.js#L7)
2. Modifier `const CACHE_VERSION = '1.0.2';` en incrémentant le numéro
3. Sauvegarder et déployer

## ⚡ Comment ça fonctionne

1. **Vous déployez** une nouvelle version avec un numéro de cache incrémenté
2. **Les utilisateurs ouvrent** l'application (organisateurs ou animateurs, ou après 1h si déjà ouverte)
3. **Le Service Worker** détecte que la version a changé
4. **L'application affiche** "Nouvelle version disponible ! Rechargement dans 3s..."
5. **L'application se recharge** automatiquement et utilise la nouvelle version
6. **L'ancien cache** est supprimé automatiquement

💡 **Les deux applications** (organisateurs et animateurs) se mettent à jour automatiquement car elles partagent le même Service Worker.

## 🎯 Bonnes pratiques

### À chaque mise à jour importante :
- ✅ Incrémenter la version avec `python bump_version.py`
- ✅ Tester en local avant de déployer
- ✅ Vérifier que le numéro de version a bien changé dans sw.js

### À chaque correction de bug mineur :
- ✅ Utiliser `python bump_version.py` (incrémente le patch)

### Pour les nouvelles fonctionnalités :
- ✅ Utiliser `python bump_version.py minor`

### Pour les changements majeurs :
- ✅ Utiliser `python bump_version.py major`

## 🔍 Vérification

### Vérifier qu'une mise à jour fonctionne :

1. Noter la version actuelle dans [static/sw.js](static/sw.js#L7)
2. Exécuter `python bump_version.py`
3. Déployer
4. Sur l'appareil mobile, ouvrir l'application
5. Après quelques secondes, vous devriez voir : "Nouvelle version disponible !"
6. L'application se recharge automatiquement

### Debug :

Ouvrir la console développeur (sur ordinateur) :
- Les logs du Service Worker indiquent l'installation/activation
- Vérifier dans `Application > Service Workers` que la nouvelle version est active
- Vérifier dans `Application > Cache Storage` que l'ancien cache est supprimé

## 📱 Comportement sur mobile

- **iOS (Safari)** : Le Service Worker vérifie les mises à jour quand l'app est ouverte (organisateurs ou animateurs)
- **Android (Chrome)** : Vérification au lancement + toutes les heures
- **Mode hors ligne** : L'ancienne version reste disponible jusqu'à ce que l'appareil soit en ligne
- **Installation séparée** : Les utilisateurs peuvent installer les deux applications comme des apps distinctes sur leur téléphone

## ⚠️ Important

**N'oubliez jamais de changer la version avant un déploiement**, sinon les clients ne recevront pas la mise à jour !

Le script `bump_version.py` fait ça automatiquement pour vous.
