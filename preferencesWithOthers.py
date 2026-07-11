import pandas as pd
import numpy as np
import os
import json

# 1. Output Folder erstellen (falls noch nicht vorhanden)
os.makedirs('preferencePlots', exist_ok=True)

# 2. Hilfsfunktionen zum Bereinigen (wie im Original)
def clean_version(x):
    if pd.isna(x): return x
    x_str = str(x)
    if 'No audio' in x_str: return 'None / No Audio'
    if 'Version 1' in x_str: return 'Earcon (V1)'
    if 'Version 2' in x_str: return 'Short Speech (V2)'
    if 'Version 3' in x_str: return 'Rich Speech (V3)'
    if 'Not applicable' in x_str: return 'N/A' 
    return x

def get_timing_cat(x):
    x_str = str(x).lower()
    if 'immediat' in x_str: return 'Immediate'
    if 'other' in x_str: return 'Other'
    return 'Specific_Delay'

def resolve_version(row):
    cat = row['Timing_Cat']
    overall = row['Clean_Overall']
    follow = row['Clean_Timing_Follow']
    
    if cat == 'Immediate':
        return overall
    else:
        if pd.notna(follow) and follow != 'N/A' and str(follow).lower() != 'nan':
            return follow
        else:
            return overall

# 3. Namen & Mapping definieren
scenario_names = {
    'A': 'Home Alone Computer',
    'B': 'Team Meeting',
    'C': 'Home Music',
    'D': 'Tent',
    'E': 'Cycle City',
    'F': 'Grocery Shopping',
    'G': 'Cooking Dinner',
    'H': 'Study Coffee Shop',
    'I': 'Quiet Friend Over'
}

scenario_mapping = {
    'A': '1', 'B': '7', 'C': '2', 'D': '9', 'E': '6', 
    'F': '5', 'G': '3', 'H': '4', 'I': '8'
}

# 4. Schleife über alle Szenarien um "Other" Responses zu sammeln
scenes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
json_other_data = {}

for scene in scenes:
    scene_num = scenario_mapping[scene]
    scene_key = f"Scene_{scene_num}_{scenario_names[scene].replace(' ', '_')}"
    
    # Standardmäßig eine leere Liste für dieses Szenario anlegen
    json_other_data[scene_key] = []
    
    try:
        # Daten laden
        df_pref = pd.read_csv(f'preferenceData/scene{scene}_preference.csv')
        df_delay = pd.read_csv(f'preferenceData/scene{scene}_delay.csv')
        
        # Daten mergen
        merged = df_pref.merge(df_delay, on='Participant ID', how='outer')
        
        merged['Clean_Overall'] = merged['Overall'].apply(clean_version)
        merged['Clean_Timing_Follow'] = merged['Timing Follow'].apply(clean_version)
        merged['Raw_Timing'] = merged['Timing'].fillna('Unknown')
        merged['Timing_Cat'] = merged['Raw_Timing'].apply(get_timing_cat)
        
        merged['Resolved_Version'] = merged.apply(resolve_version, axis=1)
        merged['Resolved_Version'] = merged['Resolved_Version'].replace({'N/A': 'None / No Audio', 'nan': 'None / No Audio', None: 'None / No Audio'})
        
        # ==========================================
        # NUR "OTHER" DATEN EXTRAHIEREN
        # ==========================================
        df_other = merged[merged['Timing_Cat'] == 'Other'].copy()
        
        # Suche nach zusätzlichen Text-Spalten (oft bei Qualtrics als "Timing_4_TEXT" o.ä. benannt),
        # um sicherzugehen, dass wir die tatsächliche Begründung nicht verpassen.
        text_cols = [col for col in merged.columns if 'text' in col.lower() or 'other' in col.lower()]
        
        scene_other_list = []
        for _, row in df_other.iterrows():
            record = {
                "Participant_ID": row.get('Participant ID', 'Unknown'),
                "Resolved_Version": row['Resolved_Version'],
                "Raw_Timing_Choice": str(row['Raw_Timing'])
            }
            
            # Alle potenziellen Freitextfelder anhängen
            for col in text_cols:
                val = row[col]
                if pd.notna(val) and str(val).strip() != '':
                    record[col] = str(val)
                    
            scene_other_list.append(record)
            
        json_other_data[scene_key] = scene_other_list
        print(f"Szenario {scene_num}: {len(scene_other_list)} 'Other'-Antwort(en) gefunden.")

    except FileNotFoundError:
        print(f"Dateien für Scene {scene} nicht gefunden. Überspringe...")
    except Exception as e:
        print(f"Fehler bei Scene {scene}: {e}")

# ==========================================
# 5. JSON DATEI SPEICHERN
# ==========================================
out_filepath = 'preferencePlots/other_responses_to_classify.json'
with open(out_filepath, 'w', encoding='utf-8') as f:
    json.dump(json_other_data, f, indent=4)

print(f"\nFertig! Die 'Other'-Gründe wurden extrahiert und in '{out_filepath}' gespeichert.")