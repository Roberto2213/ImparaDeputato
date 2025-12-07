const CACHE_NAME = 'allenamento-deputati-v7'; // Incremento versione per forzare l'aggiornamento

const APP_SHELL = [
  '/', 
  '/static/manifest.json',
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
  '/static/emiciclo_map.html',

  // AUDIO
  '/static/audio/correct.wav',
  '/static/audio/incorrect.wav',
  '/static/audio/round_start.wav',
  '/static/audio/buzzer_blu.wav',
  '/static/audio/buzzer_verde.wav',
  '/static/audio/buzzer_giallo.wav',
  '/static/audio/buzzer_rosso.wav',

  // ICONE
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

// 1. INSTALLAZIONE
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[Service Worker] Caching App Shell');
        return cache.addAll(APP_SHELL);
      })
      .catch(err => console.error('[Service Worker] Errore Installazione:', err))
  );
  self.skipWaiting();
});

// 2. ATTIVAZIONE
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keyList => {
      return Promise.all(keyList.map(key => {
        if (key !== CACHE_NAME) {
          console.log('[Service Worker] Rimozione vecchia cache:', key);
          return caches.delete(key);
        }
      }));
    })
  );
  return self.clients.claim();
});

// 3. FETCH
self.addEventListener('fetch', event => {
  
  // STRATEGIA: CACHE FIRST per TUTTO (Navigazione e Risorse)
  // Cerca prima nella cache, se non trovi vai in rete.
  
  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      // A. Se è in cache, restituiscilo SUBITO. (Velocità massima, zero rete)
      if (cachedResponse) {
        return cachedResponse;
      }

      // B. Se non è in cache, scaricalo dalla rete
      return fetch(event.request).then(networkResponse => {
        
        // Controllo validità risposta
        if (!networkResponse || networkResponse.status !== 200) {
            return networkResponse; 
        }

        // C. Salva in cache la nuova risorsa per il futuro
        
        // Caso 1: Immagini esterne (es. camera.it) o risorse opache
        const isExternalImage = event.request.url.includes('documenti.camera.it');
        
        // Caso 2: Risorse interne (nostro dominio)
        const isInternalValid = networkResponse.type === 'basic';

        if (isExternalImage || isInternalValid) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then(cache => {
                cache.put(event.request, responseToCache);
            });
        }

        return networkResponse;
      }).catch(() => {
        // D. GESTIONE OFFLINE (Fallback)
        // Se la rete fallisce E non era in cache:
        
        // Se era una navigazione (HTML), restituisci la Home
        if (event.request.mode === 'navigate') {
            return caches.match('/');
        }
        
        // Qui potresti restituire un'immagine placeholder se vuoi
        console.log('Risorsa non disponibile offline:', event.request.url);
      });
    })
  );
});