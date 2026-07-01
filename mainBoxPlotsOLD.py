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

# Ordered Categories for x-axes
ORDER_SOCIAL = ['Alone', 'Interactive', 'Passive']
ORDER_TASK   = ['Low', 'High mental', 'High physical']
ORDER_SOUND  = ['Quiet', 'Music', 'Speech']

# Custom Palettes for distinct box plot colors
PALETTE_SOCIAL = {'Alone': '#6baed6', 'Interactive': '#3182bd', 'Passive': '#08519c'}
PALETTE_TASK = {'Low': '#fd8d3c', 'High mental': '#e6550d', 'High physical': '#a63603'}
PALETTE_SOUND = {'Quiet': '#74c476', 'Music': '#31a354', 'Speech': '#006d2c'}

# Emojis for titles
TITLE_EMOJIS = {
    'Earcon': 'Earcon (\U0001f514)',
    'Short Speech': 'Short Speech (\U0001f5e3)',
    'Rich Speech': 'Rich Speech (\U0001f5e3 \U0001f5e3)'
}

# 3. Likert text to numeric conversion mapping (Corrected to match survey PDF exactly)
LIKERT_MAP = {
    # Detectability mappings
    "Very difficult to detect": 1, 
    "Difficult to detect": 2, 
    "Somewhat difficult to detect": 3,
    "Neither easy nor difficult to detect": 4, 
    "Somewhat easy to detect": 5, 
    "Easy to detect": 6, 
    "Very easy to detect": 7,
    
    # Disruption mappings
    "Not disruptive at all": 1, 
    "Slightly disruptive": 2, 
    "Somewhat disruptive": 3,
    "Moderately disruptive": 4,
    "Disruptive": 5, 
    "Very disruptive": 6, 
    "Extremely disruptive": 7,
    
    # Social mappings
    "Completely unacceptable": 1, 
    "Unacceptable": 2, 
    "Somewhat unacceptable": 3,
    "Neither acceptable nor unacceptable": 4,
    "Somewhat acceptable": 5, 
    "Acceptable": 6, 
    "Completely acceptable": 7,
    "Completely Acceptable": 7,
    "Completel Acceptable": 7  # Catching the typo present in the PDF matrix tables
}

# ==========================================
# FUNCTIONS
# ==========================================

def load_and_filter_data(data_path, outliers_path, start_date=START_DATE, end_date=END_DATE, remove_outliers=REMOVE_OUTLIERS):
    """Reads data, excludes outliers (if enabled), and filters by the global date range."""
    print("Loading data...")
    df = pd.read_excel(data_path)
    
    df['RecordedDate'] = pd.to_datetime(df['RecordedDate'], errors='coerce', format='mixed')
    
    # Apply Date Filters
    if start_date:
        df = df[df['RecordedDate'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['RecordedDate'] <= pd.to_datetime(end_date)]
        
    range_str = f"from {start_date or 'beginning'} to {end_date or 'latest'}"
    print(f"Data remaining after date filtering ({range_str}): {len(df)} rows.")

    # Apply Outlier Filter
    if remove_outliers:
        if os.path.exists(outliers_path):
            with open(outliers_path, 'r') as f:
                outliers = [line.strip() for line in f if line.strip()]
            
            df = df[~df['ResponseId'].isin(outliers)]
            print(f"Excluded {len(outliers)} outliers. Final row count: {len(df)}.")
        else:
            print(f"Outlier file '{outliers_path}' not found. Skipping outlier exclusion.")
    else:
        print("Outlier exclusion is DISABLED via global flag. Keeping all data points.")
        
    return df


def find_column(columns, sc_key, keyword, t_id):
    """
    Fuzzy matching to bypass Qualtrics' non-breaking spaces and slight typos.
    Looks for a column that starts with "A.", contains the keyword, and ends with "_1".
    """
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

    # Clean up column headers generally
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
                
                if isinstance(val_detect, str):
                    val_detect = LIKERT_MAP.get(val_detect.strip(), val_detect)
                if isinstance(val_disrupt, str):
                    val_disrupt = LIKERT_MAP.get(val_disrupt.strip(), val_disrupt)
                if isinstance(val_social, str):
                    val_social = LIKERT_MAP.get(val_social.strip(), val_social)

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
    """Generates and saves the 9 specific boxplots with custom y-axis anchoring."""
    print("Generating plots...")
    sns.set_theme(style="whitegrid")
    
    # Base ticks for all Likert scales
    ticks_1_to_7 = [1, 2, 3, 4, 5, 6, 7]

    for t_id, t_name in NOTIFICATION_TYPES.items():
        type_df = long_df[long_df['Notification_Type'] == t_name]
        
        if type_df.empty:
            print(f"Warning: No overall data found for {t_name}. Skipping its plots.")
            continue
            
        t_title = TITLE_EMOJIS.get(t_name, t_name)

        # ==========================================================
        # Plot 1: Social Setting (Asocial) vs Social Acceptability
        # ==========================================================
        plot1_df = type_df.dropna(subset=['Social Acceptability'])
        if not plot1_df.empty:
            plt.figure(figsize=(9, 6))
            ax = sns.boxplot(
                data=plot1_df, x='Asocial', y='Social Acceptability', 
                order=ORDER_SOCIAL, palette=PALETTE_SOCIAL
            )
            plt.title(f"{t_title}: Social Acceptability by Social Setting (Asocial)", fontsize=14, fontname='Segoe UI Emoji')
            plt.xlabel(r"$A_{SOCIAL}$", fontsize=12)
            plt.ylabel("Social Acceptability", fontsize=12)
            
            plt.yticks(
                ticks=ticks_1_to_7, 
                labels=[
                    "Completely unacceptable (1)",
                    "Unacceptable (2)",
                    "Somewhat unacceptable (3)",
                    "Neither acceptable nor unacceptable (4)",
                    "Somewhat acceptable (5)",
                    "Acceptable (6)",
                    "Completely acceptable (7)"
                ],
                fontsize=10
            )
            plt.ylim(0.5, 7.5)
            
            if DEBUG_MODE:
                add_debug_overlay(ax, plot1_df, 'Asocial')

            plt.tight_layout()
            plt.savefig(f"Plot1_{t_name.replace(' ', '')}_Social.png", dpi=300)
            plt.close()
        else:
            print(f"Warning: Skipping Plot 1 (Social) for {t_name}: No valid numeric data found.")

        # ==========================================================
        # Plot 2: Task Load (e-Task) vs Disruption
        # ==========================================================
        plot2_df = type_df.dropna(subset=['Disruption'])
        if not plot2_df.empty:
            plt.figure(figsize=(9, 6))
            ax = sns.boxplot(
                data=plot2_df, x='e-Task', y='Disruption', 
                order=ORDER_TASK, palette=PALETTE_TASK
            )
            plt.title(f"{t_title}: Disruption by Task Load (e-Task)", fontsize=14, fontname='Segoe UI Emoji')
            plt.xlabel(r"$E_{TASK}$", fontsize=12)
            plt.ylabel("Disruption", fontsize=12)
            
            plt.yticks(
                ticks=ticks_1_to_7, 
                labels=[
                    "Not disruptive at all (1)",
                    "Slightly disruptive (2)",
                    "Somewhat disruptive (3)",
                    "Moderately disruptive (4)",
                    "Disruptive (5)",
                    "Very disruptive (6)",
                    "Extremely disruptive (7)"
                ],
                fontsize=10
            )
            plt.ylim(0.5, 7.5)
            
            if DEBUG_MODE:
                add_debug_overlay(ax, plot2_df, 'e-Task')

            plt.tight_layout()
            plt.savefig(f"Plot2_{t_name.replace(' ', '')}_Disruption.png", dpi=300)
            plt.close()
        else:
            print(f"Warning: Skipping Plot 2 (Disruption) for {t_name}: No valid numeric data found.")

        # ==========================================================
        # Plot 3: Soundscape (CM) vs Detectability
        # ==========================================================
        plot3_df = type_df.dropna(subset=['Detectability'])
        if not plot3_df.empty:
            plt.figure(figsize=(9, 6))
            ax = sns.boxplot(
                data=plot3_df, x='CM', y='Detectability', 
                order=ORDER_SOUND, palette=PALETTE_SOUND
            )
            plt.title(f"{t_title}: Detectability by Sound Masking (CM)", fontsize=14, fontname='Segoe UI Emoji')
            plt.xlabel(r"$C_M$", fontsize=12)
            plt.ylabel("Detectability", fontsize=12)
            
            plt.yticks(
                ticks=ticks_1_to_7, 
                labels=[
                    "Very difficult to detect (1)",
                    "Difficult to detect (2)",
                    "Somewhat difficult to detect (3)",
                    "Neither easy nor difficult to detect (4)",
                    "Somewhat easy to detect (5)",
                    "Easy to detect (6)",
                    "Very easy to detect (7)"
                ],
                fontsize=10
            )
            plt.ylim(0.5, 7.5)
            
            if DEBUG_MODE:
                add_debug_overlay(ax, plot3_df, 'CM')

            plt.tight_layout()
            plt.savefig(f"Plot3_{t_name.replace(' ', '')}_Detectability.png", dpi=300)
            plt.close()
        else:
            print(f"Warning: Skipping Plot 3 (Detectability) for {t_name}: No valid numeric data found.")

    print("Finished plot generation process.")

def main():
    data_file = 'data.xlsx'
    outliers_file = 'listOfManuallyIdentifiedOutliers.txt'

    df = load_and_filter_data(data_file, outliers_file)
    long_df = transform_to_long_format(df)
    create_boxplots(long_df)

if __name__ == "__main__":
    main()

