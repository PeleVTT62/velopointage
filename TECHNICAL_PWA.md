# 🔧 Note Technique - Système PWA Dual-App

## Architecture

### Service Worker unique partagé

Le système utilise **un seul Service Worker** ([static/sw.js](static/sw.js)) qui gère le cache pour les deux applications :

```
Service Worker (sw.js)
    ├─ Cache: pelevtt-v1.0.3
    │   ├─ /static/index.html (App TTV)
    │   ├─ /static/anim.html (App anim)
    │   ├─ CSS communs
    │   └─ JS communs
    └─ Cache API: pelevtt-api-v1.0.3
        ├─ /api/passages
        ├─ /api/config
        └─ /api/equipes
```

### Deux manifests distincts

- **site.webmanifest** : App TTV
  - `start_url`: `/?utm_source=homescreen`
  - `scope`: `/`
  - `name`: "PéléVTT 62"

- **site_anim.webmanifest** : App anim
  - `start_url`: `/static/anim.html?source=pwa`
  - `scope`: `/static/`
  - `name`: "Anim PéléVTT 62"
  - `id`: `/static/anim.html` (permet installation séparée)

### Enregistrement du Service Worker

Les deux HTML enregistrent le même Service Worker :

```javascript
// Dans index.html et anim.html
const registration = await navigator.serviceWorker.register('/static/sw.js');
```

## Stratégie de mise à jour

### 1. Version unique

Une seule variable contrôle les deux apps :

```javascript
// static/sw.js
const CACHE_VERSION = '1.0.3';
const CACHE_NAME = `pelevtt-v${CACHE_VERSION}`;
```

### 2. Détection automatique

Chaque app écoute les mises à jour :

```javascript
registration.addEventListener('updatefound', () => {
  const newWorker = registration.installing;
  newWorker.addEventListener('statechange', () => {
    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
      // Notification + rechargement auto après 3s
      showToast('🔄 Nouvelle version disponible !', 'info');
      setTimeout(() => {
        newWorker.postMessage({ type: 'SKIP_WAITING' });
        window.location.reload();
      }, 3000);
    }
  });
});
```

### 3. Vérification périodique

```javascript
// Toutes les heures
setInterval(() => {
  registration.update();
}, 60 * 60 * 1000);
```

### 4. Suppression ancien cache

```javascript
// Dans sw.js - event activate
caches.keys().then((cacheNames) => {
  return Promise.all(
    cacheNames.map((cacheName) => {
      if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
        return caches.delete(cacheName);
      }
    })
  );
});
```

## Workflow de déploiement

### Automatique (recommandé)

```bash
# Incrémente la version automatiquement
python3 bump_version.py

# Commit et push
git add static/sw.js
git commit -m "Bump PWA version to $(grep CACHE_VERSION static/sw.js | sed "s/.*'\(.*\)'.*/\1/")"
git push

# Sur le serveur
docker-compose up -d --build
```

### Manuel

1. Éditer [static/sw.js](static/sw.js#L7)
2. Changer `const CACHE_VERSION = '1.0.X';`
3. Déployer

## Tests

### Tester la mise à jour en local

1. Lancer le serveur :
   ```bash
   uvicorn main:app --reload
   ```

2. Ouvrir les deux apps :
   - `http://localhost:62000/static/index.html`
   - `http://localhost:62000/static/anim.html`

3. Dans Chrome DevTools → Application → Service Workers :
   - Vérifier que le SW est actif pour les deux scopes
   - Vérifier la version du cache

4. Incrémenter la version :
   ```bash
   python3 bump_version.py
   ```

5. Recharger une des pages :
   - Le message "Nouvelle version disponible" devrait apparaître
   - L'app se recharge après 3s
   - L'ancien cache est supprimé

### Tester l'installation PWA

**iOS** :
- Safari → ouvrir anim.html → Partager → "Sur l'écran d'accueil"
- Vérifier que l'icône "Anim PéléVTT 62" apparaît
- Lancer l'app depuis l'écran d'accueil
- Vérifier qu'elle s'ouvre en plein écran

**Android** :
- Chrome → ouvrir anim.html → Menu → "Installer l'application"
- Vérifier le dialogue d'installation
- L'app apparaît dans le tiroir d'applications

## Considérations techniques

### Pourquoi un seul Service Worker ?

✅ **Avantages** :
- Une seule version à gérer
- Cache partagé pour ressources communes
- Déploiement simplifié

❌ **Inconvénients potentiels** :
- Si les apps ont des besoins de cache très différents
- Si on veut des stratégies de mise à jour différentes

Pour ce projet, un seul SW est optimal car :
- Les apps partagent beaucoup de ressources
- Même cycle de vie (déployées ensemble)
- Simplification pour les utilisateurs

### Scopes différents mais SW commun

C'est possible car :
- Le SW est enregistré à `/static/sw.js`
- Son scope par défaut est `/static/`
- Les deux apps sont sous `/static/`
- Les manifests utilisent des `id` différents pour permettre installation séparée

### Gestion du cache API

Le SW utilise une stratégie **Network First** pour les API :
```javascript
if (url.pathname.startsWith('/api/')) {
  event.respondWith(networkFirstStrategy(request, API_CACHE_NAME));
}
```

Cela garantit des données fraîches, avec fallback sur cache si hors ligne.

### Messages entre app et SW

```javascript
// App → SW : forcer activation
newWorker.postMessage({ type: 'SKIP_WAITING' });

// SW → App : notification (via events)
registration.addEventListener('updatefound', ...)
```

## Métriques et monitoring

### Vérifier les utilisateurs sous version X

Impossible directement, mais on peut :
1. Logger la version au chargement de page
2. Envoyer via API analytics
3. Tracker les versions actives

### Forcer la mise à jour immédiate

Si urgence (bug critique) :
1. Incrémenter la version
2. Déployer
3. Les apps se mettront à jour :
   - Au prochain lancement
   - Ou dans l'heure si déjà ouvertes
4. Pas de moyen de forcer instantanément sans que l'utilisateur ouvre l'app

## Ressources

- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Web App Manifest](https://developer.mozilla.org/en-US/docs/Web/Manifest)
- [Workbox (future amélioration possible)](https://developers.google.com/web/tools/workbox)

## Améliorations futures possibles

1. **Background Sync** : Synchroniser les données quand la connexion revient
2. **Push Notifications** : Alerter les utilisateurs de nouveaux passages
3. **IndexedDB** : Stocker plus de données localement
4. **Workbox** : Framework Google pour simplifier le SW
5. **Version checking API** : Endpoint pour que les apps vérifient la version serveur
