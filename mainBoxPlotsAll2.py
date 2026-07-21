import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
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
        'label': r"$C_M$ (Soundscape)",
        'title_name': 'Soundscape'
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

# Define the specific comparisons
COMPARISON_RELATIONSHIPS = [
    {'dv': 'Disruption', 'iv': 'e_Task'},
    {'dv': 'Social_Acceptability', 'iv': 'Asocial'},
    {'dv': 'Detectability', 'iv': 'CM'}
]

# Even darker colors for the Combined across-condition plots
COMBINED_COLORS = {
    'Disruption': '#662506',           # Very dark brown
    'Social_Acceptability': '#08306b', # Very dark blue
    'Detectability': '#00441b'         # Very dark green
}

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

def create_comparison_boxplots(long_df):
    output_dir = "plots2"
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nGenerating comparison plots in '{output_dir}' directory...")
    
    sns.set_theme(style="whitegrid")
    ticks_1_to_7 = [1, 2, 3, 4, 5, 6, 7]
    notification_order = ['Earcon', 'Short Speech', 'Rich Speech']
    type_markers = {'Earcon': 'o', 'Short Speech': 's', 'Rich Speech': '^'}
    type_colors = {'Earcon': '#ffb000', 'Short Speech': '#c466ff', 'Rich Speech': '#6a0dad'}

    for rel in COMPARISON_RELATIONSHIPS:
        dv = rel['dv']
        iv = rel['iv']
        iv_config = IV_PROPS[iv]
        
        # 1. Create a separate plot for EACH sub-condition of the IV
        for condition in iv_config['order']:
            
            # Filter the dataframe for the specific condition
            plot_df = long_df[long_df[iv] == condition].dropna(subset=[dv])
            if plot_df.empty: 
                continue

            # Fetch the specific color from the original palette
            condition_color = iv_config['palette'][condition]
            
            plt.figure(figsize=(9, 6))
            
            # Plot with Notification_Type on the X-axis
            ax = sns.boxplot(
                data=plot_df, x='Notification_Type', y=dv, 
                order=notification_order, color=condition_color,
                showmeans=False
            )
            
            # Calculate means and stds to draw connections and add text
            means = plot_df.groupby('Notification_Type')[dv].mean().reindex(notification_order)
            stds = plot_df.groupby('Notification_Type')[dv].std().reindex(notification_order)
            
            # Draw a line connecting the means
            x_coords = range(len(notification_order))
            ax.plot(x_coords, means.values, color='black', linestyle='--', linewidth=1.5, zorder=4)
            
            # Add mean and std annotations, and scatter the custom markers
            for tick, t_name in enumerate(notification_order):
                if pd.notna(means[t_name]):
                    mean_val = means[t_name]
                    std_val = stds[t_name]
                    
                    # Scatter custom marker
                    ax.scatter(tick, mean_val, marker=type_markers[t_name], color=type_colors[t_name], 
                               s=90, edgecolors='black', zorder=5, alpha=1.0)
                               
                    ax.text(tick, 7.2, f"M={mean_val:.2f}\nSD={std_val:.2f}", 
                            horizontalalignment='center', size='small', color='black', weight='bold')

            # Formatting
            plt.title(f"{dv.replace('_', ' ')} by Notification Type\n({iv_config['title_name']}: {condition})", fontsize=14, fontname='Segoe UI Emoji')
            plt.xlabel("Notification Type", fontsize=12)
            plt.ylabel(dv.replace('_', ' '), fontsize=12)
            
            plt.yticks(ticks=ticks_1_to_7, labels=DV_Y_LABELS.get(dv, ticks_1_to_7), fontsize=10)
            plt.ylim(0.5, 7.7)
            
            if DEBUG_MODE: add_debug_overlay(ax, plot_df, 'Notification_Type')

            plt.tight_layout()
            
            # Save format: plots2/Disruption_HighPhysical.png
            filename = os.path.join(output_dir, f"{dv.replace('_', '')}_{condition.replace(' ', '')}.png")
            plt.savefig(filename, dpi=300)
            plt.close()

        # 2. Create the OVERALL combined plot for the current DV
        plot_df_overall = long_df.dropna(subset=[dv])
        if not plot_df_overall.empty:
            plt.figure(figsize=(9, 6))
            
            combined_color = COMBINED_COLORS[dv]
            
            ax = sns.boxplot(
                data=plot_df_overall, x='Notification_Type', y=dv, 
                order=notification_order, color=combined_color,
                showmeans=False
            )
            
            # Calculate overall means and stds
            means_overall = plot_df_overall.groupby('Notification_Type')[dv].mean().reindex(notification_order)
            stds_overall = plot_df_overall.groupby('Notification_Type')[dv].std().reindex(notification_order)
            
            # Connect the overall means
            x_coords = range(len(notification_order))
            ax.plot(x_coords, means_overall.values, color='black', linestyle='--', linewidth=1.5, zorder=4)
            
            # Add overall mean and std annotations, and scatter the custom markers
            for tick, t_name in enumerate(notification_order):
                if pd.notna(means_overall[t_name]):
                    mean_val = means_overall[t_name]
                    std_val = stds_overall[t_name]
                    
                    # Scatter custom marker
                    ax.scatter(tick, mean_val, marker=type_markers[t_name], color=type_colors[t_name], 
                               s=90, edgecolors='black', zorder=5, alpha=1.0)
                               
                    ax.text(tick, 7.2, f"M={mean_val:.2f}\nSD={std_val:.2f}", 
                            horizontalalignment='center', size='small', color='black', weight='bold')

            # --- Significance Bars (Notification Type main effect from LMM) ---
            def add_stat_annotation(ax, x1, x2, y, h, text):
                ax.plot([x1, x1, x2, x2], [y, y+h, y+h, y], lw=1.5, c='k')
                ax.text((x1+x2)*.5, y+h, text, ha='center', va='bottom', color='k', weight='bold')

            # LMM pairwise results for Notification Type (Bonferroni α = .0167)
            # Order: Earcon(0), Short Speech(1), Rich Speech(2)
            NT_LMM_RESULTS = {
                'Disruption': {(0, 1): '***', (0, 2): '***', (1, 2): '***'},
                'Social_Acceptability': {(0, 1): '***', (0, 2): '***', (1, 2): 'ns'},
                'Detectability': {(0, 1): 'ns', (0, 2): '**', (1, 2): 'ns'}
            }

            y_max = 8.0
            if dv in NT_LMM_RESULTS:
                sig_height = 8.0
                step = 0.5
                for (i, j), sig_text in NT_LMM_RESULTS[dv].items():
                    add_stat_annotation(ax, i, j, sig_height, 0.1, sig_text)
                    sig_height += step
                    y_max = max(y_max, sig_height + 0.4)

            # Formatting for combined
            plt.title(f"{dv.replace('_', ' ')} by Notification Type\n(Combined across {iv_config['title_name']}s)", fontsize=14, fontname='Segoe UI Emoji')
            plt.xlabel("Notification Type", fontsize=12)
            plt.ylabel(dv.replace('_', ' '), fontsize=12)
            
            plt.yticks(ticks=ticks_1_to_7, labels=DV_Y_LABELS.get(dv, ticks_1_to_7), fontsize=10)
            plt.ylim(0.5, y_max)
            
            if DEBUG_MODE: add_debug_overlay(ax, plot_df_overall, 'Notification_Type')

            plt.tight_layout()
            
            filename = os.path.join(output_dir, f"{dv.replace('_', '')}_Combined.png")
            plt.savefig(filename, dpi=300)
            plt.close()


def main():
    data_file = 'data.xlsx'
    outliers_file = 'listOfManuallyIdentifiedOutliers.txt'

    df, stats = load_and_filter_data(data_file, outliers_file)
    long_df = transform_to_long_format(df)
    
    if GENERATE_PLOTS:
        create_comparison_boxplots(long_df)
    else:
        print("\nSkipping plot generation.")

    print("\n" + "="*50)
    print("PLOTS GENERATED SUCCESSFULLY IN 'plots2'")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()