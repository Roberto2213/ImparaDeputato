import csv
import re
import unicodedata
import json
import os
from rdflib import Graph, URIRef, RDF, RDFS
from bs4 import BeautifulSoup

# --- FUNZIONI DI UTILITÀ ---

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

def load_seat_map(canonical_key_func):
    seat_map = {}
    file_path = 'static/emiciclo.html'
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        
        seats = soup.select('a[id^="seggio_"][title*=" - "]')
        for seat in seats:
            try:
                title_text = seat['title']
                seat_number = title_text.split(' - ')[0].strip()
                name_and_group = title_text.split(' - ')[1]
                name_str = name_and_group.rsplit(' ', 1)[0].strip()
                key = canonical_key_func(name_str)
                if key:
                    seat_map[key] = seat_number
            except Exception:
                continue
    except FileNotFoundError:
        print(f"ATTENZIONE: File '{file_path}' non trovato.")
    except Exception as e:
        print(f"Errore durante la lettura di '{file_path}': {e}")
    return seat_map

def get_sorted_committees(all_committee_names):
    roman_numeral_pattern = re.compile(r'^[IVXLC]+\s+COMMISSIONE')
    p1_roman = []
    p2_bicameral = []
    p3_giunte = []
    p4_inchiesta = []
    p5_others = []

    for name in all_committee_names:
        if not name: continue
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
            p5_others.append(clean_name)
            
    return (sorted(p1_roman) + sorted(p2_bicameral) + 
            sorted(p3_giunte) + sorted(p4_inchiesta) + sorted(p5_others))

def load_additional_data(canonical_key_func):
    additional_data_map = {}
    all_committee_names_set = set()
    file_path = 'sparql (1).csv'
    
    try:
        with open(file_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                name_str = f"{row['cognome']} {row['nome']}"
                key = canonical_key_func(name_str)
                
                if not key: continue
                
                if key not in additional_data_map:
                    additional_data_map[key] = {
                        "committees": set(),
                        "constituency": row.get('collegio', 'N/D'),
                        "gender": row.get('genere', 'N/D')
                    }
                
                committee_name = row.get('commissione')
                if committee_name:
                    clean_name = committee_name.strip()
                    if clean_name:
                        additional_data_map[key]["committees"].add(clean_name)
                        all_committee_names_set.add(clean_name)
        
        # Convert sets to lists for JSON serialization
        for key, data in additional_data_map.items():
            data['committees'] = sorted(list(data['committees']))
            
        return additional_data_map, all_committee_names_set

    except FileNotFoundError:
        print(f"ATTENZIONE: File '{file_path}' non trovato.")
        return {}, set()

# --- FUNZIONE PRINCIPALE DI COSTRUZIONE ---

def build_cache():
    print("Avvio costruzione cache dati...")
    
    alias_map = load_alias_map()
    additional_data_map, all_committee_names = load_additional_data(create_canonical_key)
    seat_map = load_seat_map(create_canonical_key)
    committee_filter_list = get_sorted_committees(all_committee_names)
    
    # Parsing RDF
    print("Parsing file RDF (potrebbe richiedere qualche secondo)...")
    g = Graph()
    try:
        g.parse("deputato-19.txt", format="nt")
    except FileNotFoundError:
        print("ERRORE: File 'deputato-19.txt' non trovato.")
        return

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

    # Unione Dati
    final_deputies = []
    print("Unione dati da Nominativo,Gruppo.csv...")
    try:
        with open('Nominativo,Gruppo.csv', mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            next(reader)
            for row in reader:
                if len(row) < 2: continue
                full_name, group = row[0], ",".join(row[1:])
                
                # Gestione Status Cessato
                status = "in_carica"
                if "cessato" in full_name.lower() or "cessato" in group.lower():
                    status = "cessato"
                
                clean_name = full_name.split('(')[0].strip()
                key = create_canonical_key(clean_name)
                
                if key in rdf_deputies:
                    deputy_info = rdf_deputies[key]
                    deputy_info['name'] = clean_name
                    deputy_info['group'] = group
                    deputy_info['simple_group'] = normalize_group_name(group)
                    deputy_info['status'] = status
                    
                    additional_data = additional_data_map.get(key, {})
                    deputy_info['committees'] = additional_data.get('committees', [])
                    deputy_info['constituency'] = additional_data.get('constituency', 'N/D')
                    deputy_info['gender'] = additional_data.get('gender', 'N/D')
                    deputy_info['seat'] = seat_map.get(key, 'N/D')
                    
                    final_deputies.append(deputy_info)
    except FileNotFoundError:
        print("ERRORE: File 'Nominativo,Gruppo.csv' non trovato.")
        return

    # Salvataggio su JSON
    cache_data = {
        "deputies": final_deputies,
        "committees": committee_filter_list
    }
    
    with open('data_cache.json', 'w', encoding='utf-8') as outfile:
        json.dump(cache_data, outfile, ensure_ascii=False, indent=2)
        
    print(f"SUCCESS: Cache costruita in 'data_cache.json'.")
    print(f"Totale Deputati: {len(final_deputies)}")
    print(f"Totale Commissioni: {len(committee_filter_list)}")

if __name__ == "__main__":
    build_cache()