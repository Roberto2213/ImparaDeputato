const CACHE_NAME = 'allenamento-deputati-v1';
// Lista di file e rotte da mettere in cache subito.
const URLS_TO_CACHE = [
  '/', // La pagina principale
  '/api/deputies',
  '/api/groups',
  '/static/manifest.json' 
  // Le icone sono già referenziate nel manifest, ma possiamo aggiungerle per sicurezza
  // '/static/icons/icon-192x192.png',
  // '/static/icons/icon-512x512.png'
];

// 1. Evento "install": viene eseguito quando il service worker viene installato.
self.addEventListener('install', event => {
  // Aspetta che la cache sia pronta prima di completare l'installazione.
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache aperta');
        return cache.addAll(URLS_TO_CACHE);
      })
  );
});

// 2. Evento "fetch": si attiva ogni volta che la pagina fa una richiesta di rete (es. per un'immagine, un file API, etc.).
self.addEventListener('fetch', event => {
  event.respondWith(
    // Prova a trovare la risorsa nella cache.
    caches.match(event.request)
      .then(response => {
        // Se la risorsa è in cache, restituiscila.
        if (response) {
          return response;
        }

        // Altrimenti, fai la richiesta di rete.
        return fetch(event.request).then(
          networkResponse => {
            // Se la richiesta ha successo, mettiamola in cache per il futuro.
            // Controlliamo che la risposta sia valida prima di metterla in cache.
            if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic' && !networkResponse.type === 'cors') {
                 // Non mettiamo in cache le risposte non valide o le richieste a terze parti senza CORS
                 if (event.request.url.startsWith('https://documenti.camera.it')) {
                     // Gestiamo le foto dei deputati
                     return caches.open(CACHE_NAME).then(cache => {
                         cache.put(event.request, networkResponse.clone());
                         return networkResponse;
                     });
                 }
                 return networkResponse;
            }

            // Cloniamo la risposta perché può essere letta una sola volta.
            const responseToCache = networkResponse.clone();

            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });

            return networkResponse;
          }
        );
      })
  );
});


// 3. Evento "activate": si attiva quando il nuovo service worker diventa attivo.
// Utile per pulire le vecchie cache.
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            // Se la cache non è nella nostra "whitelist", cancellala.
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});