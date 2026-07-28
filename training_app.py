import json
import os
import logging
from flask import Flask, render_template, jsonify, send_from_directory, make_response, request
from werkzeug.utils import secure_filename

# Configurazione logging per produzione
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Determina il percorso assoluto della cartella dove si trova lo script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

CACHE_FILE = os.path.join(BASE_DIR, 'data_cache.json')
DEPUTIES_DATA = []
COMMITTEE_FILTER_LIST = []

def load_data_from_cache():
    """Carica i dati in memoria. Viene chiamata all'avvio e dopo un upload manuale."""
    global DEPUTIES_DATA, COMMITTEE_FILTER_LIST
    
    if not os.path.exists(CACHE_FILE):
        logger.warning(f"ATTENZIONE: File '{CACHE_FILE}' non trovato!")
        return

    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            DEPUTIES_DATA = data.get('deputies', [])
            COMMITTEE_FILTER_LIST = data.get('committees', [])
        logger.info(f"Dati caricati: {len(DEPUTIES_DATA)} deputati.")
    except json.JSONDecodeError:
        logger.error(f"Formato non valido o corrotto in '{CACHE_FILE}' (JSONDecodeError).")
    except Exception as e:
        logger.error(f"Errore I/O durante il caricamento cache: {e}")

def get_all_groups(deputies_list):
    if not deputies_list: return []
    groups = set(d['simple_group'] for d in deputies_list if d['simple_group'])
    return sorted(list(groups))

# Caricamento iniziale
load_data_from_cache()

# ==========================================
# ENDPOINT FALLBACK: UPLOAD MANUALE UTENTE
# ==========================================
def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'json'

@app.route('/api/admin/upload-dataset', methods=['POST'])
def upload_dataset():
    """Permette l'upload manuale del file JSON bypassando GitHub e lo scraping."""
    if 'file' not in request.files:
        return jsonify({"error": "Nessun file fornito"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nome file vuoto"}), 400
        
    if file and allowed_file(file.filename):
        try:
            # Sicurezza: rimuove path traversal
            filename = secure_filename(file.filename)
            file.save(CACHE_FILE)
            
            # Hot-reload in memoria: aggiorna i dati senza riavviare l'app
            load_data_from_cache()
            return jsonify({"message": "Dataset aggiornato e caricato in memoria con successo."}), 200
        except Exception as e:
            logger.exception("Errore di sistema durante l'upload del file.")
            return jsonify({"error": "Errore interno del server sul salvataggio."}), 500
    
    return jsonify({"error": "Formato file non valido. Atteso: .json"}), 400
# ==========================================

@app.route('/')
def index():
    return render_template('training.html')

@app.route('/service-worker.js')
def service_worker():
    response = make_response(send_from_directory(BASE_DIR, 'service-worker.js'))
    # Header vitali per lo sviluppo dei Service Worker:
    # Disabilita la cache del browser per il file JS del worker stesso
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/deputies')
def get_deputies():
    # Poiché i dati cambiano raramente, qui potremmo permettere il caching,
    # ma per sicurezza in fase di dev lasciamo no-cache o default.
    return jsonify(DEPUTIES_DATA)

@app.route('/api/groups')
def get_groups():
    groups = get_all_groups(DEPUTIES_DATA)
    return jsonify(['Tutti'] + groups)

@app.route('/api/committees')
def get_committees():
    return jsonify(['Tutte'] + COMMITTEE_FILTER_LIST)

@app.route('/emiciclo')
def mappa_moderna():
    return render_template('emiciclo_moderno.html')

@app.route('/manifest.json')
def manifest():
    return send_from_directory(STATIC_DIR, 'manifest.json')

if __name__ == '__main__':
    # Configurazione robusta per l'esecuzione
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "True") == "True"
    
    if not DEPUTIES_DATA:
        logger.warning(f"Cache vuota all'avvio. Eseguire l'upload o 'python build_data_cache.py' in {BASE_DIR}")

    logger.info(f"Server in avvio su http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
