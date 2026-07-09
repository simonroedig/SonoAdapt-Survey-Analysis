import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# CONFIGURATION
# ==========================================
DATA_FILE = "data.xlsx"
OUTLIERS_FILE = "listOfManuallyIdentifiedOutliers.txt"
OUTPUT_DIR = "furtherPlots4"
START_DATE = "2026-06-30"

# Explicitly tell Matplotlib to use the sans-serif list for all text by default
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Segoe UI Emoji', 'Tahoma', 'DejaVu Sans']

# Define the consistent color palette
COLORS = {
    'No Audio': '#A6A6A6',      # 🔕 (Grey)
    'Earcon': '#FFC300',        # 🔔 (Yellow)
    'Short Speech': '#AF7AC5',  # 🗣 (Light Purple)
    'Rich Speech': '#694487'    # 🗣🗣 (Dark Purple)
}

SCENARIOS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def categorize_overall_preference(val):
    """Maps Qualtrics overall preference responses to our clean categories."""
    if pd.isna(val): 
        return None
    val_str = str(val).lower()
    
    if 'none' in val_str or 'no audio' in val_str or 'mute' in val_str:
        return 'No Audio'
    elif '1' in val_str or 'earcon' in val_str or 'sound' in val_str:
        return 'Earcon'
    elif '2' in val_str:
        return 'Short Speech'
    elif '3' in val_str:
        return 'Rich Speech'
    return None

def plot_pie_chart(agg_data, title, filename):
    """Generates the pie chart matching your exact styling."""
    labels = []
    sizes = []
    colors = []
    
    # We want a specific order for consistency
    order = [
        'No Audio', 
        'Earcon', 
        'Short Speech', 
        'Rich Speech'
    ]
    
    total_n = sum(agg_data.values())
    if total_n == 0:
        print("No data available to plot.")
        return

    for cat in order:
        if agg_data.get(cat, 0) > 0:
            labels.append(cat)
            sizes.append(agg_data[cat])
            colors.append(COLORS[cat])
            
    # Dynamic Labeling: If a slice is too small (<5%), move its stats to the outer label
    display_labels = []
    for lbl, size in zip(labels, sizes):
        pct = (size / total_n) * 100
        if pct < 5.0:
            display_labels.append(f"{lbl}\n{pct:.1f}% (n={size})")
        else:
            display_labels.append(lbl)

    def custom_autopct(pct):
        if pct < 5.0:
            return ""
        return f"{pct:.1f}%\n(n={int(round(pct * total_n / 100))})"

    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Create the pie chart
    # pyrefly: ignore [bad-unpacking]
    wedges, texts, autotexts = ax.pie(  
        sizes, 
        labels=display_labels, 
        colors=colors, 
        autopct=custom_autopct,
        startangle=90,
        textprops=dict(color="black", fontsize=12)
    )
    
    # Style the wedges and text inside the pie
    for i, autotext in enumerate(autotexts):
        # Earcon (Yellow) and No Audio (Grey) get black text for contrast, Purples get white text
        if labels[i] == 'Earcon' or labels[i] == 'No Audio':
            autotext.set_color('black')
            wedges[i].set_edgecolor('white')
            wedges[i].set_linewidth(1.5)
        else:
            autotext.set_color('white')
            # Thicker dark purple outline for speech options to visually group them
            wedges[i].set_edgecolor('#4A235A')
            wedges[i].set_linewidth(2)
            
        if autotext.get_text() != "":
            autotext.set_weight('bold')
        
    # Combine the stats for Speech
    speech_n = agg_data['Short Speech'] + agg_data['Rich Speech']
    speech_pct = (speech_n / total_n) * 100
    
    # Calculate position for annotation
    speech_wedges = [w for i, w in enumerate(wedges) if labels[i] in ['Short Speech', 'Rich Speech']]
    if len(speech_wedges) == 2:
        # Since they are contiguous, get the start angle of the first and end angle of the second
        theta1 = speech_wedges[0].theta1
        theta2 = speech_wedges[1].theta2
        
        # If theta2 < theta1, it crossed 360, adjust for mid angle
        if theta2 < theta1:
            theta2 += 360
            
        mid_angle = (theta1 + theta2) / 2
        mid_angle_rad = np.deg2rad(mid_angle)
        
        x_target = 1.0 * np.cos(mid_angle_rad)
        y_target = 1.0 * np.sin(mid_angle_rad)
        
        # Place text closer to the pie chart
        x_text = 1.15 * np.cos(mid_angle_rad)
        y_text = 1.15 * np.sin(mid_angle_rad)
        
        ha = 'left' if x_text > 0 else 'right'
        
        ax.annotate(
            f"Overall Speech:\n{speech_pct:.1f}% (n={speech_n})",
            xy=(x_target, y_target),
            xytext=(x_text, y_text),
            ha=ha, va='center',
            fontsize=12, weight='bold', color='#4A235A',
            bbox=dict(boxstyle="round,pad=0.4", fc="#F5EEF8", ec="#4A235A", lw=1.5),
            arrowprops=dict(arrowstyle="-|>", color="#4A235A", lw=1.5)
        )
        
    plt.title(title, fontsize=14, weight='bold', pad=20)
    plt.tight_layout()
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"Saved plot: {out_path}")
    plt.close()

# ==========================================
# MAIN SCRIPT
# ==========================================
def main():
    # 1. Load Data
    print(f"Loading data from {DATA_FILE}...")
    try:
        raw_df = pd.read_excel(DATA_FILE)
        df = raw_df.iloc[1:].reset_index(drop=True)
        # Clean column headers
        df.columns = [str(c).replace('\xa0', ' ').strip() for c in df.columns]
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    # 2. Apply Date Filter
    date_col = next((c for c in ['RecordedDate', 'StartDate', 'EndDate'] if c in df.columns), None)
    if date_col:
        df['temp_date'] = pd.to_datetime(df[date_col], errors='coerce', format='mixed')
        df = df[df['temp_date'] >= pd.to_datetime(START_DATE)]

    # 3. Apply Outliers Filter
    if os.path.exists(OUTLIERS_FILE):
        with open(OUTLIERS_FILE, 'r', encoding='utf-8') as f:
            outliers = [line.strip() for line in f if line.strip()]
        if 'ResponseId' in df.columns:
            df = df[~df['ResponseId'].isin(outliers)]

    print(f"Total valid participants: {len(df)}")

    # 4. Aggregate across all Scenarios
    aggregated_counts = {
        'No Audio': 0,
        'Earcon': 0,
        'Short Speech': 0,
        'Rich Speech': 0
    }

    for letter in SCENARIOS:
        col_name = f"{letter}. Overall"
        if col_name in df.columns:
            mapped_series = df[col_name].apply(categorize_overall_preference).dropna()
            counts = mapped_series.value_counts().to_dict()
            
            for fmt, count in counts.items():
                if fmt in aggregated_counts:
                    aggregated_counts[fmt] += count
        else:
            print(f"Warning: Column '{col_name}' not found.")

    # 5. Generate Plot
    plot_pie_chart(
        aggregated_counts, 
        "Overall Notification Preference\n(Aggregated Across All Contexts)", 
        "00_Overall_Context_Dependent_Pie.png"
    )

if __name__ == '__main__':
    main()