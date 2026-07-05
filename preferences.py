import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import textwrap
import json

# 1. Output Folder erstellen
os.makedirs('preferencePlots', exist_ok=True)

# 2. Hilfsfunktionen zum Bereinigen
def clean_version(x):
    if pd.isna(x): return x
    x_str = str(x)
    if 'No audio' in x_str: return 'None / No Audio'
    if 'Version 1' in x_str: return 'Earcon (V1)'
    if 'Version 2' in x_str: return 'Short Speech (V2)'
    if 'Version 3' in x_str: return 'Rich Speech (V3)'
    if 'Not applicable' in x_str: return 'N/A' 
    return x

# Dynamische Erkennung der Timing-Kategorie
def get_timing_cat(x):
    x_str = str(x).lower()
    if 'immediat' in x_str: return 'Immediate'
    if 'other' in x_str: return 'Other'
    return 'Specific_Delay'

# Bereinigungslogik ("The Core Decision")
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

# 3. Farben, Namen & Mapping definieren
colors_dict = {
    'Earcon (V1)': '#D4AC0D',        
    'Short Speech (V2)': '#BB8FCE',  
    'Rich Speech (V3)': '#6A1B9A',   
    'None / No Audio': '#CCCCCC'     
}

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

# 4. Schleife über alle Szenarien + JSON-Daten-Sammler
scenes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
json_output_data = {}

for scene in scenes:
    scene_num = scenario_mapping[scene]
    scene_key = f"Scene_{scene_num}_{scenario_names[scene].replace(' ', '_')}"
    
    json_output_data[scene_key] = {
        "original_letter": scene,
        "scenario_name": scenario_names[scene],
        "macro_timing": {},
        "micro_timing_delayed_breakdown": {}
    }
    
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
        
        # Version finalisieren
        merged['Resolved_Version'] = merged.apply(resolve_version, axis=1)
        merged['Resolved_Version'] = merged['Resolved_Version'].replace({'N/A': 'None / No Audio', 'nan': 'None / No Audio', None: 'None / No Audio'})
        
        # Macro Timing zuweisen
        merged['Macro_Timing'] = merged['Timing_Cat'].apply(lambda x: 'Immediate' if x == 'Immediate' else ('Delayed' if x in ['Specific_Delay', 'Other'] else 'Unknown'))
        
        # ==========================================
        # MACRO-DATEN EXTRAHIEREN UND PLOTTEN
        # ==========================================
        macro_data = merged.groupby(['Macro_Timing', 'Resolved_Version']).size().reset_index(name='Count')
        pivot_macro = macro_data.pivot(index='Macro_Timing', columns='Resolved_Version', values='Count').fillna(0)
        
        for idx in ['Immediate', 'Delayed']:
            if idx not in pivot_macro.index:
                pivot_macro.loc[idx] = 0
                
        pivot_macro = pivot_macro.reindex(['Immediate', 'Delayed'])
        v_cols = [c for c in ['Earcon (V1)', 'Short Speech (V2)', 'Rich Speech (V3)', 'None / No Audio'] if c in pivot_macro.columns]
        pivot_macro = pivot_macro[v_cols]
        
        # ---> JSON: Macro-Daten speichern <---
        for timing_cat in ['Immediate', 'Delayed']:
            if timing_cat in pivot_macro.index:
                row_dict = {k: int(v) for k, v in pivot_macro.loc[timing_cat].to_dict().items()}
                row_dict["Total"] = int(pivot_macro.loc[timing_cat].sum())
                json_output_data[scene_key]["macro_timing"][timing_cat] = row_dict
        
        colors = [colors_dict[c] for c in v_cols]
        
        fig, ax = plt.subplots(figsize=(5, 6), dpi=300) 
        if not pivot_macro.empty and len(v_cols) > 0:
            pivot_macro.plot(kind='bar', stacked=True, color=colors, ax=ax, edgecolor='black', linewidth=0.8, legend=False)
            for c in ax.containers:
                ax.bar_label(c, label_type='center', color='white', fontsize=10, fontweight='bold',
                             labels=[f"{int(v.get_height())}" if v.get_height() > 0 else "" for v in c])
            totals = pivot_macro.sum(axis=1)
            for i, total in enumerate(totals):
                ax.text(i, total + 0.5, f"n={int(total)}", ha='center', fontweight='bold')
            plt.ylim(0, max(totals.max() + 3, 5)) 
            
        plt.title(f'Immediate vs. Delayed Delivery\n(Scene {scene_num}: {scenario_names[scene]})', fontsize=13, pad=15)
        plt.xlabel('Delivery Timing Decision', fontsize=12)
        plt.ylabel('Number of Participants', fontsize=12)
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig(f'preferencePlots/Scene{scene_num}_Immediate_vs_Delayed.png')
        plt.close()
        
        # ==========================================
        # MIKRO-DATEN (DELAYED) EXTRAHIEREN UND PLOTTEN
        # ==========================================
        delayed_only = merged[merged['Macro_Timing'] == 'Delayed'].copy()
        if not delayed_only.empty:
            
            def format_label(text, cat):
                if cat == 'Other': return 'Other'
                return textwrap.fill(str(text), width=18)
                
            delayed_only['Plot_Label'] = delayed_only.apply(lambda r: format_label(r['Raw_Timing'], r['Timing_Cat']), axis=1)
            # Speichere auch den Raw-Text für das JSON
            delayed_only['Raw_Label_For_Json'] = delayed_only.apply(lambda r: 'Other' if r['Timing_Cat'] == 'Other' else str(r['Raw_Timing']), axis=1)
            
            unique_labels = delayed_only['Plot_Label'].unique().tolist()
            if 'Other' in unique_labels: unique_labels.remove('Other')
            unique_labels.sort(key=len) 
            delay_order = unique_labels + (['Other'] if 'Other' in delayed_only['Plot_Label'].values else [])
            
            delayed_data = delayed_only.groupby(['Plot_Label', 'Resolved_Version']).size().reset_index(name='Count')
            pivot_delayed = delayed_data.pivot(index='Plot_Label', columns='Resolved_Version', values='Count').fillna(0)
            pivot_delayed = pivot_delayed.reindex(delay_order).dropna(how='all')
            
            if not pivot_delayed.empty:
                v_cols_del = [c for c in ['Earcon (V1)', 'Short Speech (V2)', 'Rich Speech (V3)', 'None / No Audio'] if c in pivot_delayed.columns]
                pivot_delayed = pivot_delayed[v_cols_del]
                
                # ---> JSON: Mikro-Daten speichern <---
                # Wir mappen Plot_Label zurück auf den originalen String für bessere JSON-Lesbarkeit
                label_mapping = dict(zip(delayed_only['Plot_Label'], delayed_only['Raw_Label_For_Json']))
                for plot_label in pivot_delayed.index:
                    original_string = label_mapping.get(plot_label, plot_label)
                    row_dict = {k: int(v) for k, v in pivot_delayed.loc[plot_label].to_dict().items()}
                    row_dict["Total"] = int(pivot_delayed.loc[plot_label].sum())
                    json_output_data[scene_key]["micro_timing_delayed_breakdown"][original_string] = row_dict

                colors_del = [colors_dict[c] for c in v_cols_del]
                
                fig2, ax2 = plt.subplots(figsize=(6.5, 6), dpi=300)
                pivot_delayed.plot(kind='bar', stacked=True, color=colors_del, ax=ax2, edgecolor='black', linewidth=0.8, legend=False)
                
                for c in ax2.containers:
                    ax2.bar_label(c, label_type='center', color='white', fontsize=10, fontweight='bold',
                                 labels=[f"{int(v.get_height())}" if v.get_height() > 0 else "" for v in c])
                
                plt.title(f'Breakdown of Delayed Timing\n(Scene {scene_num}: {scenario_names[scene]})', fontsize=13, pad=15)
                plt.xlabel('Specific Delay Timing', fontsize=12)
                plt.ylabel('Number of Participants', fontsize=12)
                plt.xticks(rotation=0)
                plt.tight_layout()
                plt.savefig(f'preferencePlots/Scene{scene_num}_Delayed_Breakdown.png')
                plt.close()
                
        print(f"Erfolgreich verarbeitet: Scene {scene_num} (Daten von Scene {scene}).")
        
    except FileNotFoundError:
        print(f"Dateien für Scene {scene} nicht gefunden. Überspringe...")
    except Exception as e:
        print(f"Fehler bei Scene {scene}: {e}")

# ==========================================
# 5. STANDALONE LEGENDE GENERIEREN
# ==========================================
fig_leg, ax_leg = plt.subplots(figsize=(3, 2), dpi=300)
ax_leg.axis('off')
legend_patches = [mpatches.Patch(color=color, label=label, ec='black', lw=0.8) 
                  for label, color in colors_dict.items()]
ax_leg.legend(handles=legend_patches, title='Preferred Version', loc='center')
plt.tight_layout()
plt.savefig('preferencePlots/Legend_Standalone.png', bbox_inches='tight')
plt.close()

# ==========================================
# 6. JSON DATEI SPEICHERN
# ==========================================
json_filepath = 'preferencePlots/scenario_preferences_summary.json'
with open(json_filepath, 'w', encoding='utf-8') as f:
    json.dump(json_output_data, f, indent=4)

print(f"\nFertig! Alle Plots und das JSON-File ('{json_filepath}') wurden im Ordner 'preferencePlots' gespeichert!")