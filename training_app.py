# training_app.py (Versione aggiornata con logica per gruppi e PWA)
import csv
import re
import unicodedata
from flask import Flask, render_template, jsonify, send_from_directory
from rdflib import Graph, URIRef, RDF, RDFS

# --- Configurazione ---
app = Flask(__name__, template_folder='templates', static_folder='static')

# --- Dati in memoria ---
DEPUTIES_DATA = []

# --- Logica di Caricamento Dati (migliorata) ---
def create_canonical_key(name_str):
    nfkd_form = unicodedata.normalize('NFKD', name_str)
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    cleaned_str = re.sub('[^a-zA-Z ]', '', only_ascii).upper()
    parts = sorted(cleaned_str.split())

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

# NUOVA FUNZIONE DI NORMALIZZAZIONE DEI GRUPPI
def normalize_group_name(group_name):
    """
    Normalizza i nomi dei gruppi parlamentari per accorparli in modo intelligente.
    Cerca delle parole chiave nel nome completo del gruppo e restituisce un nome canonico.
    """
    # Mappa di normalizzazione: (chiave da cercare, nome canonico finale)
    # L'ordine è importante: le chiavi più specifiche vanno prima.
    # La ricerca è case-insensitive.
    normalization_map = [
        ("FRATELLI D'ITALIA", "Fratelli d'Italia"),
        ("PARTITO DEMOCRATICO", "Partito Democratico"),
        ("LEGA", "Lega - Salvini Premier"),
        ("MOVIMENTO 5 STELLE", "Movimento 5 Stelle"),
        ("FORZA ITALIA", "Forza Italia"),
        ("AZIONE - ITALIA VIVA", "Azione - Italia Viva"),
        ("VERDI E SINISTRA", "Alleanza Verdi e Sinistra"),
        ("NOI MODERATI", "Noi Moderati"),
        # Il Misto deve essere tra gli ultimi, perché molti nomi lo contengono
        ("MISTO", "Gruppo Misto")
    ]

    # Converti il nome del gruppo in maiuscolo per un confronto senza distinzioni
    upper_group = group_name.upper()

    for key, canonical_name in normalization_map:
        if key in upper_group:
            return canonical_name

    # Se nessuna regola corrisponde, usa la vecchia logica di base come fallback
    simplified = re.split(r' - |–|—|\(Cessato', group_name)[0].strip()
    return simplified


def load_deputies_data():
    alias_map = load_alias_map()
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
                # MODIFICA CHIAVE: Usiamo la nuova funzione
                deputy_info['simple_group'] = normalize_group_name(group)
                final_deputies.append(deputy_info)
    
    print(f"--- Dati caricati per {len(final_deputies)} deputati. ---")
    return final_deputies

def get_all_groups(deputies_list):
    if not deputies_list: return []
    groups = set(d['simple_group'] for d in deputies_list)
    return sorted(list(groups))

# --- Endpoint Web ---
@app.route('/')
def index():
    """Serve la pagina principale del gioco di allenamento."""
    return render_template('training.html')

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('.', 'service-worker.js')

@app.route('/api/deputies')
def get_deputies():
    """Fornisce tutti i dati dei deputati in formato JSON."""
    return jsonify(DEPUTIES_DATA)

@app.route('/api/groups')
def get_groups():
    """Fornisce la lista unica e semplificata dei gruppi parlamentari."""
    groups = get_all_groups(DEPUTIES_DATA)
    return jsonify(['Tutti'] + groups)

if __name__ == '__main__':
    DEPUTIES_DATA = load_deputies_data()
    if not DEPUTIES_DATA:
        print("\nImpossibile avviare il server: nessun dato caricato.")
    else:
        print("\nServer modalità Allenamento pronto.")
        print("Apri il browser su http://127.0.0.1:5000")
        app.run(host='0.0.0.0', port=5000)