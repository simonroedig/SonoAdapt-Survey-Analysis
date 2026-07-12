import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import datetime

# ==========================================
# CONFIGURATION
# ==========================================
DATA_FILE = "data.xlsx"
OUTPUT_DIR = "finalMetrics"
OUTLIERS_FILE = "listOfManuallyIdentifiedOutliers.txt"

# Explicitly tell Matplotlib to use the sans-serif list for all text by default
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Segoe UI Emoji', 'Tahoma', 'DejaVu Sans']

# --- PALETTES ---
COLORS_PREF = {
    'No Audio': '#A6A6A6',      # 🔕 (Grey)
    'Earcon': '#FFC300',        # 🔔 (Yellow)
    'Short Speech': '#AF7AC5',  # 🗣 (Light Purple)
    'Rich Speech': '#694487'    # 🗣🗣 (Dark Purple)
}

COLORS_DELAY = {
    'No Delay': '#E74C3C',                 # 🚨 Red (Interrupt immediately)
    'Brief Delay (Secs)': '#F39C12',       # ⚠️ Orange (Quick safe moment)
    'Moderate Delay (Mins)': '#3498DB',    # ⏳ Blue (Finish current task)
    'Indefinite Delay (Hours)': '#95A5A6'  # 💤 Grey (Withhold entirely)
}

# --- COLUMNS ---
PREF_COLS = ['Preference Matrix_1', 'Preference Matrix_2', 'Preference Matrix_3', 'Preference Matrix_4']
DELAY_COLS = ['Delay Matrix_1', 'Delay Matrix_2', 'Delay Matrix_3', 'Delay Matrix_4']

X_LABELS = [
    "Simple Ack\n(Low Urgency,\nLow Importance)",
    "Routine Update\n(Low Urgency,\nMed Importance)",
    "Great News\n(Low Urgency,\nHigh Importance)",
    "Time-Sensitive\n(High Urgency,\nHigh Importance)"
]

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def map_pref_category(response_str):
    response_str = str(response_str).lower()
    if 'mute' in response_str: return 'No Audio'
    elif 'version 1' in response_str or 'sound only' in response_str: return 'Earcon'
    elif 'version 3' in response_str or 'full/summarized' in response_str: return 'Rich Speech'
    elif 'version 2' in response_str or 'speech' in response_str: return 'Short Speech'
    return None

def map_delay_category(response_str):
    response_str = str(response_str).lower()
    if 'no delay' in response_str: return 'No Delay'
    elif 'brief delay' in response_str: return 'Brief Delay (Secs)'
    elif 'moderate delay' in response_str: return 'Moderate Delay (Mins)'
    elif 'indefinite delay' in response_str: return 'Indefinite Delay (Hours)'
    return None

def generate_flow_chart(results_dict, categories, colors, title, output_filename, legend_title):
    fig, ax = plt.subplots(figsize=(10, 6))
    x_pos = np.arange(len(X_LABELS))

    for category in categories:
        y_values = results_dict[category]
        
        ax.plot(
            x_pos, y_values, 
            color=colors[category], 
            label=category, 
            linewidth=4, marker='o', markersize=10,
            markeredgecolor='white', markeredgewidth=1.5
        )
        
        for i, (x, y) in enumerate(zip(x_pos, y_values)):
            y_offset = 3 if y < 50 else -4 
            va = 'bottom' if y_offset > 0 else 'top'
            
            ax.annotate(
                f"{y:.1f}%", (x, y), 
                textcoords="offset points", xytext=(0, y_offset), 
                ha='center', va=va, fontsize=10, 
                fontweight='bold', color=colors[category]
            )

    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel("Percentage of Participants (%)", fontsize=12, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(X_LABELS, fontsize=11)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5, color='#D3D3D3')
    ax.set_axisbelow(True)
    ax.set_ylim(-5, 105)

    ax.legend(
        loc='upper left', bbox_to_anchor=(1.02, 1), 
        borderaxespad=0, frameon=False, fontsize=12,
        title=legend_title, title_fontproperties={'weight': 'bold', 'size': 12}
    )

    plt.tight_layout()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, output_filename)
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"Saved plot: {out_path}")
    plt.close()

# ==========================================
# MAIN EXECUTION
# ==========================================
def main():
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found.")
        return

    # 1. Load Data
    raw_df = pd.read_excel(DATA_FILE)
    df = raw_df.iloc[1:].reset_index(drop=True)
    df.columns = [str(c).replace('\xa0', ' ').strip() for c in df.columns]

    initial_count = len(df)
    print(f"Initial rows loaded: {initial_count}")

    # 2. Date Filter (>= June 30, 2026)
    date_col = next((c for c in ['RecordedDate', 'StartDate', 'EndDate'] if c in df.columns), None)
    if date_col:
        df['__temp_date'] = pd.to_datetime(df[date_col], errors='coerce')
        mask = df['__temp_date'].dt.date >= datetime.date(2026, 6, 30)
        df = df[mask].drop(columns=['__temp_date'])
        print(f"Rows after date filter: {len(df)}")

    # 3. Outlier Filter
    if os.path.exists(OUTLIERS_FILE):
        with open(OUTLIERS_FILE, "r", encoding="utf-8") as f:
            outliers = [line.strip() for line in f if line.strip()]
        if outliers and 'ResponseId' in df.columns:
            df = df[~df['ResponseId'].isin(outliers)]
            print(f"Rows after outlier removal: {len(df)}")

    # 4. Process Preference Data
    pref_results = {k: [] for k in COLORS_PREF.keys()}
    for col in PREF_COLS:
        series = df[col].dropna().apply(map_pref_category)
        counts = series.value_counts()
        total = counts.sum() or 1 # avoid div by zero
        for k in pref_results:
            pref_results[k].append((counts.get(k, 0) / total) * 100)

    # 5. Process Delay Data
    delay_results = {k: [] for k in COLORS_DELAY.keys()}
    for col in DELAY_COLS:
        series = df[col].dropna().apply(map_delay_category)
        counts = series.value_counts()
        total = counts.sum() or 1
        for k in delay_results:
            delay_results[k].append((counts.get(k, 0) / total) * 100)

    # 6. Print Data Summaries to Terminal
    print("\n" + "="*50)
    print(" 📊 AUDIO PREFERENCE BY LEVEL (%)")
    print("="*50)
    for i, label in enumerate(X_LABELS):
        print(f"\nLevel {i+1}: {label.replace(chr(10), ' ')}")
        for cat in COLORS_PREF.keys():
            print(f"  - {cat}: {pref_results[cat][i]:.1f}%")

    print("\n" + "="*50)
    print(" ⏱️ DELAY TOLERANCE BY LEVEL (%)")
    print("="*50)
    for i, label in enumerate(X_LABELS):
        print(f"\nLevel {i+1}: {label.replace(chr(10), ' ')}")
        for cat in COLORS_DELAY.keys():
            print(f"  - {cat}: {delay_results[cat][i]:.1f}%")
    print("\n" + "="*50 + "\n")

    # 7. Generate Plots
    generate_flow_chart(
        pref_results, list(COLORS_PREF.keys()), COLORS_PREF,
        "Notification Preference Shifts Based on Message Priority",
        "02_Preference_Flow_Matrix.png", "Modality Type"
    )
    
    generate_flow_chart(
        delay_results, list(COLORS_DELAY.keys()), COLORS_DELAY,
        "Delay Tolerance Shifts Based on Message Priority",
        "03_Delay_Tolerance_Flow.png", "Max Acceptable Delay"
    )

if __name__ == "__main__":
    main()