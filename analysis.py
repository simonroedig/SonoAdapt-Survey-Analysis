import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import statsmodels.formula.api as smf
import warnings
warnings.filterwarnings('ignore') # Unterdrückt irrelevante Warnungen bei der Modell-Konvergenz
import numpy as np


# Configure fonts to properly render emojis (falling back to Segoe UI Emoji on Windows)
plt.rcParams['font.sans-serif'] = ['Arial', 'Segoe UI Emoji', 'Tahoma', 'DejaVu Sans']

# ==========================================
# CONFIGURATION & MAPPINGS
# ==========================================

# Toggle flags
GENERATE_PLOTS = False              # Set to True if you want to regenerate the boxplots
DEBUG_MODE = False                  # Toggle this flag to show/hide sample sizes on plots
REMOVE_OUTLIERS = True              # Exclude predefined outliers
GENERATE_SECONDARY_PLOTS = False    # Generate the extra 18 exploratory plots

# Date Filtering Range (Format: 'YYYY-MM-DD' or None)
START_DATE = "2026-06-30"  
END_DATE = None            

# 1. Notification Types
NOTIFICATION_TYPES = {
    '1': 'Earcon',
    '2': 'Short Speech',
    '3': 'Rich Speech'
}

# 2. Scenario Definitions
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

# 3. Independent Variable Properties (Updated names for formulas: e_Task instead of e-Task)
IV_PROPS = {
    'Asocial': {
        'order': ['Alone', 'Interactive', 'Passive'], 
        'palette': {'Alone': '#6baed6', 'Interactive': '#3182bd', 'Passive': '#08519c'}, 
        'label': r"$A_{SOCIAL}$ (Social Setting)",
        'title_name': 'Social Setting'
    },
    'e_Task': {
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

# 4. Dependent Variable Labels (Updated Social_Acceptability)
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
    'Rich Speech': 'Rich Speech (\U0001f5e3 \U0001f5e3)'
}

# 5. Likert Map (Added Appropriateness)
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


# AIC (Akaike Information Criterion)
# $R^2_{marg}$ (Marginal R-squared)
# $R^2_{cond}$ (Conditional R-squared)
def print_model_fit_stats(res, model_name):
    # 1. AIC auslesen
    aic = res.aic
    
    # 2. Nakagawa's R-squared für Mixed Models berechnen
    var_f = np.var(res.fittedvalues)           # Varianz der Fixed Effects
    var_r = float(res.cov_re.iloc[0, 0])       # Varianz des Random Effects (Teilnehmer)
    var_e = res.scale                          # Residual-Varianz (Restfehler)
    
    r2_marg = var_f / (var_f + var_r + var_e)
    r2_cond = (var_f + var_r) / (var_f + var_r + var_e)
    
    print(f"--- Fit Statistics for {model_name} ---")
    print(f"AIC:      {aic:.2f}")
    print(f"R2_marg:  {r2_marg:.3f}")
    print(f"R2_cond:  {r2_cond:.3f}")
    print("-" * 40 + "\n")


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
        else:
            print(f"Outlier file '{outliers_path}' not found.")
            
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
    print("Transforming dataset (including Appropriateness)...")
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
                
                # Apply likert map if values are text
                if isinstance(val_detect, str): val_detect = LIKERT_MAP.get(val_detect.strip(), val_detect)
                if isinstance(val_disrupt, str): val_disrupt = LIKERT_MAP.get(val_disrupt.strip(), val_disrupt)
                if isinstance(val_social, str): val_social = LIKERT_MAP.get(val_social.strip(), val_social)
                if isinstance(val_approp, str): val_approp = LIKERT_MAP.get(val_approp.strip(), val_approp)

                if pd.isna(val_detect) and pd.isna(val_disrupt) and pd.isna(val_social) and pd.isna(val_approp):
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
    plot_count = 27 if GENERATE_SECONDARY_PLOTS else 9
    print(f"\nGenerating {plot_count} plots...")
    sns.set_theme(style="whitegrid")
    ticks_1_to_7 = [1, 2, 3, 4, 5, 6, 7]

    for t_id, t_name in NOTIFICATION_TYPES.items():
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
            ax = sns.boxplot(data=plot_df, x=iv, y=dv, order=iv_config['order'], palette=iv_config['palette'])
            
            plt.title(f"{t_title}: {dv.replace('_', ' ')} by {iv_config['title_name']}", fontsize=14, fontname='Segoe UI Emoji')
            plt.xlabel(iv_config['label'], fontsize=12)
            plt.ylabel(dv.replace('_', ' '), fontsize=12)
            
            plt.yticks(ticks=ticks_1_to_7, labels=DV_Y_LABELS.get(dv, ticks_1_to_7), fontsize=10)
            plt.ylim(0.5, 7.5)
            
            if DEBUG_MODE: add_debug_overlay(ax, plot_df, iv)

            plt.tight_layout()
            plot_type_label = "Primary" if is_primary else "Secondary"
            filename = os.path.join("plots", f"{plot_type_label}_{t_name.replace(' ', '')}_{iv}_vs_{dv.replace(' ', '')}.png")
            plt.savefig(filename, dpi=300)
            plt.close()

# --- NEW ANALYTICAL FUNCTIONS ---

def calculate_descriptives(long_df):
    print("\nCalculating Descriptive Statistics (Means & SDs)...")
    # Groups the data and calculates Mean and Standard Deviation
    desc_stats = long_df.groupby(['Notification_Type', 'Asocial', 'e_Task', 'CM'])[['Detectability', 'Disruption', 'Social_Acceptability', 'Appropriateness']].agg(['mean', 'std']).round(2)
    
    # Save to a CSV file for easy copying into your thesis/Excel
    desc_stats.to_csv('descriptive_statistics.csv')
    print("-> Descriptive statistics saved successfully to 'descriptive_statistics.csv'.")
    return desc_stats

def run_lmm_analysis(long_df):
    print("\n" + "="*50)
    print("RUNNING LINEAR MIXED MODELS (LMM)")
    print("="*50)
    
    # Drop rows where any of the variables are missing to ensure model stability
    model_data = long_df.dropna(subset=['Disruption', 'Social_Acceptability', 'Detectability', 'Appropriateness', 'ResponseId'])
    
    if model_data.empty:
        print("Error: Not enough valid data to run LMMs. Check data formatting.")
        return

    # 1. Main Effect Model for Disruption
    print("\n--- MODEL 1: DISRUPTION ---")
    formula_disrupt = "Disruption ~ C(Notification_Type) + C(Asocial) + C(e_Task) + C(CM)"
    model_disrupt = smf.mixedlm(formula_disrupt, data=model_data, groups=model_data["ResponseId"])
    try:
        res_disrupt = model_disrupt.fit(reml=False)
        print(res_disrupt.summary())
        print_model_fit_stats(res_disrupt, "Disruption")
    except Exception as e:
        print(f"Model failed to fit: {e}")

    # 2. Main Effect Model for Social Acceptability
    print("\n--- MODEL 2: SOCIAL ACCEPTABILITY ---")
    formula_social = "Social_Acceptability ~ C(Notification_Type) + C(Asocial) + C(e_Task) + C(CM)"
    model_social = smf.mixedlm(formula_social, data=model_data, groups=model_data["ResponseId"])
    try:
        res_social = model_social.fit(reml=False)
        print(res_social.summary())
        print_model_fit_stats(res_social, "Social Acceptability")
    except Exception as e:
         print(f"Model failed to fit: {e}")

    # 3. Main Effect Model for Detectability
    print("\n--- MODEL 3: DETECTABILITY ---")
    formula_detect = "Detectability ~ C(Notification_Type) + C(Asocial) + C(e_Task) + C(CM)"
    model_detect = smf.mixedlm(formula_detect, data=model_data, groups=model_data["ResponseId"])
    try:
        res_detect = model_detect.fit(reml=False)
        print(res_detect.summary())
        print_model_fit_stats(res_detect, "Detectability")
    except Exception as e:
         print(f"Model failed to fit: {e}")

    # 4. The Appropriateness Model
    print("\n--- MODEL 4: APPROPRIATENESS ---")
    print("Testing: Which dimensions explain why people find a notification appropriate?")
    # Continuous predictors do not need C()
    formula_approp = "Appropriateness ~ Detectability * Disruption * Social_Acceptability"
    model_approp = smf.mixedlm(formula_approp, data=model_data, groups=model_data["ResponseId"])
    try:
        res_approp = model_approp.fit(reml=False)
        print(res_approp.summary())
    except Exception as e:
         print(f"Model failed to fit: {e}")

def main():
    # Use your specific dataset name
    data_file = 'data.xlsx'  # Switch to 'data.xlsx' for the real run
    outliers_file = 'listOfManuallyIdentifiedOutliers.txt'

    # Load and clean
    df, stats = load_and_filter_data(data_file, outliers_file)
    long_df = transform_to_long_format(df)
    
    # 1. Plots (Conditional)
    if GENERATE_PLOTS:
        create_boxplots(long_df)
    else:
        print("\nSkipping plot generation (GENERATE_PLOTS = False).")

    # 2. Descriptive Statistics (M & SD)
    calculate_descriptives(long_df)

    # 3. Linear Mixed Models
    run_lmm_analysis(long_df)

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
    import sys
    class Logger:
        def __init__(self, filename):
            self.terminal = sys.stdout
            self.log = open(filename, "w", encoding="utf-8")
        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
        def flush(self):
            self.terminal.flush()
            self.log.flush()
            
    sys.stdout = Logger("mainAnalysis.txt")
    main()