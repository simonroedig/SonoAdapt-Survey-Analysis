import pandas as pd
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# CONFIGURATION
# ==========================================
DATA_FILE = "data.xlsx"
OUTLIERS_FILE = "listOfManuallyIdentifiedOutliers.txt"
OUTPUT_DIR = "furtherPlots"
START_DATE = "2026-06-30"

# Explicitly tell Matplotlib to use the sans-serif list for all text by default
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Segoe UI Emoji', 'Tahoma', 'DejaVu Sans']

SCENARIOS = {
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

# Define the requested color palette using strict base unicode 
# to prevent Matplotlib from rendering the \uFE0F variation selector as an empty space.
COLORS = {
    'No Audio \U0001F515': '#A6A6A6',              # 🔕
    'Version 1 \U0001F514': '#FFC300',             # 🔔
    'Version 2 \U0001F5E3': '#AF7AC5',             # 🗣
    'Version 3 \U0001F5E3\U0001F5E3': '#694487',   # 🗣🗣
    'Other': '#E0E0E0'
}

# Enforce order so Version 2 and 3 sit next to each other
ORDER = ['No Audio \U0001F515', 'Version 1 \U0001F514', 'Version 2 \U0001F5E3', 'Version 3 \U0001F5E3\U0001F5E3', 'Other']

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def categorize_preference(val):
    """Maps free-text or standard Qualtrics responses to plotting categories with emojis."""
    if pd.isna(val): 
        return None
        
    val_str = str(val).lower()
    
    if 'none' in val_str or 'no audio' in val_str or 'mute' in val_str:
        return 'No Audio \U0001F515'
    elif '1' in val_str or 'earcon' in val_str or 'sound' in val_str:
        return 'Version 1 \U0001F514'
    elif '2' in val_str:
        return 'Version 2 \U0001F5E3'
    elif '3' in val_str:
        return 'Version 3 \U0001F5E3\U0001F5E3'
    return 'Other'

# ==========================================
# MAIN SCRIPT
# ==========================================
def main():
    # 1. Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. Load data
    print(f"Loading data from {DATA_FILE}...")
    try:
        raw_df = pd.read_excel(DATA_FILE)
        df = raw_df.iloc[1:].reset_index(drop=True)
        df.columns = [str(c).replace('\xa0', ' ').strip() for c in df.columns]
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    # 3. Apply Date Filter
    date_col = next((c for c in ['RecordedDate', 'StartDate', 'EndDate'] if c in df.columns), None)
    if date_col:
        df['temp_date'] = pd.to_datetime(df[date_col], errors='coerce', format='mixed')
        df = df[df['temp_date'] >= pd.to_datetime(START_DATE)]
        print(f"Filtered by date >= {START_DATE}. Remaining rows: {len(df)}")

    # 4. Apply Outlier Filter
    if os.path.exists(OUTLIERS_FILE):
        with open(OUTLIERS_FILE, 'r', encoding='utf-8') as f:
            outliers = [line.strip() for line in f if line.strip()]
            
        if 'ResponseId' in df.columns:
            df = df[~df['ResponseId'].isin(outliers)]
            print(f"Removed {len(outliers)} manually identified outliers. Remaining rows: {len(df)}")

    # 5. Generate Pie Charts
    print("\nGenerating scenario pie charts...")
    for prefix, name in SCENARIOS.items():
        col_name = f"{prefix}. Overall"
        
        if col_name in df.columns:
            # Extract values and categorize them
            preferences = df[col_name].apply(categorize_preference).dropna()
            
            if preferences.empty:
                print(f"  - No valid data for Scenario {prefix}, skipping.")
                continue
                
            counts = preferences.value_counts()
            
            # Match the customized order and colors
            plot_labels = [label for label in ORDER if label in counts.index]
            plot_sizes = [counts[label] for label in plot_labels]
            plot_colors = [COLORS[label] for label in plot_labels]
            
            # Setup Plot
            fig, ax = plt.subplots(figsize=(8, 8))
            
            pie_result = ax.pie(
                plot_sizes, 
                labels=plot_labels, 
                colors=plot_colors, 
                autopct='%1.1f%%', 
                startangle=140, 
                wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}
            )
            
            # Manually force the emoji font on all generated pie texts
            texts = pie_result[1]
            autotexts = pie_result[2] if len(pie_result) > 2 else []
            
            for text in texts + autotexts:
                text.set_fontname('Segoe UI Emoji')
                text.set_fontsize(13)
            
            # Enforce the font for the title
            plt.title(f"Overall Preference\nScenario {prefix}: {name}", 
                      fontsize=16, fontweight='bold', pad=20, fontname='Segoe UI Emoji')
            
            # Save the file
            output_path = os.path.join(OUTPUT_DIR, f"Scenario_{prefix}_Overall_Preference.png")
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"  + Saved: {output_path}")
        else:
            print(f"  ! Column '{col_name}' not found for Scenario {prefix}.")

    print("\nDone! Check the 'furtherPlots' directory for the charts.")

if __name__ == '__main__':
    main()