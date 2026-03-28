import json
import re
import requests
import unicodedata
import time
import os
from bs4 import BeautifulSoup

# --- CONFIGURAZIONE ---
LEGISLATURA = 19
SPARQL_ENDPOINT = "https://dati.camera.it/sparql"
OUTPUT_FILE = 'data_cache.json'

# --- FUNZIONI DI UTILITÀ ---

def create_canonical_key(name_str):
    """Crea una chiave univoca dal nome per evitare duplicati"""
    nfkd_form = unicodedata.normalize('NFKD', name_str)
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    cleaned_str = re.sub('[^a-zA-Z ]', '', only_ascii).upper()
    parts = sorted(cleaned_str.split())
    return "".join(parts)

def build_new_photo_url(uri, legislatura):
    """Costruisce l'URL della foto partendo dall'URI del deputato"""
    match = re.search(r'(d\d+)', uri)
    if match:
        dep_id = match.group(1)
        return f"https://documenti.camera.it/_dati/leg{legislatura}/schededeputatinuovosito/fotoDefinitivo/big/{dep_id}.jpg"
    return None

def normalize_group_name(group_name):
    """Normalizza i nomi dei gruppi per la visualizzazione"""
    if not group_name:
        return "N/D"
    normalization_map = [
        ("FRATELLI D'ITALIA", "Fratelli d'Italia"),
        ("PARTITO DEMOCRATICO", "Partito Democratico"),
        ("LEGA", "Lega - Salvini Premier"),
        ("MOVIMENTO 5 STELLE", "Movimento 5 Stelle"),
        ("FORZA ITALIA", "Forza Italia"),
        ("AZIONE", "Azione - Italia Viva"),
        ("ITALIA VIVA", "Azione - Italia Viva"),
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

def get_sorted_committees(all_committee_names):
    """Ordina le commissioni categorizzandole correttamente"""
    roman_numeral_pattern = re.compile(r'^[IVXLC]+\s+COMMISSIONE')
    p1_roman, p2_bicameral, p3_giunte, p4_inchiesta, p5_others = [], [], [], [], []

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

def load_seat_map(canonical_key_func):
    """Legge il file HTML dell'emiciclo per mappare i seggi dei deputati"""
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
                # Prende il nome ignorando il gruppo (es. "ROSSI Mario (Misto)" -> "ROSSI Mario")
                name_str = name_and_group.rsplit(' ', 1)[0].strip()
                key = canonical_key_func(name_str)
                if key:
                    seat_map[key] = seat_number
            except Exception:
                continue
    except FileNotFoundError:
        print(f"ATTENZIONE: File '{file_path}' non trovato. I seggi non verranno mappati.")
    except Exception as e:
        print(f"Errore durante la lettura di '{file_path}': {e}")
    return seat_map

# --- RECUPERO DATI LIVE DA DATI.CAMERA.IT ---

def fetch_deputies_live(legislatura, max_retries=3, delay_seconds=5):
    """Interroga direttamente il server SPARQL della Camera per i dati più aggiornati"""
    print(f"\n📡 Connessione ai server della Camera per la legislatura {legislatura}...")
    
    query = f"""
    PREFIX ocd: <http://dati.camera.it/ocd/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?d ?persona ?cognome ?nome ?dataNascita ?nato ?luogoNascita ?genere ?collegio ?nomeGruppo ?sigla ?commissione ?aggiornamento  
    WHERE {{
        ?persona ocd:rif_mandatoCamera ?mandato; a foaf:Person.
        ## deputato
        ?d a ocd:deputato; ocd:aderisce ?aderisce;
        ocd:rif_leg <http://dati.camera.it/ocd/legislatura.rdf/repubblica_{legislatura}>;
        ocd:rif_mandatoCamera ?mandato.
        ## anagrafica
        ?d foaf:surname ?cognome; foaf:gender ?genere; foaf:firstName ?nome.
        OPTIONAL {{
            ?persona <http://purl.org/vocab/bio/0.1/Birth> ?nascita.
            ?nascita <http://purl.org/vocab/bio/0.1/date> ?dataNascita; 
            rdfs:label ?nato; ocd:rif_luogo ?luogoNascitaUri. 
            ?luogoNascitaUri dc:title ?luogoNascita. 
        }}
        ## aggiornamento del sistema
        OPTIONAL {{?d <http://lod.xdams.org/ontologies/ods/modified> ?aggiornamento.}}
        ## mandato (ESCLUDE I CESSATI tramite il MINUS endDate)
        ?mandato ocd:rif_elezione ?elezione.  
        MINUS {{?mandato ocd:endDate ?fineMandato.}}
        ## elezione
        ?elezione dc:coverage ?collegio.
        ## adesione a gruppo
        OPTIONAL {{
            ?aderisce ocd:rif_gruppoParlamentare ?gruppo.
            ?gruppo <http://purl.org/dc/terms/alternative> ?sigla.
            ?gruppo dc:title ?nomeGruppo.
        }}
        MINUS {{?aderisce ocd:endDate ?fineAdesione}}
        ## organo (commissione)
        OPTIONAL {{
            ?d ocd:membro ?membro.
            ?membro ocd:rif_organo ?organo. 
            ?organo dc:title ?commissione .
        }}
        MINUS {{?membro ocd:endDate ?fineMembership}}
    }}
    """

    headers = {"Accept": "application/sparql-results+json"}
    
    for attempt in range(max_retries):
        try:
            print(f"⏳ Esecuzione query SPARQL (Tentativo {attempt + 1}/{max_retries}). Attendere prego, potrebbe richiedere fino a un minuto...")
            # TIMEOUT AUMENTATO A 120 SECONDI
            response = requests.get(SPARQL_ENDPOINT, params={"query": query}, headers=headers, timeout=120)
            response.raise_for_status() 
            print("✅ Dati scaricati con successo!")
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code in [500, 502, 503, 504]:
                print(f"⚠️  I server della Camera hanno risposto con errore {status_code}.")
                if attempt < max_retries - 1:
                    print(f"Riprovo tra {delay_seconds} secondi...")
                    time.sleep(delay_seconds)
            else:
                raise Exception(f"Errore fatale nella query: HTTP {status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Errore di rete: {e}")
            if attempt < max_retries - 1:
                print(f"Riprovo tra {delay_seconds} secondi...")
                time.sleep(delay_seconds)

    raise Exception("\n❌ Impossibile scaricare i dati. I server di dati.camera.it potrebbero essere offline o sovraccarichi.")

# --- FUNZIONE PRINCIPALE DI COSTRUZIONE CACHE ---

def build_cache():
    print("="*50)
    print("🚀 AVVIO AGGIORNAMENTO DATI IMPARA DEPUTATO")
    print("="*50)
    
    # 1. CARICA LA MAPPA DEI SEGGI DAL FILE LOCALE HTML
    seat_map = load_seat_map(create_canonical_key)
    print(f"🪑 Mappa seggi caricata: {len(seat_map)} postazioni trovate in 'static/emiciclo.html'")
    
    # 2. SCARICA I DATI VIA SPARQL
    try:
        data = fetch_deputies_live(LEGISLATURA)
    except Exception as e:
        print(e)
        return

    bindings = data.get("results", {}).get("bindings", [])
    print(f"📦 Ricevuti {len(bindings)} record grezzi da elaborare (incluse doppie commissioni).")
    
    if len(bindings) == 0:
        print("⚠️  Nessun dato restituito! Verifica se il server Camera ha modificato le ontologie.")
        return

    deputies_dict = {}
    all_committees = set()

    for row in bindings:
        uri = row.get("d", {}).get("value", "")
        if not uri: continue
        
        cognome = row.get("cognome", {}).get("value", "").title()
        nome = row.get("nome", {}).get("value", "").title()
        full_name = f"{cognome} {nome}"
        key = create_canonical_key(full_name)
        
        # Se incontriamo il deputato per la prima volta, creiamo il suo record
        if key not in deputies_dict:
            gruppo_raw = row.get("nomeGruppo", {}).get("value", "Misto")
            
            deputies_dict[key] = {
                "name": full_name,
                "photo_url": build_new_photo_url(uri, LEGISLATURA),
                "group": gruppo_raw,
                "simple_group": normalize_group_name(gruppo_raw),
                "status": "in_carica",
                "gender": row.get("genere", {}).get("value", "N/D"),
                "constituency": row.get("collegio", {}).get("value", "N/D"),
                "committees": set(),
                # 3. ASSEGNA IL SEGGIO LEGGENDOLO DALLA MAPPA LOCALE
                "seat": seat_map.get(key, "N/D") 
            }
            
        # Aggiungiamo le commissioni (usando i set evitiamo duplicati)
        commissione = row.get("commissione", {}).get("value")
        if commissione:
            clean_comm = commissione.strip()
            deputies_dict[key]["committees"].add(clean_comm)
            all_committees.add(clean_comm)

    # Convertiamo il dizionario in lista ordinata per il JSON finale
    final_deputies = []
    for info in deputies_dict.values():
        info["committees"] = sorted(list(info["committees"]))
        final_deputies.append(info)
    
    # Ordine alfabetico per nome
    final_deputies.sort(key=lambda x: x['name'])

    committee_filter_list = get_sorted_committees(all_committees)

    # Salvataggio del JSON finale sovrascrivendo la vecchia cache
    cache_data = {
        "deputies": final_deputies,
        "committees": committee_filter_list
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        json.dump(cache_data, outfile, ensure_ascii=False, indent=2)
        
    print("\n" + "="*50)
    print("✅ ELABORAZIONE COMPLETATA CON SUCCESSO!")
    print(f"📄 Salvato su: {os.path.abspath(OUTPUT_FILE)}")
    print(f"👤 Deputati unici attualmente in carica: {len(final_deputies)}")
    print(f"🏛️  Totale Commissioni estratte: {len(committee_filter_list)}")
    print("="*50)

if __name__ == "__main__":
    build_cache()