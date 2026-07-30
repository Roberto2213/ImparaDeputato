import json
import os
import tempfile
import logging
from flask import Flask, render_template, jsonify, send_from_directory, request
from werkzeug.utils import secure_filename

# Importa i moduli custom per il parsing
try:
    from build_data_cache import process_open_data, process_emiciclo, build_final_cache
except ImportError:
    logging.warning("Modulo 'build_data_cache' non trovato. Assicurati che sia presente per far funzionare l'upload.")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
CACHE_FILE = os.path.join(BASE_DIR, 'data_cache.json')

# Configurazione Sicurezza Upload
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024  # Max 15MB
ALLOWED_EXTENSIONS = {'json', 'html', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def get_fresh_data():
    if not os.path.exists(CACHE_FILE):
        return [], []

    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            deputies = data.get('deputies', [])
            committees = data.get('committees', [])
            
            for d in deputies:
                foto = d.get('foto') or d.get('image_url') or d.get('image') or ''
                foto = foto.replace('http://', 'https://')
                d['foto'] = foto
                d['image'] = foto
                d['image_url'] = foto
                d['img'] = foto

                gen = d.get('genere') or d.get('gender') or d.get('sesso') or 'Maschio'
                d['genere'] = gen
                d['gender'] = gen
                d['sesso'] = gen

                col = d.get('circoscrizione') or d.get('collegio') or 'Territorio nazionale'
                d['circoscrizione'] = col
                d['collegio'] = col
                
            return deputies, committees
    except Exception as e:
        logging.error(f"Errore caricamento cache: {e}")
        return [], []

@app.route('/')
def index():
    return render_template('training.html')

@app.route('/data_cache.json')
def serve_data_cache():
    deputies, committees = get_fresh_data()
    return jsonify({
        "deputies": deputies,
        "committees": committees
    })

@app.route('/api/deputies')
def get_deputies():
    deputies, _ = get_fresh_data()
    return jsonify(deputies)

@app.route('/api/groups')
def get_groups():
    deputies, _ = get_fresh_data()
    groups = set(d.get('simple_group', 'Misto') for d in deputies if d.get('simple_group'))
    return jsonify(['Tutti'] + sorted(list(groups)))

@app.route('/api/committees')
def get_committees():
    _, committees = get_fresh_data()
    return jsonify(['Tutte'] + committees)

@app.route('/emiciclo')
def mappa_moderna():
    return render_template('emiciclo_moderno.html')

@app.route('/manifest.json')
def manifest():
    return send_from_directory(STATIC_DIR, 'manifest.json')

# --- ENDPOINT: RICEZIONE E AGGIORNAMENTO CACHE ---
@app.route('/api/update_cache', methods=['POST'])
def update_cache():
    if 'open_data' not in request.files or 'emiciclo_data' not in request.files:
        return jsonify({'error': 'File mancanti nella richiesta.'}), 400

    open_data_file = request.files['open_data']
    emiciclo_file = request.files['emiciclo_data']

    if not open_data_file.filename or not emiciclo_file.filename:
        return jsonify({'error': 'Nessun file selezionato.'}), 400

    if not (allowed_file(open_data_file.filename) and allowed_file(emiciclo_file.filename)):
        return jsonify({'error': 'Estensione file non consentita.'}), 415

    # Utilizziamo la directory temporanea solo per i file di input in transito
    with tempfile.TemporaryDirectory() as temp_dir:
        open_data_path = os.path.join(temp_dir, secure_filename(open_data_file.filename))
        emiciclo_path = os.path.join(temp_dir, secure_filename(emiciclo_file.filename))
        
        try:
            open_data_file.save(open_data_path)
            emiciclo_file.save(emiciclo_path)

            # Esecuzione dei parser custom
            deputati_data = process_open_data(open_data_path)
            emiciclo_layout = process_emiciclo(emiciclo_path)
            
            # Sovrascrive direttamente il file cache locale (data_cache.json) in uso dall'applicazione
            build_final_cache(deputati_data, emiciclo_layout, CACHE_FILE)

            # Restituisce un JSON di successo per permettere al frontend di reagire
            return jsonify({
                'success': True,
                'message': 'Cache rigenerata e salvata con successo sul server.'
            }), 200

        except Exception as e:
            logging.error(f"Errore generazione cache: {str(e)}", exc_info=True)
            return jsonify({'error': 'Errore nell\'elaborazione dei file forniti.'}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"Server Flask avviato su http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
