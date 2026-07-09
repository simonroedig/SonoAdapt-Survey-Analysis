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

# !!! IMPORTANT !!!
# Change this to match the exact column suffix in your Excel file for the timing question
TIMING_COLUMN_SUFFIX = ". Timing" # e.g., looks for "A. Timing", "B. Timing"

# Explicitly tell Matplotlib to use the sans-serif list for all text by default
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Segoe UI Emoji', 'Tahoma', 'DejaVu Sans']

SCENARIOS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def categorize_timing(val):
    """Maps free-text or standard Qualtrics timing responses to plotting categories."""
    if pd.isna(val): 
        return None
    val_str = str(val).lower()
    
    # 1. Immediate
    if 'immediate' in val_str or 'right away' in val_str:
        return 'Immediate'
        
    # 2. Micro-Break
    elif 'pause' in val_str or 'brief' in val_str or 'between picking' in val_str or 'look up' in val_str:
        return 'Micro-Break'
        
    # 3. Subtask Break
    elif 'current task' in val_str or 'segment' in val_str or 'part of' in val_str or 'stopping point' in val_str or 'collected all' in val_str or 'current topic' in val_str:
        return 'Subtask Break'
        
    # 4. After Task
    elif 'later' in val_str or 'done' in val_str or 'finished' in val_str or 'over' in val_str:
        return 'After Task'
        
    # Generic delay catch-all if they just picked "Delayed"
    elif 'delay' in val_str:
        return 'Delayed (General)'
        
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
    pref_cols = [f"{sc}{TIMING_COLUMN_SUFFIX}" for sc in SCENARIOS if f"{sc}{TIMING_COLUMN_SUFFIX}" in df.columns]
    
    if not pref_cols:
        print(f"Error: Could not find any columns ending with '{TIMING_COLUMN_SUFFIX}'. Please check your Excel column headers.")
        return

    # Create a clean subset dataframe of just their choices
    choices_df = pd.DataFrame()
    for col in pref_cols:
        choices_df[col] = df[col].apply(categorize_timing)

    # Calculate how many unique timing styles each person picked
    df['Unique_Timings_Count'] = choices_df.apply(lambda row: row.dropna().nunique(), axis=1)
    
    # Calculate how many scenarios they actually answered
    df['Scenarios_Answered'] = choices_df.apply(lambda row: row.notna().sum(), axis=1)
    
    # Only look at participants who answered at least 5 scenarios
    valid_users = df[df['Scenarios_Answered'] >= 5]
    
    if valid_users.empty:
        print("Not enough scenario data to calculate variance.")
        return

    # 6. Calculate Statistics
    counts = valid_users['Unique_Timings_Count'].value_counts().sort_index()
    percentages = (counts / len(valid_users)) * 100
    
    one_style_users = percentages.get(1, 0)
    adaptable_users = 100 - one_style_users

    print("\n--- INTRA-USER TIMING VARIANCE STATS ---")
    print(f"Participants who used ONLY ONE timing across all contexts: {one_style_users:.1f}%")
    print(f"Participants who ADAPTED timing (used 2+ timings) based on context: {adaptable_users:.1f}%")
    for k, v in counts.items():
        print(f" - Used exactly {k} different timings: {v} participants ({percentages[k]:.1f}%)")
    print("----------------------------------------\n")

    # 7. Generate Visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Custom colors: Emphasize that >1 is good
    bar_colors = ['#E74C3C' if x == 1 else '#27AE60' for x in counts.index]
    
    bars = ax.bar(counts.index, percentages.values, color=bar_colors, edgecolor='black', linewidth=1.2)
    
    # Add percentage labels on top of bars
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 1, f'{yval:.1f}%', 
                ha='center', va='bottom', fontsize=12, fontweight='bold')

    # Formatting
    ax.set_title("Intra-User Timing Variance:\nDo participants stick to one timing, or adapt to the context?", 
                 fontsize=14, fontweight='bold', pad=15)
    
    ax.set_xlabel("Number of Unique Timing Styles Chosen\n(Immediate, Micro-Break, Subtask Break, After Task, Other)", fontsize=12, labelpad=15)
    ax.set_ylabel("Percentage of Participants (%)", fontsize=12, labelpad=10)
    
    # Custom Descriptive X-Axis Labels dynamically based on available data
    x_labels = []
    for i in counts.index:
        if i == 1:
            x_labels.append("1 Timing\n(Static)")
        elif i == max(counts.index):
            x_labels.append(f"{i} Timings\n(Highly Adaptive)")
        else:
            x_labels.append(f"{i} Timings")
            
    ax.set_xticks(counts.index)
    ax.set_xticklabels(x_labels, fontsize=11)
    
    # Limit Y-axis slightly above max value to fit the text
    ax.set_ylim(0, percentages.max() + 10)
    
    # Clean up background
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Add a descriptive text box summarizing the finding
    textstr = f"Finding: {adaptable_users:.1f}% of users changed\ntheir preferred notification timing\nat least once based on the scenario."
    props = dict(boxstyle='round', facecolor='honeydew', alpha=0.5)
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props)

    # Save Plot
    output_path = os.path.join(OUTPUT_DIR, "IntraUser_TimingVariance_BarChart.png")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    print(f"Saved visualization to: {output_path}")

if __name__ == '__main__':
    main()