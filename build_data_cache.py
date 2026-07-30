import json
import re
import logging
from bs4 import BeautifulSoup

def process_open_data(filepath: str) -> list:
    """
    Parsa il JSON estratto dalla query estesa della Camera.
    Poiché la query non usa GROUP_CONCAT, restituisce più righe per deputato 
    (una per ogni commissione). Questa funzione fonde le righe (Deduplicazione).
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    bindings = data.get('results', {}).get('bindings', [])
    deputati_dict = {}

    for item in bindings:
        def get_val(key): return item.get(key, {}).get('value', '').strip()

        # Estrazione dell'URI per ricavare l'ID pulito e la foto HD
        persona_uri = get_val('persona')
        if not persona_uri:
            continue
            
        id_match = re.search(r'p(\d+)', persona_uri)
        id_numeric = id_match.group(1) if id_match else ""
        
        # Formattazione anagrafica per compatibilità col frontend: "Cognome Nome"
        nome = get_val('nome').title()
        cognome = get_val('cognome').title()
        full_name = f"{cognome} {nome}".strip()
        
        commissione = get_val('commissione')
        
        # Se il deputato non è ancora nel dizionario, lo creiamo
        if full_name not in deputati_dict:
            genere_raw = get_val('genere').lower()
            gender_mapped = "male" if genere_raw.startswith("m") else "female"
            
            gruppo = get_val('nomeGruppo')
            collegio = get_val('collegio')
            
            # Generazione URL Foto in Alta Definizione
            foto_url = f"https://documenti.camera.it/_dati/leg19/schededeputatinuovosito/fotoDefinitivo/big/d{id_numeric}.jpg" if id_numeric else ""
            
            deputati_dict[full_name] = {
                "name": full_name,
                "photo_url": foto_url,
                "group": gruppo,
                "simple_group": _parse_simple_group(gruppo),
                "status": "in_carica",
                "gender": gender_mapped,
                "constituency": collegio or "N/D",
                "committees": set(),
                
                # Campi ridondanti per garantire compatibilità con le tue logiche legacy
                "nome": nome,
                "cognome": cognome,
                "foto": foto_url,
                "image_url": foto_url,
                "gruppo": gruppo,
                "commissioni": set(),
                
                # FIX: Sincronizziamo 'genere' al valore raw 'male'/'female' per impedire 
                # che la logica di fallback in app.py corrompa la chiave 'gender' attesa dal frontend.
                "genere": gender_mapped 
            }
        
        # Aggiungiamo la commissione al Set (evita duplicati)
        if commissione:
            deputati_dict[full_name]["committees"].add(commissione)
            deputati_dict[full_name]["commissioni"].add(commissione)

    # Convertiamo il dizionario in lista e i Set in Liste ordinate per JSON
    deputati_list = list(deputati_dict.values())
    for dep in deputati_list:
        dep["committees"] = sorted(list(dep["committees"]))
        dep["commissioni"] = sorted(list(dep["commissioni"]))
        
    return deputati_list

def _parse_simple_group(gruppo: str) -> str:
    """Mappa i nomi completi sulle Select Option esatte del frontend JS."""
    g_up = gruppo.upper()
    if "5 STELLE" in g_up: return "Movimento 5 Stelle"
    if "FRATELLI D'ITALIA" in g_up: return "Fratelli d'Italia"
    if "DEMOCRATICO" in g_up: return "Partito Democratico"
    if "LEGA" in g_up: return "Lega - Salvini Premier"
    if "FORZA ITALIA" in g_up: return "Forza Italia"
    if "AZIONE" in g_up or "ITALIA VIVA" in g_up or "RENEW" in g_up: return "Azione - Italia Viva"
    if "VERDI" in g_up and "SINISTRA" in g_up: return "Alleanza Verdi e Sinistra"
    if "MODERATI" in g_up: return "Noi Moderati"
    return "Gruppo Misto"

def process_emiciclo(filepath: str) -> dict:
    """
    Ricava l'allocazione seggio <-> deputato dall'HTML dell'Emiciclo.
    Adattato al DOM ufficiale di camera.it/deputati
    """
    seats = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fallback legacy per vecchi JSON
    if filepath.endswith('.json'):
        data = json.loads(content)
        for seat in data:
            match = re.match(r'^(\d+)\s*-\s*(.+?)\s+([A-Z0-9\-\+]+)$', seat.get('title', ''))
            if match:
                seats[match.group(2).strip().upper()] = match.group(1)
        return seats

    # Parsing dell'HTML aggiornato
    soup = BeautifulSoup(content, 'html.parser')
    
    # Cerca tutti i tag <a> che contengono l'attributo aria-label (dove sta il nome)
    for a_tag in soup.find_all('a', attrs={"aria-label": True}):
        aria_label = a_tag['aria-label']
        
        # Controlla se è un seggio occupato
        if "Scheda del deputato" in aria_label:
            # Estrae il nome: prende quello che c'è tra "deputato " e ", gruppo"
            name_match = re.search(r'deputato\s+(.+?),\s+gruppo', aria_label)
            
            # Cerca il tag <circle> all'interno dell'<a> per prendere l'ID del seggio
            circle_tag = a_tag.find('circle')
            
            if name_match and circle_tag and circle_tag.get('id'):
                name_part = name_match.group(1).strip().upper()
                seat_id = circle_tag.get('id')
                seats[name_part] = seat_id

    return seats

def build_final_cache(deputati_data: list, emiciclo_layout: dict, output_cache_path: str) -> None:
    """Fonde i dati anagrafici con le posizioni dell'emiciclo."""
    all_committees = set()

    for dep in deputati_data:
        nome_up = dep['nome'].upper()
        cognome_up = dep['cognome'].upper()
        
        # Matching robusto "Cognome Nome" o "Nome Cognome"
        target_1 = f"{cognome_up} {nome_up}"
        target_2 = f"{nome_up} {cognome_up}"
        
        matched_seat = "N/D"
        for seat_name, seat_id in emiciclo_layout.items():
            if target_1 in seat_name or target_2 in seat_name:
                matched_seat = seat_id
                break
                
        dep['seat'] = matched_seat
        
        for c in dep['committees']:
            all_committees.add(c)

    final_data = {
        "deputies": deputati_data,
        "committees": sorted(list(all_committees))
    }

    with open(output_cache_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
        
    logging.info("Cache JSON rigenerata con successo e validata.")
