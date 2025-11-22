# 🇮🇹 ImparaDeputato

**ImparaDeputato** è un'applicazione web interattiva progettata per aiutare gli utenti a memorizzare e riconoscere i membri della Camera dei Deputati italiana, la loro collocazione nell'emiciclo e i gruppi parlamentari di appartenenza attraverso un sistema di quiz e visualizzazione grafica.

## ✨ Funzionalità Principali

  * **Training Mode (Quiz):** Un sistema di gioco interattivo per testare la conoscenza sui deputati.
  * **Mappa dell'Emiciclo:** Visualizzazione grafica dei seggi parlamentari (basata su file SVG/HTML mappati).
  * **Feedback Audio:** Effetti sonori per risposte corrette, errate e inizio round (buzzer, suoni di vittoria).
  * **Gestione Dati:** Script automatici per convertire ed elaborare i dati dei deputati da formati CSV/SPARQL a JSON ottimizzati per il web.
  * **Supporto PWA:** Include un `service-worker.js` e un `manifest.json`, suggerendo che l'app può essere installata o utilizzata offline come Progressive Web App.

## 🛠️ Tecnologie Utilizzate

  * **Backend:** Python (Flask)
  * **Frontend:** HTML5, CSS3, JavaScript
  * **Dati:** Elaborazione di CSV e JSON (dati sui gruppi parlamentari e nominativi)
  * **Deployment:** Predisposto per Heroku (presenza del file `Procfile`)

## 📂 Struttura del Progetto

Ecco una panoramica dei file principali presenti nella repository:

  * `training_app.py`: L'applicazione principale Flask che gestisce il server web e le rotte.
  * `build_data_cache.py` & `convert_to_json.py`: Script di utilità per elaborare i dati grezzi (CSV) e creare la cache JSON (`data_cache.json`) utilizzata dall'app.
  * `templates/`: Contiene i file HTML per l'interfaccia utente (es. `training.html`, `emiciclo_moderno.html`).
  * `static/`:
      * `audio/`: Effetti sonori (buzzer, correct, incorrect).
      * `css/`: Fogli di stile per l'emiciclo e l'interfaccia di training.
      * `js/`: Logica del gioco (`training_logic.js`) e service worker.
  * `data_cache.json` & `seggi.json`: Database locale dei deputati e delle posizioni dei seggi.

## 🚀 Installazione e Avvio Locale

Per eseguire il progetto in locale, assicurati di avere Python installato.

1.  **Clona la repository:**

    ```bash
    git clone https://github.com/roberto2213/imparadeputato.git
    cd imparadeputato
    ```

2.  **Crea un virtual environment (opzionale ma consigliato):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # Su Windows: venv\Scripts\activate
    ```

3.  **Installa le dipendenze:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Prepara i dati (se necessario):**
    Se `data_cache.json` non è aggiornato, puoi rigenerarlo:

    ```bash
    python build_data_cache.py
    ```

5.  **Avvia l'applicazione:**

    ```bash
    python training_app.py
    ```

6.  **Apri il browser:**
    L'applicazione sarà solitamente accessibile all'indirizzo `http://127.0.0.1:5000`.

## ☁️ Deployment

Il progetto include un `Procfile`, rendendolo pronto per il deploy su piattaforme come **Heroku**.

1.  Installa la Heroku CLI.
2.  Crea una nuova app su Heroku.
3.  Collega la repository ed esegui il push:
    ```bash
    git push heroku main
    ```

## 📄 Licenza

Vedi il file [LICENSE](https://www.google.com/search?q=LICENSE) per maggiori dettagli sui diritti di utilizzo.

## 🤝 Contribuire

Le Pull Request sono benvenute. Per modifiche importanti, apri prima una discussione per analizzare cosa vorresti cambiare.

1.  Fai un Fork del progetto
2.  Crea il tuo Feature Branch (`git checkout -b feature/NuovaFunzionalita`)
3.  Commiitta i tuoi cambiamenti (`git commit -m 'Aggiunta nuova funzionalità'`)
4.  Pusha sul Branch (`git push origin feature/NuovaFunzionalita`)
5.  Apri una Pull Request
