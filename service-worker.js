const CACHE_NAME = 'allenamento-deputati-v6'; // Aggiornato a v6

// LISTA CRITICA: Se uno di questi file manca sul server, L'OFFLINE NON FUNZIONERÀ MAI.
// Controlla bene di avere le icone o commentale se non le hai ancora create!
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
  '/static/emiciclo_map.html', // Assicurati che questo file esista!

  // AUDIO (Assicurati che esistano tutti!)
  '/static/audio/correct.wav',
  '/static/audio/incorrect.wav',
  '/static/audio/round_start.wav',
  '/static/audio/buzzer_blu.wav',
  '/static/audio/buzzer_verde.wav',

  // ICONE (Se non le hai create, COMMENTA QUESTE DUE RIGHE col // davanti)
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

// 1. INSTALLAZIONE: Scarica l'App Shell (Sito base)
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[Service Worker] Caching App Shell');
        // Se qui c'è un errore (es. file mancante), l'installazione si ferma.
        return cache.addAll(APP_SHELL);
      })
      .catch(err => console.error('[Service Worker] Errore Installazione. Manca un file?', err))
  );
  self.skipWaiting();
});

// 2. ATTIVAZIONE: Pulizia vecchie cache
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keyList => {
      return Promise.all(keyList.map(key => {
        if (key !== CACHE_NAME) {
          return caches.delete(key);
        }
      }));
    })
  );
  return self.clients.claim();
});

// 3. FETCH: Il cuore dell'offline
self.addEventListener('fetch', event => {
  
  // A. GESTIONE NAVIGAZIONE (Quando apri l'app o ricarichi la pagina)
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          // SE SEI OFFLINE: Restituisci la pagina principale dalla cache
          return caches.match('/')
              .then(response => {
                  if (response) return response;
                  // Fallback estremo se '/' non è in cache (non dovrebbe succedere)
                  return new Response("Sei offline e la cache è vuota. Riconnettiti per scaricare l'app.");
              });
        })
    );
    return;
  }

  // B. GESTIONE RISORSE (Immagini, CSS, JS, JSON)
  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      // 1. Se è in cache (es. foto scaricata col pulsante), usala subito!
      if (cachedResponse) {
        return cachedResponse;
      }

      // 2. Altrimenti vai in rete
      return fetch(event.request).then(networkResponse => {
        
        // GESTIONE FOTO ESTERNE (Camera.it)
        if (event.request.url.includes('documenti.camera.it')) {
             // Salviamo anche le risposte opache (status 0) o ok (200)
             if (networkResponse.type === 'opaque' || networkResponse.status === 200) {
                 const clone = networkResponse.clone();
                 caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
             }
             return networkResponse;
        }

        // GESTIONE ALTRI FILE INTERNI
        if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
            const clone = networkResponse.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }

        return networkResponse;
      }).catch(() => {
         // Niente rete e niente cache per questa risorsa
         console.log('Risorsa non disponibile offline:', event.request.url);
      });
    })
  );
});