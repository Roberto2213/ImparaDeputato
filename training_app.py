import json
import os
from flask import Flask, render_template, jsonify, send_from_directory

app = Flask(__name__, template_folder='templates', static_folder='static')

CACHE_FILE = 'data_cache.json'
DEPUTIES_DATA = []
COMMITTEE_FILTER_LIST = []

def load_data_from_cache():
    """
    Carica i dati pre-elaborati dal file JSON di cache.
    Molto più veloce rispetto al parsing dei CSV/RDF ad ogni avvio.
    """
    global DEPUTIES_DATA, COMMITTEE_FILTER_LIST
    
    if not os.path.exists(CACHE_FILE):
        print(f"ATTENZIONE: File '{CACHE_FILE}' non trovato!")
        print("Esegui prima 'python build_data_cache.py' per generare i dati.")
        return

    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            DEPUTIES_DATA = data.get('deputies', [])
            COMMITTEE_FILTER_LIST = data.get('committees', [])
            
        print(f"Dati caricati da cache. {len(DEPUTIES_DATA)} deputati pronti.")
    except Exception as e:
        print(f"Errore durante il caricamento della cache: {e}")

def get_all_groups(deputies_list):
    if not deputies_list: return []
    # Filtra solo i gruppi validi (opzionale, ma pulisce la lista)
    groups = set(d['simple_group'] for d in deputies_list if d['simple_group'])
    return sorted(list(groups))

# --- CARICAMENTO DATI ALL'AVVIO ---
load_data_from_cache()

# --- Endpoint Web ---

@app.route('/')
def index():
    return render_template('training.html')

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('.', 'service-worker.js')

@app.route('/api/deputies')
def get_deputies():
    return jsonify(DEPUTIES_DATA)

@app.route('/api/groups')
def get_groups():
    groups = get_all_groups(DEPUTIES_DATA)
    return jsonify(['Tutti'] + groups)

@app.route('/api/committees')
def get_committees():
    return jsonify(['Tutte'] + COMMITTEE_FILTER_LIST)

if __name__ == '__main__':
    if not DEPUTIES_DATA:
        print("\nATTENZIONE: Nessun dato caricato. L'app potrebbe non funzionare correttamente.")
        print(f"Assicurati di aver eseguito 'python build_data_cache.py'.\n")
    
    print("\nServer modalità Allenamento pronto (Versione Ottimizzata).")
    print("Apri il browser su http://127.0.0.1:5000")
    app.run(debug=True, port=5000)