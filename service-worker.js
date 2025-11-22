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
    caches.match(event.request).then(response => {
      // 1. Se è in cache, restituisci subito
      if (response) {
        return response;
      }

      // 2. Altrimenti vai in rete
      return fetch(event.request).then(networkResponse => {
        
        // A. GESTIONE IMMAGINI ESTERNE (Camera.it)
        // Le immagini 'no-cors' hanno status 0 e type 'opaque'. Dobbiamo salvarle comunque!
        if (event.request.url.includes('documenti.camera.it')) {
             // Se la risposta è valida o opaca (status 0), la cachiamo
             if (networkResponse.type === 'opaque' || networkResponse.status === 200) {
                 const responseToCache = networkResponse.clone();
                 caches.open(CACHE_NAME).then(cache => {
                     cache.put(event.request, responseToCache);
                 });
             }
             return networkResponse;
        }

        // B. GESTIONE STANDARD (File interni della tua app)
        // Se non è valido o non è status 200, non cachare (evita di salvare errori 404/500)
        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
          return networkResponse;
        }

        // C. CACHE DEI FILE INTERNI
        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then(cache => {
          cache.put(event.request, responseToCache);
        });

        return networkResponse;
      });
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