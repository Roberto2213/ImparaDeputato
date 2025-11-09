import csv
import re
import unicodedata
from flask import Flask, render_template, jsonify, send_from_directory
from rdflib import Graph, URIRef, RDF, RDFS
from bs4 import BeautifulSoup  # <-- IMPORT AGGIUNTO

app = Flask(__name__, template_folder='templates', static_folder='static')

DEPUTIES_DATA = []
COMMITTEE_FILTER_LIST = [] # Per la lista dei filtri

def create_canonical_key(name_str):
    nfkd_form = unicodedata.normalize('NFKD', name_str)
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    cleaned_str = re.sub('[^a-zA-Z ]', '', only_ascii).upper()
    parts = sorted(cleaned_str.split())
    return "".join(parts)

def build_new_photo_url(uri):
    match = re.search(r'(d\d+)', uri)
    if match:
        dep_id = match.group(1)
        return f"https://documenti.camera.it/_dati/leg19/schededeputatinuovosito/fotoDefinitivo/big/{dep_id}.jpg"
    return None

def load_alias_map():
    alias_map = {}
    try:
        with open('alias_deputati.csv', mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            next(reader)
            for row in reader:
                if len(row) >= 2:
                    alias_map[row[0].strip()] = row[1].strip()
    except FileNotFoundError:
        print("ATTENZIONE: File 'alias_deputati.csv' non trovato.")
    return alias_map

def normalize_group_name(group_name):
    normalization_map = [
        ("FRATELLI D'ITALIA", "Fratelli d'Italia"),
        ("PARTITO DEMOCRATICO", "Partito Democratico"),
        ("LEGA", "Lega - Salvini Premier"),
        ("MOVIMENTO 5 STELLE", "Movimento 5 Stelle"),
        ("FORZA ITALIA", "Forza Italia"),
        ("AZIONE - ITALIA VIVA", "Azione - Italia Viva"),
        ("VERDI E SINISTRA", "Alleanza Verdi e Sinistra"),
        ("NOI MODERATI", "Noi Moderati"),
        ("MISTO", "Gruppo Misto")
    ]
    upper_group = group_name.upper()
    for key, canonical_name in normalization_map:
        if key in upper_group:
            return canonical_name
    simplified = re.split(r' - |–|—|\(Cessato', group_name)[0].strip()
    return simplified

# --- NUOVA FUNZIONE PER LEGGERE L'EMICICLO ---
def load_seat_map(canonical_key_func):
    """
    Legge static/emiciclo.html e crea una mappa {canonical_key: seat_number}.
    """
    seat_map = {}
    # Ora il file si trova in 'static'
    file_path = 'static/emiciclo.html' 
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        
        # Seleziona tutti i seggi che hanno un deputato assegnato
        # (hanno un 'id' che inizia con 'seggio_' e un 'title' che contiene ' - ')
        seats = soup.select('a[id^="seggio_"][title*=" - "]')
        
        for seat in seats:
            try:
                # Estrai info dal titolo es: "15 - GRIBAUDO CHIARA PD-IDP"
                title_text = seat['title']
                
                # Estrai numero seggio
                seat_number = title_text.split(' - ')[0].strip()
                
                # Estrai nome (tutto tra ' - ' e l'ultimo spazio)
                name_and_group = title_text.split(' - ')[1]
                name_str = name_and_group.rsplit(' ', 1)[0].strip()
                
                # Crea la stessa chiave canonica usata dal resto dell'app
                key = canonical_key_func(name_str)
                
                if key:
                    seat_map[key] = seat_number
            except Exception:
                # Ignora seggi formattati male (es. "Postazione disabilitata")
                continue
                
    except FileNotFoundError:
        print(f"ATTENZIONE: File '{file_path}' non trovato. I numeri di seggio non saranno disponibili.")
    except Exception as e:
        print(f"Errore durante la lettura di '{file_path}' (forse 'pip install beautifulsoup4'?): {e}")
    
    return seat_map

# --- NUOVA FUNZIONE PER ORDINARE LE COMMISSIONI ---
def get_sorted_committees(all_committee_names):
    """
    Ordina la lista di commissioni.
    Priorità:
    1. Commissioni Romane (I, II, ...)
    2. Commissioni Bicamerali
    3. Giunte
    4. Commissioni d'Inchiesta
    5. Tutto il resto (es. Comitati)
    Ogni gruppo è ordinato alfabeticamente al suo interno.
    """
    roman_numeral_pattern = re.compile(r'^[IVXLC]+\s+COMMISSIONE')
    
    # Liste per ogni categoria
    p1_roman = []
    p2_bicameral = []
    p3_giunte = []
    p4_inchiesta = []
    p5_others = [] # Qui finiranno i Comitati

    for name in all_committee_names:
        if not name:
            continue
        
        clean_name = name.strip()
        upper_name = clean_name.upper()

        if roman_numeral_pattern.match(upper_name):
            p1_roman.append(clean_name)
        elif upper_name.startswith("COMMISSIONE BICAMERALE"):
            p2_bicameral.append(clean_name)
        elif upper_name.startswith("GIUNTA"):
            p3_giunte.append(clean_name)
        elif upper_name.startswith("COMMISSIONE D'INCHIESTA"):
            p4_inchiesta.append(clean_name)
        else:
            p5_others.append(clean_name) # I comitati finiscono qui
            
    # Ordina ogni singola lista e concatena
    return (sorted(p1_roman) + 
            sorted(p2_bicameral) + 
            sorted(p3_giunte) + 
            sorted(p4_inchiesta) + 
            sorted(p5_others))

# --- FUNZIONE MODIFICATA PER LEGGERE TUTTI I DATI AGGIUNTIVI ---
def load_additional_data(canonical_key_func):
    """
    Legge sparql (1).csv e ritorna:
    1. Una mappa dei dati per deputato {key: {committees, constituency, gender}}
    2. Un set con TUTTI i nomi unici delle commissioni trovate.
    """
    additional_data_map = {}
    all_committee_names_set = set()
    file_path = 'sparql (1).csv'
    
    try:
        with open(file_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                name_str = f"{row['cognome']} {row['nome']}"
                key = canonical_key_func(name_str)
                
                if not key:
                    continue
                
                if key not in additional_data_map:
                    additional_data_map[key] = {
                        "committees": set(),
                        "constituency": row.get('collegio', 'N/D'),
                        "gender": row.get('genere', 'N/D')
                    }
                
                committee_name = row.get('commissione')
                if committee_name:
                    clean_name = committee_name.strip()
                    if clean_name: # Non aggiungere stringhe vuote
                        additional_data_map[key]["committees"].add(clean_name)
                        all_committee_names_set.add(clean_name)
        
        for key, data in additional_data_map.items():
            data['committees'] = sorted(list(data['committees']))
            
        return additional_data_map, all_committee_names_set # Ritorna entrambi

    except FileNotFoundError:
        print(f"ATTENZIONE: File '{file_path}' non trovato.")
        return {}, set()
    except Exception as e:
        print(f"Errore durante la lettura di '{file_path}': {e}")
        return {}, set()

def load_deputies_data():
    global COMMITTEE_FILTER_LIST
    try:
        alias_map = load_alias_map()
        
        additional_data_map, all_committee_names = load_additional_data(create_canonical_key)
        
        # --- NUOVA RIGA ---
        seat_map = load_seat_map(create_canonical_key) # <-- CARICA LA MAPPA SEGGI
        
        # Popola la lista per il filtro API con la nuova logica di ORDINAMENTO
        COMMITTEE_FILTER_LIST = get_sorted_committees(all_committee_names)
        
        g = Graph()
        g.parse("deputato-19.txt", format="nt")

        rdf_deputies = {}
        for s, _, _ in g.triples((None, RDF.type, URIRef("http://dati.camera.it/ocd/deputato"))):
            name_literal = g.value(s, RDFS.label) or g.value(s, URIRef("http://purl.org/dc/elements/1.1/title"))
            if name_literal:
                raw_name = str(name_literal).split(',')[0].strip()
                corrected_name = alias_map.get(raw_name, raw_name)
                key = create_canonical_key(corrected_name)
                photo_url = build_new_photo_url(str(s))
                if photo_url and key:
                    rdf_deputies[key] = {"photo_url": photo_url}

        final_deputies = []
        with open('Nominativo,Gruppo.csv', mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            next(reader)
            for row in reader:
                if len(row) < 2: continue
                full_name, group = row[0], ",".join(row[1:])
                clean_name = full_name.split('(')[0].strip()
                key = create_canonical_key(clean_name)
                if key in rdf_deputies:
                    deputy_info = rdf_deputies[key]
                    deputy_info['name'] = clean_name
                    deputy_info['group'] = group
                    deputy_info['simple_group'] = normalize_group_name(group)
                    
                    additional_data = additional_data_map.get(key, {})
                    deputy_info['committees'] = additional_data.get('committees', [])
                    deputy_info['constituency'] = additional_data.get('constituency', 'N/D')
                    deputy_info['gender'] = additional_data.get('gender', 'N/D')
                    
                    # --- NUOVA RIGA ---
                    deputy_info['seat'] = seat_map.get(key, 'N/D') # <-- AGGIUNGI IL SEGGIO AI DATI
                    
                    final_deputies.append(deputy_info)
        
        print(f"--- Dati caricati per {len(final_deputies)} deputati. ---")
        print(f"--- Dati aggiuntivi (collegio, genere, commissioni) caricati per {len(additional_data_map)} deputati. ---")
        print(f"--- Mappa seggi creata per {len(seat_map)} deputati. ---") # <-- NUOVO LOG
        print(f"--- Creato filtro ordinato con {len(COMMITTEE_FILTER_LIST)} commissioni/comitati totali. ---")
        return final_deputies
    except FileNotFoundError as e:
        print(f"ERRORE CRITICO: File di dati non trovato: {e.filename}. Impossibile caricare i dati.")
        return []

def get_all_groups(deputies_list):
    if not deputies_list: return []
    groups = set(d['simple_group'] for d in deputies_list)
    return sorted(list(groups))

# --- CARICAMENTO DATI GLOBALE ---
DEPUTIES_DATA = load_deputies_data()

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

# --- ENDPOINT PER LE COMMISSIONI (ora ordinato) ---
@app.route('/api/committees')
def get_committees():
    # Aggiunge "Tutte" in cima alla lista già ordinata
    return jsonify(['Tutte'] + COMMITTEE_FILTER_LIST)

if __name__ == '__main__':
    if not DEPUTIES_DATA:
        print("\nImpossibile avviare il server locale: nessun dato caricato.")
    else:
        print("\nServer modalità Allenamento pronto per lo sviluppo locale.")
        print("Apri il browser su http://12V7.0.0.1:5000")
        app.run(host='0.0.0.0', port=5000)