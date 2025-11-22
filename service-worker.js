// 1. CAMBIA IL NOME DELLA CACHE OGNI VOLTA CHE AGGIORNI!
const CACHE_NAME = 'allenamento-deputati-v5';

// 2. AGGIUNGI TUTTI I FILE DELL'APP SHELL
const URLS_TO_CACHE = [
  '/', 
  
  // LOGICA E DATI (Fondamentale: aggiunto seggi.json)
  '/static/training_logic.js',
  '/static/seggi.json', 

  // CSS
  '/static/training_styles.css',
  '/static/dove_siedono.css',
  '/static/posizioni.css',
  '/static/gruppi.css',
  '/static/componenti.css',

  // HTML Aggiuntivi
  '/static/emiciclo.html',
  '/static/emiciclo_quiz.html',
  '/static/emiciclo_map.html', // Aggiunto per sicurezza

  // Manifest e icone
  '/static/manifest.json',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',

  // Audio (Aggiunti i buzzer che mancavano)
  '/static/audio/correct.wav',
  '/static/audio/incorrect.wav',
  '/static/audio/round_start.wav',
  '/static/audio/buzzer_blu.wav',
  '/static/audio/buzzer_verde.wav'
];

// 1. Evento "install"
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache aperta:', CACHE_NAME);
        return cache.addAll(URLS_TO_CACHE);
      })
  );
  
  // Forza il service worker a passare dallo stato "waiting" ad "active"
  self.skipWaiting();
});


// 2. Evento "fetch": si attiva ogni volta che la pagina fa una richiesta di rete
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
            if (!networkResponse || networkResponse.status !== 200) {
                 return networkResponse;
            }
            
            // Gestione speciale per le foto, ma va bene anche per altri
             if (networkResponse.type !== 'basic' && !networkResponse.type === 'cors') {
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
                // Metti in cache la nuova risorsa (JS, CSS, API, FOTO, ecc.)
                cache.put(event.request, responseToCache);
              });

            return networkResponse;
          }
        );
      })
  );
});


// 3. Evento "activate"
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME]; // Solo la nuova cache 'v4' è permessa
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          // Se il nome della cache NON è nella whitelist (è una vecchia cache 'v3')
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            console.log('Cancellazione vecchia cache:', cacheName);
            return caches.delete(cacheName); // Cancellala
          }
        })
      );
    }).then(() => {
      // Prende il controllo immediato di tutte le pagine aperte
      return self.clients.claim();
    })
  );
});