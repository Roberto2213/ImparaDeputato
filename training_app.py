import json
import os
from flask import Flask, render_template, jsonify, send_from_directory, make_response

# Determina il percorso assoluto della cartella dove si trova lo script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

CACHE_FILE = os.path.join(BASE_DIR, 'data_cache.json')
DEPUTIES_DATA = []
COMMITTEE_FILTER_LIST = []

def load_data_from_cache():
    global DEPUTIES_DATA, COMMITTEE_FILTER_LIST
    
    if not os.path.exists(CACHE_FILE):
        print(f"ATTENZIONE: File '{CACHE_FILE}' non trovato!")
        return

    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            DEPUTIES_DATA = data.get('deputies', [])
            COMMITTEE_FILTER_LIST = data.get('committees', [])
        print(f"Dati caricati: {len(DEPUTIES_DATA)} deputati.")
    except Exception as e:
        print(f"Errore caricamento cache: {e}")

def get_all_groups(deputies_list):
    if not deputies_list: return []
    groups = set(d['simple_group'] for d in deputies_list if d['simple_group'])
    return sorted(list(groups))

load_data_from_cache()

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
        print(f"WARN: Cache vuota. Esegui 'python build_data_cache.py' nella cartella {BASE_DIR}")

    print(f"Server avviato su http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)