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
OUTPUT_DIR = "variancePlots"
START_DATE = "2026-06-30"

# Explicitly tell Matplotlib to use the sans-serif list for all text by default
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Segoe UI Emoji', 'Tahoma', 'DejaVu Sans']

SCENARIOS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def categorize_preference(val):
    """Maps free-text or standard Qualtrics responses to plotting categories."""
    if pd.isna(val): 
        return None
    val_str = str(val).lower()
    
    if 'none' in val_str or 'no audio' in val_str or 'mute' in val_str:
        return 'No Audio'
    elif '1' in val_str or 'earcon' in val_str or 'sound' in val_str:
        return 'Version 1'
    elif '2' in val_str:
        return 'Version 2'
    elif '3' in val_str:
        return 'Version 3'
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

    # 4. Apply Outlier Filter
    if os.path.exists(OUTLIERS_FILE):
        with open(OUTLIERS_FILE, 'r', encoding='utf-8') as f:
            outliers = [line.strip() for line in f if line.strip()]
        if 'ResponseId' in df.columns:
            df = df[~df['ResponseId'].isin(outliers)]

    print(f"Total valid participants to analyze: {len(df)}")

    # 5. Extract and process scenario choices
    pref_cols = [f"{sc}. Overall" for sc in SCENARIOS if f"{sc}. Overall" in df.columns]
    
    # Create a clean subset dataframe of just their choices
    choices_df = pd.DataFrame()
    for col in pref_cols:
        choices_df[col] = df[col].apply(categorize_preference)

    # Calculate how many unique styles each person picked across all answered scenarios
    df['Unique_Styles_Count'] = choices_df.apply(lambda row: row.dropna().nunique(), axis=1)
    
    # Calculate how many scenarios they actually answered
    df['Scenarios_Answered'] = choices_df.apply(lambda row: row.notna().sum(), axis=1)
    
    # Only look at participants who answered at least 5 scenarios to get a fair variance
    valid_users = df[df['Scenarios_Answered'] >= 5]
    
    if valid_users.empty:
        print("Not enough scenario data to calculate variance.")
        return

    # 6. Calculate Statistics
    counts = valid_users['Unique_Styles_Count'].value_counts().sort_index()
    percentages = (counts / len(valid_users)) * 100
    
    one_style_users = percentages.get(1, 0)
    adaptable_users = 100 - one_style_users

    print("\n--- INTRA-USER VARIANCE STATS ---")
    print(f"Participants who used ONLY ONE style across all contexts: {one_style_users:.1f}%")
    print(f"Participants who ADAPTED (used 2+ styles) based on context: {adaptable_users:.1f}%")
    for k, v in counts.items():
        print(f" - Used exactly {k} different styles: {v} participants ({percentages[k]:.1f}%)")
    print("---------------------------------\n")

    # 7. Generate Visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Custom colors: Emphasize that >1 is good
    bar_colors = ['#E74C3C' if x == 1 else '#3498DB' for x in counts.index]
    
    bars = ax.bar(counts.index, percentages.values, color=bar_colors, edgecolor='black', linewidth=1.2)
    
    # Add percentage labels on top of bars
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 1, f'{yval:.1f}%', 
                ha='center', va='bottom', fontsize=12, fontweight='bold')

    # Formatting
    ax.set_title("Intra-User Variance:\nDo participants stick to one favorite, or adapt to the context?", 
                 fontsize=14, fontweight='bold', pad=15)
    
    # --- RESTORED: Main X-axis label added back ---
    ax.set_xlabel("Number of Unique Notification Styles Chosen", fontsize=12, labelpad=15)
    ax.set_ylabel("Percentage of Participants (%)", fontsize=12, labelpad=10)
    
    # Custom Descriptive X-Axis Labels
    x_labels = [
        "1 Style\n(Static)", 
        "2 Styles", 
        "3 Styles", 
        "4 Styles\n(Highly Adaptive)"
    ]
    ax.set_xticks(range(1, 5))
    ax.set_xticklabels(x_labels, fontsize=11)
    # -------------------------------------------------
    
    # Limit Y-axis slightly above max value to fit the text
    ax.set_ylim(0, percentages.max() + 10)
    
    # Clean up background
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Add a descriptive text box summarizing the finding
    textstr = f"Finding: {adaptable_users:.1f}% of users changed\ntheir preferred notification style\nat least once based on the scenario."
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props)

    # Save Plot
    output_path = os.path.join(OUTPUT_DIR, "IntraUser_Variance_BarChart.png")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    print(f"Saved visualization to: {output_path}")

if __name__ == '__main__':
    main()