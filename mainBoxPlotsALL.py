import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import statsmodels.formula.api as smf
from scipy.stats import ttest_ind
from matplotlib.lines import Line2D
import warnings
warnings.filterwarnings('ignore')

# Configure fonts
plt.rcParams['font.sans-serif'] = ['Arial', 'Segoe UI Emoji', 'Tahoma', 'DejaVu Sans']

# ==========================================
# CONFIGURATION & MAPPINGS
# ==========================================

GENERATE_PLOTS = True
DEBUG_MODE = False 
REMOVE_OUTLIERS = True
GENERATE_SECONDARY_PLOTS = False

START_DATE = "2026-06-30" 
END_DATE = None            

# 1. Notification Types
NOTIFICATION_TYPES = {
    '1': 'Earcon',
    '2': 'Short Speech',
    '3': 'Rich Speech'
}

SCENARIO_MAPPING = {
    'A': {'Social': 'Alone',       'Task': 'High mental',   'Soundscape': 'Quiet'},  
    'B': {'Social': 'Interactive', 'Task': 'High mental',   'Soundscape': 'Speech'}, 
    'C': {'Social': 'Alone',       'Task': 'Low',           'Soundscape': 'Music'},  
    'D': {'Social': 'Interactive', 'Task': 'High physical', 'Soundscape': 'Music'},  
    'E': {'Social': 'Passive',     'Task': 'High physical', 'Soundscape': 'Quiet'},  
    'F': {'Social': 'Passive',     'Task': 'Low',           'Soundscape': 'Speech'}, 
    'G': {'Social': 'Alone',       'Task': 'High physical', 'Soundscape': 'Speech'}, 
    'H': {'Social': 'Passive',     'Task': 'High mental',   'Soundscape': 'Music'},  
    'I': {'Social': 'Interactive', 'Task': 'Low',           'Soundscape': 'Quiet'},  
}

IV_PROPS = {
    'Asocial': {
        'order': ['Alone', 'Interactive', 'Passive'], 
        'palette': {'Alone': '#6baed6', 'Interactive': '#3182bd', 'Passive': '#08519c'}, 
        'label': r"$A_{SOCIAL}$ (Social Setting)",
        'title_name': 'Social Setting'
    },
    'e_Task': {
        'order': ['High mental', 'Low', 'High physical'], 
        'palette': {'High mental': '#fd8d3c', 'Low': '#e6550d', 'High physical': '#a63603'}, 
        'label': r"$E_{TASK}$ (Task Load)",
        'title_name': 'Task Load'
    },
    'CM': {
        'order': ['Music', 'Quiet', 'Speech'], 
        'palette': {'Music': '#74c476', 'Quiet': '#31a354', 'Speech': '#006d2c'}, 
        'label': r"$C_M$ (Sound Masking)",
        'title_name': 'Sound Masking'
    }
}

DV_Y_LABELS = {
    'Social_Acceptability': [
        "Completely unacceptable (1)", "Unacceptable (2)", "Somewhat unacceptable (3)",
        "Neither acceptable nor unacceptable (4)", "Somewhat acceptable (5)",
        "Acceptable (6)", "Completely acceptable (7)"
    ],
    'Disruption': [
        "Not disruptive at all (1)", "Slightly disruptive (2)", "Somewhat disruptive (3)",
        "Moderately disruptive (4)", "Disruptive (5)", "Very disruptive (6)",
        "Extremely disruptive (7)"
    ],
    'Detectability': [
        "Very difficult to detect (1)", "Difficult to detect (2)", "Somewhat difficult to detect (3)",
        "Neither easy nor difficult to detect (4)", "Somewhat easy to detect (5)",
        "Easy to detect (6)", "Very easy to detect (7)"
    ],
    'Appropriateness': [
        "Completely inappropriate (1)", "Inappropriate (2)", "Somewhat inappropriate (3)",
        "Neither appropriate nor inappropriate (4)", "Somewhat appropriate (5)",
        "Appropriate (6)", "Completely appropriate (7)"
    ]
}

TITLE_EMOJIS = {
    'Earcon': 'Earcon (\U0001f514)',
    'Short Speech': 'Short Speech (\U0001f5e3)',
    'Rich Speech': 'Rich Speech (\U0001f5e3 \U0001f5e3)',
    'Overall': 'Overall Average (\U0001f4c8)' # Chart emoji für den Gesamtschnitt
}

LIKERT_MAP = {
    "Very difficult to detect": 1, "Difficult to detect": 2, "Somewhat difficult to detect": 3,
    "Neither easy nor difficult to detect": 4, "Somewhat easy to detect": 5, "Easy to detect": 6, "Very easy to detect": 7,
    "Not disruptive at all": 1, "Slightly disruptive": 2, "Somewhat disruptive": 3,
    "Moderately disruptive": 4, "Disruptive": 5, "Very disruptive": 6, "Extremely disruptive": 7,
    "Completely unacceptable": 1, "Unacceptable": 2, "Somewhat unacceptable": 3,
    "Neither acceptable nor unacceptable": 4, "Somewhat acceptable": 5, "Acceptable": 6, 
    "Completely acceptable": 7, "Completely Acceptable": 7, "Completel Acceptable": 7,
    "Completely inappropriate": 1, "Inappropriate": 2, "Somewhat inappropriate": 3,
    "Neither appropriate nor inappropriate": 4, "Somewhat appropriate": 5, "Appropriate": 6,
    "Completely appropriate": 7
}

RELATIONSHIPS = [
    {'iv': 'Asocial', 'dv': 'Social_Acceptability', 'is_primary': True},
    {'iv': 'e_Task', 'dv': 'Disruption', 'is_primary': True},
    {'iv': 'CM', 'dv': 'Detectability', 'is_primary': True},
    {'iv': 'Asocial', 'dv': 'Disruption', 'is_primary': False},
    {'iv': 'Asocial', 'dv': 'Detectability', 'is_primary': False},
    {'iv': 'e_Task', 'dv': 'Social_Acceptability', 'is_primary': False},
    {'iv': 'e_Task', 'dv': 'Detectability', 'is_primary': False},
    {'iv': 'CM', 'dv': 'Social_Acceptability', 'is_primary': False},
    {'iv': 'CM', 'dv': 'Disruption', 'is_primary': False},
]

# ==========================================
# FUNCTIONS
# ==========================================

def load_and_filter_data(data_path, outliers_path, start_date=START_DATE, end_date=END_DATE, remove_outliers=REMOVE_OUTLIERS):
    print("Loading data...")
    df = pd.read_excel(data_path)
    raw_count = len(df)
    
    df['RecordedDate'] = pd.to_datetime(df['RecordedDate'], errors='coerce', format='mixed')
    if start_date: df = df[df['RecordedDate'] >= pd.to_datetime(start_date)]
    if end_date: df = df[df['RecordedDate'] <= pd.to_datetime(end_date)]
        
    post_date_count = len(df)
    date_removed_count = raw_count - post_date_count
    
    removed_outliers_count = 0
    if remove_outliers:
        if os.path.exists(outliers_path):
            with open(outliers_path, 'r') as f:
                outliers = [line.strip() for line in f if line.strip()]
            removed_outliers_count = df['ResponseId'].isin(outliers).sum()
            df = df[~df['ResponseId'].isin(outliers)]
            print(f"Excluded {removed_outliers_count} outliers.")
            
    stats = {
        'raw_original': raw_count,
        'date_removed': date_removed_count,
        'post_date': post_date_count,
        'outliers_removed': removed_outliers_count,
        'final': len(df)
    }
    return df, stats

def find_column(columns, sc_key, keyword, t_id):
    keyword_lower = keyword.lower()
    for col in columns:
        col_str = str(col)
        if col_str.startswith(f"{sc_key}.") and keyword_lower in col_str.lower() and col_str.endswith(f"_{t_id}"):
            return col_str
    return None

def transform_to_long_format(df):
    print("Transforming dataset...")
    long_data = []
    df.columns = [str(c).replace('\xa0', ' ').strip() for c in df.columns]

    for _, row in df.iterrows():
        response_id = row.get('ResponseId', 'Unknown')
        for sc_key, sc_attrs in SCENARIO_MAPPING.items():
            for t_id, t_name in NOTIFICATION_TYPES.items():
                
                col_detect = find_column(df.columns, sc_key, 'detect', t_id)
                col_disrupt = find_column(df.columns, sc_key, 'disrupt', t_id)
                col_social = find_column(df.columns, sc_key, 'social', t_id)
                col_approp = find_column(df.columns, sc_key, 'appropriateness', t_id)

                val_detect = row.get(col_detect, pd.NA) if col_detect else pd.NA
                val_disrupt = row.get(col_disrupt, pd.NA) if col_disrupt else pd.NA
                val_social = row.get(col_social, pd.NA) if col_social else pd.NA
                val_approp = row.get(col_approp, pd.NA) if col_approp else pd.NA
                
                if isinstance(val_detect, str): val_detect = LIKERT_MAP.get(val_detect.strip(), val_detect)
                if isinstance(val_disrupt, str): val_disrupt = LIKERT_MAP.get(val_disrupt.strip(), val_disrupt)
                if isinstance(val_social, str): val_social = LIKERT_MAP.get(val_social.strip(), val_social)
                if isinstance(val_approp, str): val_approp = LIKERT_MAP.get(val_approp.strip(), val_approp)

                if pd.isna(val_detect) and pd.isna(val_disrupt) and pd.isna(val_social):
                    continue

                long_data.append({
                    'ResponseId': response_id,
                    'Notification_Type': t_name,
                    'Scenario': sc_key,
                    'Asocial': sc_attrs['Social'],
                    'e_Task': sc_attrs['Task'],
                    'CM': sc_attrs['Soundscape'],
                    'Detectability': pd.to_numeric(val_detect, errors='coerce'),
                    'Disruption': pd.to_numeric(val_disrupt, errors='coerce'),
                    'Social_Acceptability': pd.to_numeric(val_social, errors='coerce'),
                    'Appropriateness': pd.to_numeric(val_approp, errors='coerce')
                })

    return pd.DataFrame(long_data)

def add_debug_overlay(ax, df, x_col):
    n_total = len(df)
    counts = df[x_col].value_counts().to_dict()
    debug_text = f"DEBUG MODE: ON\nTotal n = {n_total}\n" + "-"*15 + "\n"
    debug_text += "\n".join([f"{k}: {v}" for k, v in counts.items()])
    ax.text(0.98, 0.02, debug_text, transform=ax.transAxes, 
            fontsize=9, fontfamily='monospace',
            verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', alpha=0.9, edgecolor='red', linewidth=1.5))

def create_boxplots(long_df):
    os.makedirs("plots", exist_ok=True)
    plot_count = 36 if GENERATE_SECONDARY_PLOTS else 12 # 4 Plots pro Beziehung (3 Typen + 1 Overall)
    print(f"\nGenerating {plot_count} plots with mean values...")
    sns.set_theme(style="whitegrid")
    ticks_1_to_7 = [1, 2, 3, 4, 5, 6, 7]

    # Wir fügen 'Overall' als vierte Kategorie zur Schleife hinzu
    types_to_plot = list(NOTIFICATION_TYPES.values()) + ['Overall']

    for t_name in types_to_plot:
        
        # Für 'Overall' filtern wir NICHT nach dem Typ, sondern nehmen alle Daten
        if t_name == 'Overall':
            type_df = long_df.copy()
        else:
            type_df = long_df[long_df['Notification_Type'] == t_name]
            
        if type_df.empty: continue
            
        t_title = TITLE_EMOJIS.get(t_name, t_name)

        for rel in RELATIONSHIPS:
            iv, dv, is_primary = rel['iv'], rel['dv'], rel['is_primary']
            if not GENERATE_SECONDARY_PLOTS and not is_primary: continue
            
            plot_df = type_df.dropna(subset=[dv])
            if plot_df.empty: continue

            iv_config = IV_PROPS[iv]
            
            plt.figure(figsize=(9, 6))
            
            if t_name == 'Earcon':
                meanprops={"marker":"o", "markerfacecolor":"#ffb000", "markeredgecolor":"black", "markersize":"9"}
            elif t_name == 'Short Speech':
                meanprops={"marker":"s", "markerfacecolor":"#c466ff", "markeredgecolor":"black", "markersize":"9"}
            elif t_name == 'Rich Speech':
                meanprops={"marker":"^", "markerfacecolor":"#6a0dad", "markeredgecolor":"black", "markersize":"9"}
            else:
                meanprops={"marker":"X", "markerfacecolor":"white", "markeredgecolor":"black", "markersize":"8"}

            ax = sns.boxplot(
                data=plot_df, x=iv, y=dv, 
                order=iv_config['order'], palette=iv_config['palette'],
                showmeans=True, meanprops=meanprops
            )
            
            means = plot_df.groupby(iv)[dv].mean()
            stds = plot_df.groupby(iv)[dv].std()
            
            for tick, label in enumerate(iv_config['order']):
                if label in means.index:
                    mean_val = means[label]
                    std_val = stds[label]
                    ax.text(tick, 7.2, f"M={mean_val:.2f}\nSD={std_val:.2f}", 
                            horizontalalignment='center', size='small', color='black', weight='bold')

            plt.title(f"{t_title}: {dv.replace('_', ' ')} by {iv_config['title_name']}", fontsize=14, fontname='Segoe UI Emoji')
            plt.xlabel(iv_config['label'], fontsize=12)
            plt.ylabel(dv.replace('_', ' '), fontsize=12)
            
            plt.yticks(ticks=ticks_1_to_7, labels=DV_Y_LABELS.get(dv, ticks_1_to_7), fontsize=10)
            plt.ylim(0.5, 7.7)
            
            if DEBUG_MODE: add_debug_overlay(ax, plot_df, iv)

            plt.tight_layout()
            plot_type_label = "Primary" if is_primary else "Secondary"
            filename = os.path.join("plots", f"{plot_type_label}_{t_name.replace(' ', '')}_{iv}_vs_{dv.replace(' ', '')}.png")
            plt.savefig(filename, dpi=300)
            plt.close()

            # --- NEW ADVANCED PLOT LOGIC ---
            if is_primary and t_name == 'Overall':
                plt.figure(figsize=(9, 6))
                
                y_max = 7.7
                if iv in ['e_Task', 'Asocial', 'CM']:
                    y_max = 8.8 # Make room for bars
                    
                ax_adv = sns.boxplot(
                    data=plot_df, x=iv, y=dv, 
                    order=iv_config['order'], palette=iv_config['palette'],
                    showmeans=False, meanprops=meanprops
                )
                
                # Plot individual means for Earcon, Short Speech, Rich Speech
                types_order = ['All', 'Earcon', 'Short Speech', 'Rich Speech']
                type_markers = {'All': 'X', 'Earcon': 'o', 'Short Speech': 's', 'Rich Speech': '^'}
                type_colors = {'All': 'white', 'Earcon': '#ffb000', 'Short Speech': '#c466ff', 'Rich Speech': '#6a0dad'}
                type_offsets = {'All': -0.3, 'Earcon': -0.1, 'Short Speech': 0.1, 'Rich Speech': 0.3}
                
                for tick, label in enumerate(iv_config['order']):
                    label_df = plot_df[plot_df[iv] == label]
                    for n_type in types_order:
                        if n_type == 'All':
                            type_mean = label_df[dv].mean()
                        else:
                            type_mean = label_df[label_df['Notification_Type'] == n_type][dv].mean()
                            
                        if pd.notna(type_mean):
                            ax_adv.scatter(tick + type_offsets[n_type], type_mean, 
                                           marker=type_markers[n_type], color=type_colors[n_type], 
                                           s=80, edgecolors='black', zorder=5, alpha=0.9)

                # Add Significance Bars
                def add_stat_annotation(ax, x1, x2, y, h, text):
                    ax.plot([x1, x1, x2, x2], [y, y+h, y+h, y], lw=1.5, c='k')
                    ax.text((x1+x2)*.5, y+h, text, ha='center', va='bottom', color='k', weight='bold')

                LMM_RESULTS = {
                    'Disruption': {
                        'Asocial': {('Alone', 'Passive'): '*', ('Alone', 'Interactive'): 'ns'},
                        'e_Task': {('High mental', 'Low'): '***', ('High mental', 'High physical'): '***'},
                        'CM': {('Music', 'Quiet'): '***', ('Music', 'Speech'): '***'}
                    },
                    'Social_Acceptability': {
                        'Asocial': {('Alone', 'Passive'): 'ns', ('Alone', 'Interactive'): '***'},
                        'e_Task': {('High mental', 'Low'): '***', ('High mental', 'High physical'): '***'},
                        'CM': {('Music', 'Quiet'): '***', ('Music', 'Speech'): '***'}
                    },
                    'Detectability': {
                        'Asocial': {('Alone', 'Passive'): '**', ('Alone', 'Interactive'): '**'},
                        'e_Task': {('High mental', 'Low'): 'ns', ('High mental', 'High physical'): '***'},
                        'CM': {('Music', 'Quiet'): '***', ('Music', 'Speech'): '***'}
                    }
                }

                labels = iv_config['order']
                sig_height = 7.7
                step = 0.5
                
                if dv in LMM_RESULTS and iv in LMM_RESULTS[dv]:
                    sig_dict = LMM_RESULTS[dv][iv]
                    for (g1, g2), sig_text in sig_dict.items():
                        if g1 in labels and g2 in labels:
                            i = labels.index(g1)
                            j = labels.index(g2)
                            if i > j:
                                i, j = j, i
                            
                            add_stat_annotation(ax_adv, i, j, sig_height, 0.1, sig_text)
                            sig_height += step
                            y_max = max(y_max, sig_height + 0.4)

                for tick, label in enumerate(iv_config['order']):
                    if label in means.index:
                        mean_val = means[label]
                        std_val = stds[label]
                        ax_adv.text(tick, 7.3, f"M={mean_val:.2f}\nSD={std_val:.2f}", 
                                horizontalalignment='center', verticalalignment='center', size='small', color='black', weight='bold')

                plt.title(f"Advanced {t_title}: {dv.replace('_', ' ')} by {iv_config['title_name']}", fontsize=14, fontname='Segoe UI Emoji')
                plt.xlabel(iv_config['label'], fontsize=12)
                plt.ylabel(dv.replace('_', ' '), fontsize=12)
                
                plt.yticks(ticks=ticks_1_to_7, labels=DV_Y_LABELS.get(dv, ticks_1_to_7), fontsize=10)
                plt.ylim(0.5, y_max)
                
                plt.tight_layout()
                filename_adv = os.path.join("plots", f"PrimaryAdvanced_Overall_{iv}_vs_{dv.replace(' ', '')}.png")
                plt.savefig(filename_adv, dpi=300)
                plt.close()
                
                # Save Standalone Legend
                fig_leg = plt.figure(figsize=(3, 2))
                legend_elements = [Line2D([0], [0], marker=type_markers[t], color='w', label=t, 
                                          markerfacecolor=type_colors[t], markersize=9, markeredgecolor='black') 
                                   for t in types_order]
                fig_leg.legend(handles=legend_elements, loc='center', title="Notification Types")
                fig_leg.savefig(os.path.join("plots", "PrimaryAdvanced_Legend_Standalone.png"), dpi=300, bbox_inches='tight')
                plt.close(fig_leg)
            # --- END NEW ADVANCED PLOT LOGIC ---

def main():
    data_file = 'data.xlsx'
    outliers_file = 'listOfManuallyIdentifiedOutliers.txt'

    df, stats = load_and_filter_data(data_file, outliers_file)
    long_df = transform_to_long_format(df)
    
    if GENERATE_PLOTS:
        create_boxplots(long_df)
    else:
        print("\nSkipping plot generation.")

    print("\n" + "="*50)
    print("PLOTS GENERATED SUCCESSFULLY")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()