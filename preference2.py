import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import json

# 1. Ensure Output Folders Exist
os.makedirs('reasonPlots', exist_ok=True)

# 2. Configuration & Dictionaries
colors_dict = {
    'Earcon (V1)': '#D4AC0D',        
    'Short Speech (V2)': '#BB8FCE',  
    'Rich Speech (V3)': '#6A1B9A',   
    'None / No Audio': '#CCCCCC'     
}

scenario_names = {
    'A': '1 - Home Alone Computer',
    'B': '7 - Team Meeting',
    'C': '2 - Home Music',
    'D': '9 - Tent',
    'E': '6 - Cycle City',
    'F': '5 - Grocery Shopping',
    'G': '3 - Cooking Dinner',
    'H': '4 - Study Coffee Shop',
    'I': '8 - Quiet Friend Over'
}

# 3. Helper Functions
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
    if 'nan' in x_str or pd.isna(x) or str(x).strip() == '': return 'Unknown'
    return 'Delayed' # Groups 'Specific_Delay' and 'Other' into Delayed

def extract_reasons(text):
    """Safely extracts reasons using substrings to avoid issues with commas inside parentheses"""
    if pd.isna(text): return []
    t_lower = str(text).lower()
    reasons = []
    if 'acoustic' in t_lower: reasons.append('Acoustic')
    if 'focus' in t_lower: reasons.append('Focus')
    if 'social' in t_lower: reasons.append('Social')
    if 'safety' in t_lower: reasons.append('Safety')
    if 'information' in t_lower or 'desire' in t_lower: reasons.append('Info')
    if 'other' in t_lower: reasons.append('Other')
    return reasons

# Column finder to safely match columns regardless of non-breaking spaces
def find_col(df, pattern):
    for c in df.columns:
        clean_c = " ".join(str(c).split()) # Normalize spaces
        if clean_c == pattern: return c
    return None

# Plotting Function for Grouped, Stacked, and Hatched Bars
def plot_reason_mapping(df_plot, title, filename):
    reasons = ['Acoustic', 'Focus', 'Social', 'Safety', 'Info', 'Other']
    versions = ['Earcon (V1)', 'Short Speech (V2)', 'Rich Speech (V3)', 'None / No Audio']
    
    # Filter to reasons actually present in data
    active_reasons = [r for r in reasons if r in df_plot['Short_Reason'].values]
    if not active_reasons: return # Skip if no data
    
    x = np.arange(len(active_reasons))
    width = 0.35
    
    bottom_imm = np.zeros(len(active_reasons))
    bottom_del = np.zeros(len(active_reasons))
    
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    
    for v in versions:
        imm_counts = []
        del_counts = []
        
        for r in active_reasons:
            subset = df_plot[(df_plot['Short_Reason'] == r) & (df_plot['Resolved_Version'] == v)]
            imm_counts.append(len(subset[subset['Macro_Timing'] == 'Immediate']))
            del_counts.append(len(subset[subset['Macro_Timing'] == 'Delayed']))
            
        # Draw Immediate Bars (Solid)
        bars_imm = ax.bar(x - width/2 - 0.02, imm_counts, width, label=v, bottom=bottom_imm, 
                          color=colors_dict[v], edgecolor='black', linewidth=0.8)
        
        # Draw Delayed Bars (Hatched)
        bars_del = ax.bar(x + width/2 + 0.02, del_counts, width, bottom=bottom_del, 
                          color=colors_dict[v], edgecolor='black', linewidth=0.8, hatch='///')
        
        # Add text labels inside bars if count > 0
        for i, (b_imm, b_del) in enumerate(zip(bars_imm, bars_del)):
            if imm_counts[i] > 0:
                ax.text(b_imm.get_x() + b_imm.get_width()/2, bottom_imm[i] + imm_counts[i]/2, 
                        str(imm_counts[i]), ha='center', va='center', color='white', fontweight='bold', fontsize=9)
            if del_counts[i] > 0:
                ax.text(b_del.get_x() + b_del.get_width()/2, bottom_del[i] + del_counts[i]/2, 
                        str(del_counts[i]), ha='center', va='center', color='white', fontweight='bold', fontsize=9)
                
        bottom_imm += np.array(imm_counts)
        bottom_del += np.array(del_counts)
        
    ax.set_xticks(x)
    ax.set_xticklabels(active_reasons, fontsize=11)
    ax.set_ylabel('Number of Occurrences', fontsize=12)
    ax.set_title(title, fontsize=14, pad=15)
    
    # Custom Legend
    legend_elements = [
        mpatches.Patch(facecolor=colors_dict['Earcon (V1)'], edgecolor='black', label='Earcon (V1)'),
        mpatches.Patch(facecolor=colors_dict['Short Speech (V2)'], edgecolor='black', label='Short Speech (V2)'),
        mpatches.Patch(facecolor=colors_dict['Rich Speech (V3)'], edgecolor='black', label='Rich Speech (V3)'),
        mpatches.Patch(facecolor=colors_dict['None / No Audio'], edgecolor='black', label='None / No Audio'),
        mpatches.Patch(facecolor='white', edgecolor='white', label=' '), # Spacer
        mpatches.Patch(facecolor='#E0E0E0', edgecolor='black', label='Timing: Immediate'),
        mpatches.Patch(facecolor='#E0E0E0', edgecolor='black', hatch='///', label='Timing: Delayed')
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1), title="Preferences", title_fontsize=11)
    
    plt.tight_layout()
    plt.savefig(f'reasonPlots/{filename}.png')
    plt.close()

# 4. Main Execution
print("Loading data.xlsx...")
try:
    df = pd.read_excel('data.xlsx', header=0)
    # Qualtrics specific: Remove the sub-header description row if it exists
    if 'Start Date' in str(df.iloc[0, 0]) or 'Start Date' in str(df.iloc[0, 1]):
        df = df.iloc[1:].reset_index(drop=True)
except Exception as e:
    print(f"Error loading Excel file: {e}")
    exit()

json_output = {}
all_scenarios_data = [] # For the aggregate plot

scenes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']

for scene in scenes:
    print(f"Processing Scenario {scene}...")
    
    col_overall = find_col(df, f"{scene}. Overall")
    col_why = find_col(df, f"{scene}. Overall Why")
    col_timing = find_col(df, f"{scene}. Timing")
    col_follow = find_col(df, f"{scene}. Timing Follow")
    
    if not all([col_overall, col_why, col_timing]):
        print(f"Skipping {scene} - Couldn't find required columns.")
        continue
        
    df_scene = df[[col_overall, col_why, col_timing]].copy()
    if col_follow: df_scene[col_follow] = df[col_follow]
    else: df_scene['Timing Follow'] = None
    
    df_scene = df_scene.dropna(subset=[col_overall])
    
    # Clean standard columns
    df_scene['Clean_Overall'] = df_scene[col_overall].apply(clean_version)
    df_scene['Macro_Timing'] = df_scene[col_timing].apply(get_timing_cat)
    df_scene['Clean_Timing_Follow'] = df_scene[col_follow].apply(clean_version) if col_follow else None
    
    # Resolve Final Decision
    def resolve(row):
        if row['Macro_Timing'] == 'Immediate': return row['Clean_Overall']
        else:
            if pd.notna(row['Clean_Timing_Follow']) and str(row['Clean_Timing_Follow']).lower() != 'nan':
                return row['Clean_Timing_Follow']
            return row['Clean_Overall']
            
    df_scene['Resolved_Version'] = df_scene.apply(resolve, axis=1)
    df_scene['Resolved_Version'] = df_scene['Resolved_Version'].replace({'N/A': 'None / No Audio', 'nan': 'None / No Audio', None: 'None / No Audio'})
    
    # Extract & Explode Reasons
    df_scene['Reason_List'] = df_scene[col_why].apply(extract_reasons)
    df_exploded = df_scene.explode('Reason_List').dropna(subset=['Reason_List'])
    df_exploded = df_exploded.rename(columns={'Reason_List': 'Short_Reason'})
    
    # Append to master dataset for aggregate plot
    all_scenarios_data.append(df_exploded)
    
    # Generate Plot
    title = f"Impact of Contextual Reasons on Preferences\n(Scenario {scenario_names[scene]})"
    plot_reason_mapping(df_exploded, title, f"Scenario_{scene}_Reason_Mapping")
    
    # Save to JSON structure
    scene_key = f"Scenario_{scenario_names[scene].replace(' ', '_')}"
    json_output[scene_key] = {}
    
    grouped = df_exploded.groupby(['Short_Reason', 'Macro_Timing', 'Resolved_Version']).size().reset_index(name='Count')
    for r in grouped['Short_Reason'].unique():
        json_output[scene_key][r] = {"Immediate": {}, "Delayed": {}}
        subset = grouped[grouped['Short_Reason'] == r]
        for t in ['Immediate', 'Delayed']:
            sub_t = subset[subset['Macro_Timing'] == t]
            for _, row in sub_t.iterrows():
                json_output[scene_key][r][t][row['Resolved_Version']] = int(row['Count'])

# 5. Generate Aggregate Master Plot
print("\nGenerating Aggregate Master Plot across all Scenarios...")
if all_scenarios_data:
    df_all = pd.concat(all_scenarios_data, ignore_index=True)
    plot_reason_mapping(df_all, "Impact of Contextual Reasons on Preferences\n(Aggregated Across ALL Scenarios)", "ALL_Scenarios_Aggregated_Reason_Mapping")

# 6. Save JSON
json_filepath = 'reasonPlots/Reasons_to_Preferences_Mapping.json'
with open(json_filepath, 'w', encoding='utf-8') as f:
    json.dump(json_output, f, indent=4)

print(f"Finished! Plots and JSON mapped data saved to the 'reasonPlots' folder.")