/**
 * Service Worker - PWA Mode Hors Ligne
 * Permet le fonctionnement de l'application sans connexion internet
 */

// Version du cache - IMPORTANT: Changer ce numéro à chaque déploiement pour forcer la mise à jour
const CACHE_VERSION = '1.1.23';
const CACHE_NAME = `pelevtt-v${CACHE_VERSION}`;
const API_CACHE_NAME = `pelevtt-api-v${CACHE_VERSION}`;

// Ressources à mettre en cache au premier chargement
const STATIC_ASSETS = [
  '/',
  '/sw.js',
  '/static/index.html',
  '/static/carte.html',
  '/static/observateur.html',
  '/static/anim.html',
  '/static/etat.html',
  '/static/log.html',
  '/static/start.html',
  '/static/configuration.html',
  '/static/css/common.css',
  '/static/css/index.css',
  '/static/js/ui-components.js',
  '/static/js/utils.js',
  '/static/js/connection.js',
  '/static/js/auth.js',
  '/static/img/logo_pelevtt.png',
  '/site.webmanifest',
  '/site_anim.webmanifest',
  '/static/favicon.ico'
];

// URLs API à mettre en cache
const API_URLS = [
  '/api/passages',
  '/api/config'
];

// Installation du Service Worker
self.addEventListener('install', (event) => {
  console.log('🔧 Service Worker: Installation...');
  
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('📦 Service Worker: Mise en cache des ressources statiques');
      return cache.addAll(STATIC_ASSETS.map(url => new Request(url, {
        cache: 'reload' // Force le rechargement pour avoir la dernière version
      })));
    }).catch((error) => {
      console.error('❌ Service Worker: Erreur lors de la mise en cache:', error);
      // Continue l'installation même si certains fichiers échouent
    })
  );
  
  // Force l'activation immédiate
  self.skipWaiting();
});

// Activation du Service Worker
self.addEventListener('activate', (event) => {
  console.log('✅ Service Worker: Activation');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // Supprimer les anciens caches
          if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
            console.log('🗑️ Service Worker: Suppression ancien cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      // Prend le contrôle immédiatement
      return self.clients.claim();
    })
  );
});

// Interception des requêtes
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Ignore les requêtes non-GET
  if (request.method !== 'GET') {
    return;
  }
  
  // Ignore les requêtes vers d'autres domaines
  if (url.origin !== location.origin) {
    return;
  }
  
  // Stratégie pour les requêtes API
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstStrategy(request, API_CACHE_NAME));
    return;
  }
  
  // Stratégie pour les ressources statiques
  event.respondWith(cacheFirstStrategy(request, CACHE_NAME));
});

/**
 * Stratégie Cache First (pour ressources statiques)
 * Cherche d'abord dans le cache, puis réseau si non trouvé
 */
async function cacheFirstStrategy(request, cacheName) {
  try {
    // Chercher dans le cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Si pas en cache, requête réseau
    const networkResponse = await fetch(request);
    
    // Mettre en cache pour la prochaine fois
    if (networkResponse && networkResponse.status === 200) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('❌ Service Worker: Erreur cache-first:', error);
    
    // Retourner une page hors ligne personnalisée si disponible
    const offlineResponse = await caches.match('/static/offline.html');
    if (offlineResponse) {
      return offlineResponse;
    }
    
    // Sinon retourner une réponse d'erreur simple
    return new Response('Hors ligne - Cette ressource n\'est pas disponible', {
      status: 503,
      statusText: 'Service Unavailable',
      headers: new Headers({
        'Content-Type': 'text/plain'
      })
    });
  }
}

/**
 * Stratégie Network First (pour API)
 * Essaie d'abord le réseau, puis cache si échec
 */
async function networkFirstStrategy(request, cacheName) {
  try {
    // Essayer le réseau d'abord (avec timeout)
    const timeoutPromise = new Promise((_, reject) => 
      setTimeout(() => reject(new Error('Timeout')), 3000)
    );
    
    const networkResponse = await Promise.race([
      fetch(request),
      timeoutPromise
    ]);
    
    // Mettre en cache si succès
    if (networkResponse && networkResponse.status === 200) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.warn('⚠️ Service Worker: Réseau indisponible, utilisation du cache:', error.message);
    
    // Chercher dans le cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Pas de cache disponible
    return new Response(JSON.stringify({
      error: 'Hors ligne',
      message: 'Impossible de récupérer les données',
      offline: true
    }), {
      status: 503,
      statusText: 'Service Unavailable',
      headers: new Headers({
        'Content-Type': 'application/json'
      })
    });
  }
}

// Synchronisation en arrière-plan (si supporté)
self.addEventListener('sync', (event) => {
  console.log('🔄 Service Worker: Synchronisation en arrière-plan');
  
  if (event.tag === 'sync-passages') {
    event.waitUntil(syncPassages());
  }
});

/**
 * Synchronise les données de passages quand la connexion revient
 */
async function syncPassages() {
  try {
    // Récupérer les passages en attente depuis IndexedDB ou autre storage
    // TODO: Implémenter la logique de sync selon vos besoins
    console.log('📡 Synchronisation des passages...');
  } catch (error) {
    console.error('❌ Erreur de synchronisation:', error);
  }
}

// Messages depuis l'application
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      })
    );
  }
});
