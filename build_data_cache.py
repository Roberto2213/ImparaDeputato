import json
import re
import requests
import time
import os

# --- CONFIGURAZIONE ---
LEGISLATURA = 19
SPARQL_ENDPOINT = "https://dati.camera.it/sparql"
OUTPUT_FILE = 'data_cache.json'
URL_EMICICLO_CAMERA = "https://www.camera.it/deputati/"

# --- FUNZIONI DI UTILITÀ ---

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

def load_seat_map():
    """Scarica la mappa dei seggi dinamicamente dal sito della Camera e la indicizza per ID"""
    seat_map = {}
    print(f"📡 Scaricamento mappa seggi in tempo reale da {URL_EMICICLO_CAMERA}...")
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}
        response = requests.get(URL_EMICICLO_CAMERA, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Cerchiamo la variabile JS 'var deputati = [...];' nel codice della pagina
        match = re.search(r'var\s+deputati\s*=\s*(\[.*?\]);', response.text, re.DOTALL)
        if match:
            deputati_json_str = match.group(1)
            deputati_data = json.loads(deputati_json_str)
            
            for dep in deputati_data:
                # Estraiamo l'ID numerico ufficiale del deputato e il suo posto
                dep_id = str(dep.get("idAulDeputato", ""))
                posto = str(dep.get("posto", ""))
                
                if dep_id and posto and posto != "None":
                    seat_map[dep_id] = posto
        else:
            print("⚠️ Variabile 'var deputati' non trovata nella pagina della Camera.")
            
    except Exception as e:
        print(f"⚠️ Errore durante il recupero dei seggi: {e}")
        
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
            print(f"⏳ Esecuzione query SPARQL (Tentativo {attempt + 1}/{max_retries}). Attendere prego...")
            response = requests.get(SPARQL_ENDPOINT, params={"query": query}, headers=headers, timeout=120)
            response.raise_for_status() 
            print("✅ Dati scaricati con successo!")
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code in [500, 502, 503, 504]:
                print(f"⚠️ I server della Camera hanno risposto con errore {status_code}.")
                if attempt < max_retries - 1:
                    print(f"Riprovo tra {delay_seconds} secondi...")
                    time.sleep(delay_seconds)
            else:
                raise Exception(f"Errore fatale nella query: HTTP {status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Errore di rete: {e}")
            if attempt < max_retries - 1:
                print(f"Riprovo tra {delay_seconds} secondi...")
                time.sleep(delay_seconds)

    raise Exception("\n❌ Impossibile scaricare i dati. I server di dati.camera.it potrebbero essere offline o sovraccarichi.")

# --- FUNZIONE PRINCIPALE DI COSTRUZIONE CACHE ---

def build_cache():
    print("="*50)
    print("🚀 AVVIO AGGIORNAMENTO DATI IMPARA DEPUTATO")
    print("="*50)
    
    # 1. SCARICA LA MAPPA DEI SEGGI (Indicizzata per ID Deputato)
    seat_map = load_seat_map()
    print(f"🪑 Mappa seggi generata: {len(seat_map)} postazioni trovate sul sito ufficiale.")
    
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
        
        # Estraiamo l'ID numerico dall'URI SPARQL (es: da .../d308825 estrae 308825)
        match_id = re.search(r'd(\d+)', uri)
        dep_id = match_id.group(1) if match_id else None
        
        cognome = row.get("cognome", {}).get("value", "").title()
        nome = row.get("nome", {}).get("value", "").title()
        full_name = f"{cognome} {nome}"
        
        # Usiamo l'ID Deputato come chiave primaria del dizionario per raggruppare i record
        dict_key = dep_id if dep_id else full_name
        
        if dict_key not in deputies_dict:
            gruppo_raw = row.get("nomeGruppo", {}).get("value", "Misto")
            
            # Recuperiamo il posto esatto usando l'ID
            assigned_seat = seat_map.get(dep_id, "N/D") if dep_id else "N/D"
            
            deputies_dict[dict_key] = {
                "name": full_name,
                "photo_url": build_new_photo_url(uri, LEGISLATURA),
                "group": gruppo_raw,
                "simple_group": normalize_group_name(gruppo_raw),
                "status": "in_carica",
                "gender": row.get("genere", {}).get("value", "N/D"),
                "constituency": row.get("collegio", {}).get("value", "N/D"),
                "committees": set(),
                "seat": assigned_seat
            }
            
        # Aggiungiamo le commissioni
        commissione = row.get("commissione", {}).get("value")
        if commissione:
            clean_comm = commissione.strip()
            deputies_dict[dict_key]["committees"].add(clean_comm)
            all_committees.add(clean_comm)

    # Convertiamo il dizionario in lista ordinata per il JSON finale
    final_deputies = []
    for info in deputies_dict.values():
        info["committees"] = sorted(list(info["committees"]))
        final_deputies.append(info)
    
    # Ordine alfabetico per nome
    final_deputies.sort(key=lambda x: x['name'])

    committee_filter_list = get_sorted_committees(all_committees)

    # Salvataggio del JSON finale
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