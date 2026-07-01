import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Configure fonts to properly render emojis (falling back to Segoe UI Emoji on Windows)
plt.rcParams['font.sans-serif'] = ['Arial', 'Segoe UI Emoji', 'Tahoma', 'DejaVu Sans']

# ==========================================
# CONFIGURATION & MAPPINGS
# ==========================================

# Toggle this flag to show/hide sample sizes and debug info on the generated plots
DEBUG_MODE = False 

# Toggle this flag to exclude/include predefined outliers from the text file
REMOVE_OUTLIERS = True

# Toggle this flag to generate the extra 18 exploratory plots (Secondary Mappings)
GENERATE_SECONDARY_PLOTS = True

# Date Filtering Range (Format: 'YYYY-MM-DD' or None)
START_DATE = "2026-06-30"  # Includes this date and later
END_DATE = None            # Set to a date string to cap the range (e.g., "2026-07-02"), or leave as None

# 1. Notification Types
NOTIFICATION_TYPES = {
    '1': 'Earcon',
    '2': 'Short Speech',
    '3': 'Rich Speech'
}

# 2. Scenario Definitions (Corrected to 3x3x3 Orthogonal Design)
SCENARIO_MAPPING = {
    'A': {'Social': 'Alone',       'Task': 'High mental',   'Soundscape': 'Quiet'},  # Desk coding
    'B': {'Social': 'Interactive', 'Task': 'High mental',   'Soundscape': 'Speech'}, # Team meeting
    'C': {'Social': 'Alone',       'Task': 'Low',           'Soundscape': 'Music'},  # Relaxing at home
    'D': {'Social': 'Interactive', 'Task': 'High physical', 'Soundscape': 'Music'},  # Setting up tent 
    'E': {'Social': 'Passive',     'Task': 'High physical', 'Soundscape': 'Quiet'},  # Cycling street
    'F': {'Social': 'Passive',     'Task': 'Low',           'Soundscape': 'Speech'}, # Grocery shopping
    'G': {'Social': 'Alone',       'Task': 'High physical', 'Soundscape': 'Speech'}, # Cooking + Podcast
    'H': {'Social': 'Passive',     'Task': 'High mental',   'Soundscape': 'Music'},  # Study Coffee Shop
    'I': {'Social': 'Interactive', 'Task': 'Low',           'Soundscape': 'Quiet'},  # Quiet Friend over
}

# 3. Independent Variable Properties for Plotting
IV_PROPS = {
    'Asocial': {
        'order': ['Alone', 'Interactive', 'Passive'], 
        'palette': {'Alone': '#6baed6', 'Interactive': '#3182bd', 'Passive': '#08519c'}, 
        'label': r"$A_{SOCIAL}$ (Social Setting)",
        'title_name': 'Social Setting'
    },
    'e-Task': {
        'order': ['Low', 'High mental', 'High physical'], 
        'palette': {'Low': '#fd8d3c', 'High mental': '#e6550d', 'High physical': '#a63603'}, 
        'label': r"$E_{TASK}$ (Task Load)",
        'title_name': 'Task Load'
    },
    'CM': {
        'order': ['Quiet', 'Music', 'Speech'], 
        'palette': {'Quiet': '#74c476', 'Music': '#31a354', 'Speech': '#006d2c'}, 
        'label': r"$C_M$ (Sound Masking)",
        'title_name': 'Sound Masking'
    }
}

# 4. Dependent Variable Labels for Plotting
DV_Y_LABELS = {
    'Social Acceptability': [
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
    ]
}

# Emojis for titles
TITLE_EMOJIS = {
    'Earcon': 'Earcon (\U0001f514)',
    'Short Speech': 'Short Speech (\U0001f5e3)',
    'Rich Speech': 'Rich Speech (\U0001f5e3 \U0001f5e3)'
}

# 5. Likert text to numeric conversion mapping
LIKERT_MAP = {
    "Very difficult to detect": 1, "Difficult to detect": 2, "Somewhat difficult to detect": 3,
    "Neither easy nor difficult to detect": 4, "Somewhat easy to detect": 5, "Easy to detect": 6, "Very easy to detect": 7,
    "Not disruptive at all": 1, "Slightly disruptive": 2, "Somewhat disruptive": 3,
    "Moderately disruptive": 4, "Disruptive": 5, "Very disruptive": 6, "Extremely disruptive": 7,
    "Completely unacceptable": 1, "Unacceptable": 2, "Somewhat unacceptable": 3,
    "Neither acceptable nor unacceptable": 4, "Somewhat acceptable": 5, "Acceptable": 6, 
    "Completely acceptable": 7, "Completely Acceptable": 7, "Completel Acceptable": 7
}

# Define the relationships mapping (IV -> DV)
RELATIONSHIPS = [
    # Primary Mappings
    {'iv': 'Asocial', 'dv': 'Social Acceptability', 'is_primary': True},
    {'iv': 'e-Task', 'dv': 'Disruption', 'is_primary': True},
    {'iv': 'CM', 'dv': 'Detectability', 'is_primary': True},
    # Secondary Mappings (Social Setting)
    {'iv': 'Asocial', 'dv': 'Disruption', 'is_primary': False},
    {'iv': 'Asocial', 'dv': 'Detectability', 'is_primary': False},
    # Secondary Mappings (Task Load)
    {'iv': 'e-Task', 'dv': 'Social Acceptability', 'is_primary': False},
    {'iv': 'e-Task', 'dv': 'Detectability', 'is_primary': False},
    # Secondary Mappings (Soundscape)
    {'iv': 'CM', 'dv': 'Social Acceptability', 'is_primary': False},
    {'iv': 'CM', 'dv': 'Disruption', 'is_primary': False},
]

# ==========================================
# FUNCTIONS
# ==========================================

def load_and_filter_data(data_path, outliers_path, start_date=START_DATE, end_date=END_DATE, remove_outliers=REMOVE_OUTLIERS):
    """Reads data, filters by date, handles outliers, and returns stats."""
    print("Loading data...")
    df = pd.read_excel(data_path)
    
    # Grab the absolute raw count before doing anything
    raw_count = len(df)
    
    df['RecordedDate'] = pd.to_datetime(df['RecordedDate'], errors='coerce', format='mixed')
    
    if start_date: df = df[df['RecordedDate'] >= pd.to_datetime(start_date)]
    if end_date: df = df[df['RecordedDate'] <= pd.to_datetime(end_date)]
        
    post_date_count = len(df)
    date_removed_count = raw_count - post_date_count
    
    range_str = f"from {start_date or 'beginning'} to {end_date or 'latest'}"
    print(f"Data remaining after date filtering ({range_str}): {post_date_count} rows.")

    removed_outliers_count = 0

    if remove_outliers:
        if os.path.exists(outliers_path):
            with open(outliers_path, 'r') as f:
                outliers = [line.strip() for line in f if line.strip()]
            
            # Count exactly how many of these outliers were actually in our post-date-filtered data
            removed_outliers_count = df['ResponseId'].isin(outliers).sum()
            df = df[~df['ResponseId'].isin(outliers)]
            print(f"Excluded {removed_outliers_count} outliers from the dataset.")
        else:
            print(f"Outlier file '{outliers_path}' not found. Skipping outlier exclusion.")
    else:
        print("Outlier exclusion is DISABLED via global flag. Keeping all data points.")
        
    stats = {
        'raw_original': raw_count,
        'date_removed': date_removed_count,
        'post_date': post_date_count,
        'outliers_removed': removed_outliers_count,
        'final': len(df)
    }
        
    return df, stats

def find_column(columns, sc_key, keyword, t_id):
    """Fuzzy matching to bypass Qualtrics' non-breaking spaces and slight typos."""
    keyword_lower = keyword.lower()
    for col in columns:
        col_str = str(col)
        if col_str.startswith(f"{sc_key}.") and keyword_lower in col_str.lower() and col_str.endswith(f"_{t_id}"):
            return col_str
    return None

def transform_to_long_format(df):
    """Transforms the wide Qualtrics dataset into a long format suitable for seaborn."""
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

                val_detect = row.get(col_detect, pd.NA) if col_detect else pd.NA
                val_disrupt = row.get(col_disrupt, pd.NA) if col_disrupt else pd.NA
                val_social = row.get(col_social, pd.NA) if col_social else pd.NA
                
                if isinstance(val_detect, str): val_detect = LIKERT_MAP.get(val_detect.strip(), val_detect)
                if isinstance(val_disrupt, str): val_disrupt = LIKERT_MAP.get(val_disrupt.strip(), val_disrupt)
                if isinstance(val_social, str): val_social = LIKERT_MAP.get(val_social.strip(), val_social)

                if pd.isna(val_detect) and pd.isna(val_disrupt) and pd.isna(val_social):
                    continue

                long_data.append({
                    'ResponseId': response_id,
                    'Notification_Type': t_name,
                    'Scenario': sc_key,
                    'Asocial': sc_attrs['Social'],
                    'e-Task': sc_attrs['Task'],
                    'CM': sc_attrs['Soundscape'],
                    'Detectability': pd.to_numeric(val_detect, errors='coerce'),
                    'Disruption': pd.to_numeric(val_disrupt, errors='coerce'),
                    'Social Acceptability': pd.to_numeric(val_social, errors='coerce')
                })

    return pd.DataFrame(long_data)

def add_debug_overlay(ax, df, x_col):
    """Helper function to draw the debug text box on a plot."""
    n_total = len(df)
    counts = df[x_col].value_counts().to_dict()
    
    debug_text = f"DEBUG MODE: ON\nTotal n = {n_total}\n" + "-"*15 + "\n"
    debug_text += "\n".join([f"{k}: {v}" for k, v in counts.items()])
    
    ax.text(0.98, 0.02, debug_text, transform=ax.transAxes, 
            fontsize=9, fontfamily='monospace',
            verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', alpha=0.9, edgecolor='red', linewidth=1.5))

def create_boxplots(long_df):
    """Generates and saves the set of boxplots based on configuration toggles."""
    # Ensure plots directory exists
    os.makedirs("plots", exist_ok=True)
    
    plot_count = 27 if GENERATE_SECONDARY_PLOTS else 9
    print(f"Generating {plot_count} plots...")
    sns.set_theme(style="whitegrid")
    ticks_1_to_7 = [1, 2, 3, 4, 5, 6, 7]

    for t_id, t_name in NOTIFICATION_TYPES.items():
        type_df = long_df[long_df['Notification_Type'] == t_name]
        
        if type_df.empty:
            print(f"Warning: No data found for {t_name}. Skipping its plots.")
            continue
            
        t_title = TITLE_EMOJIS.get(t_name, t_name)

        # Iterate over combinations of IVs and DVs
        for rel in RELATIONSHIPS:
            iv = rel['iv']
            dv = rel['dv']
            is_primary = rel['is_primary']
            
            # Skip secondary plots if the flag is turned off
            if not GENERATE_SECONDARY_PLOTS and not is_primary:
                continue
            
            plot_df = type_df.dropna(subset=[dv])
            
            if plot_df.empty:
                print(f"Warning: Skipping plot ({iv} vs {dv}) for {t_name}: No valid data found.")
                continue

            iv_config = IV_PROPS[iv]
            
            plt.figure(figsize=(9, 6))
            ax = sns.boxplot(
                data=plot_df, x=iv, y=dv, 
                order=iv_config['order'], palette=iv_config['palette']
            )
            
            # Use the clean, human-readable title_name
            plt.title(f"{t_title}: {dv} by {iv_config['title_name']}", fontsize=14, fontname='Segoe UI Emoji')
            plt.xlabel(iv_config['label'], fontsize=12)
            plt.ylabel(dv, fontsize=12)
            
            plt.yticks(ticks=ticks_1_to_7, labels=DV_Y_LABELS[dv], fontsize=10)
            plt.ylim(0.5, 7.5)
            
            if DEBUG_MODE:
                add_debug_overlay(ax, plot_df, iv)

            plt.tight_layout()
            
            plot_type_label = "Primary" if is_primary else "Secondary"
            filename = os.path.join("plots", f"{plot_type_label}_{t_name.replace(' ', '')}_{iv}_vs_{dv.replace(' ', '')}.png")
            plt.savefig(filename, dpi=300)
            plt.close()

def main():
    data_file = 'data.xlsx'
    outliers_file = 'listOfManuallyIdentifiedOutliers.txt'

    df, stats = load_and_filter_data(data_file, outliers_file)
    long_df = transform_to_long_format(df)
    create_boxplots(long_df)

    # Final summary printout
    print("\n" + "="*50)
    print("DATA PROCESSING SUMMARY")
    print("="*50)
    print(f"Raw responses loaded:                      {stats['raw_original']}")
    print(f"Responses removed by date filter:          {stats['date_removed']}")
    print(f"Responses remaining before outlier check:  {stats['post_date']}")
    print(f"Responses removed as outliers:             {stats['outliers_removed']}")
    print(f"Final valid participants analyzed:         {stats['final']}")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()