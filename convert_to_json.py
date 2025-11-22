import re
import json
import os
from bs4 import BeautifulSoup

# --- CONFIGURAZIONE ---
# Aumentato a 7.0 per cerchi giganti e leggibili
FATTORE_SPAZIATURA = 7.0 
# ----------------------

def parse_css_coordinates(css_path):
    coords = {}
    if not os.path.exists(css_path):
        print(f"ERRORE: Non trovo il file {css_path}")
        return coords
        
    with open(css_path, 'r') as f:
        content = f.read()
        matches = re.finditer(r'#seggio_(\d+)\s*\{[^}]*top\s*:\s*(\d+)pt;[^}]*left\s*:\s*(\d+)pt;', content)
        found = 0
        for match in matches:
            found += 1
            seggio_id = match.group(1)
            top = int(match.group(2)) * FATTORE_SPAZIATURA
            left = int(match.group(3)) * FATTORE_SPAZIATURA
            coords[seggio_id] = {'y': top, 'x': left}
        print(f"   - Trovate coordinate per {found} seggi.")
    return coords

def parse_html_metadata(html_path):
    metadata = {}
    if not os.path.exists(html_path):
        return metadata

    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        links = soup.select('#emiciclo a')
        for link in links:
            id_attr = link.get('id', '')
            if id_attr.startswith('seggio_'):
                num_id = id_attr.replace('seggio_', '')
                title = link.get('title', '')
                classes = link.get('class', [])
                
                gruppo = "Misto"
                for c in classes:
                    if c not in ['circle', 'true', 'highlighted']:
                        gruppo = c
                        break
                
                is_vacant = 'true' in classes
                metadata[num_id] = {
                    'title': title,
                    'gruppo': gruppo,
                    'is_vacant': is_vacant
                }
    return metadata

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(base_dir, 'static', 'posizioni.css')
    html_path = os.path.join(base_dir, 'static', 'emiciclo.html')
    output_path = os.path.join(base_dir, 'static', 'seggi.json')

    print(f"Generazione seggi.json con spaziatura {FATTORE_SPAZIATURA}x...")
    coords = parse_css_coordinates(css_path)
    meta = parse_html_metadata(html_path)

    if not coords:
        print("❌ ERRORE: Nessuna coordinata trovata.")
        return

    final_data = []
    for seggio_id, pos in coords.items():
        info = meta.get(seggio_id, {'title': f'Seggio {seggio_id}', 'gruppo': 'ND', 'is_vacant': False})
        final_data.append({
            'id': int(seggio_id),
            'x': pos['x'],
            'y': pos['y'],
            'title': info['title'],
            'gruppo': info['gruppo'],
            'vacante': info['is_vacant']
        })

    final_data.sort(key=lambda k: k['id'])

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ SUCCESS! File {output_path} aggiornato.")

if __name__ == "__main__":
    main()