// Cambia questo nome ogni volta che fai un grosso aggiornamento (es. v3, v4, ecc.)
const CACHE_NAME = 'impara-deputato-v2';

// File base da mettere in cache (le foto verranno gestite a parte)
const urlsToCache = [
  '/',
  '/static/training_styles.css',
  '/static/training_logic.js',
  '/static/manifest.json'
];

// 1. FASE DI INSTALLAZIONE
self.addEventListener('install', event => {
  // L'ISTRUZIONE MAGICA: Forza il nuovo Service Worker a prendere il controllo SUBITO,
  // senza aspettare che l'utente chiuda tutte le schede del browser.
  self.skipWaiting(); 
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache aperta');
        return cache.addAll(urlsToCache);
      })
  );
});

// 2. FASE DI ATTIVAZIONE (Pulizia vecchia roba)
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          // Se trova una cache vecchia (es. v1), la ELIMINA senza pietà
          if (cacheName !== CACHE_NAME) {
            console.log('Eliminazione vecchia cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim()) // Prende il controllo immediato della pagina aperta
  );
});

// 3. FASE DI RECUPERO DATI (Network First, fallback to Cache)
self.addEventListener('fetch', event => {
  // Per i file di sistema (HTML, CSS, JS), proviamo PRIMA a scaricarli da internet (Network First)
  // Così l'utente ha sempre l'ultima versione. Se è offline, usiamo la cache.
  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Se la richiesta va a buon fine, aggiorniamo la cache silenziosamente
        if (response && response.status === 200 && response.type === 'basic') {
            const responseToCache = response.clone();
            caches.open(CACHE_NAME).then(cache => {
              cache.put(event.request, responseToCache);
            });
        }
        return response;
      })
      .catch(() => {
        // Se l'utente è offline, peschiamo dalla cache
        return caches.match(event.request);
      })
  );
});