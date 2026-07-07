import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# Configure fonts (matching your original setup)
plt.rcParams['font.sans-serif'] = ['Arial', 'Segoe UI Emoji', 'Tahoma', 'DejaVu Sans']

# ==========================================
# CONFIGURATION
# ==========================================

START_DATE = "2026-06-30" 
END_DATE = None            
REMOVE_OUTLIERS = True
OUTPUT_DIR = "furtherPlots2"

# ==========================================
# FUNCTIONS
# ==========================================

def load_and_filter_data(data_path, outliers_path, start_date=START_DATE, end_date=END_DATE, remove_outliers=REMOVE_OUTLIERS):
    print("Loading data...")
    df = pd.read_excel(data_path)
    
    # Clean column names (remove non-breaking spaces) to match your Streamlit logic perfectly
    df.columns = [str(c).replace('\xa0', ' ').strip() for c in df.columns]
    
    raw_count = len(df)
    
    # Filter by Date (this also implicitly removes the Qualtrics metadata rows at index 0 and 1)
    df['RecordedDate'] = pd.to_datetime(df['RecordedDate'], errors='coerce', format='mixed')
    if start_date: df = df[df['RecordedDate'] >= pd.to_datetime(start_date)]
    if end_date: df = df[df['RecordedDate'] <= pd.to_datetime(end_date)]
        
    post_date_count = len(df)
    
    # Remove Outliers
    removed_outliers_count = 0
    if remove_outliers:
        if os.path.exists(outliers_path):
            with open(outliers_path, 'r') as f:
                outliers = [line.strip() for line in f if line.strip()]
            removed_outliers_count = df['ResponseId'].isin(outliers).sum()
            df = df[~df['ResponseId'].isin(outliers)]
            print(f"Excluded {removed_outliers_count} outliers.")
            
    print(f"Initial rows: {raw_count} | Post-date filter: {post_date_count} | Final N = {len(df)}")
    return df

def plot_notification_settings(df):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    col_name = 'My Notif Settings'
    
    # Ensure column exists
    if col_name not in df.columns:
        print(f"\n❌ Error: Column '{col_name}' not found in the dataset.")
        return
        
    # Drop empty responses for this specific question
    plot_df = df.dropna(subset=[col_name]).copy()
    
    # Shorten labels by removing text in parentheses
    plot_df[col_name] = plot_df[col_name].astype(str).apply(lambda x: x.split('(')[0].strip())
    
    # Count frequencies
    counts = plot_df[col_name].value_counts().reset_index()
    counts.columns = [col_name, 'Count']
    
    if counts.empty:
        print(f"\n❌ No valid data found in column '{col_name}'.")
        return

    print("\nGenerating plot for Standard Smartphone Notification Settings...")
    
    # Set up the plot
    plt.figure(figsize=(10, 6))
    sns.set_theme(style="whitegrid")
    
    # Define a custom color map to visually group categories
    color_map = {
        'Visual only': '#6baed6',                  # Light blue (visual approach)
        'Visual and Vibration': '#2171b5',         # Dark blue (visual approach)
        'Visual and Audio': '#fd8d3c',             # Light orange (audio involved)
        'Visual, Vibration, and Audio': '#d94801', # Dark orange (audio involved)
        'No notification at all': '#969696'        # Grey (different)
    }
    
    # Map colors to the categories in the order they appear in 'counts'
    colors = [color_map.get(label, '#cccccc') for label in counts[col_name]]
    
    # Create horizontal bar plot (horizontal is best for long text answers)
    ax = sns.barplot(
        data=counts, 
        x='Count', 
        y=col_name, 
        palette=colors
    )
    
    # Add count and percentage labels to the end of each bar
    total_participants = counts['Count'].sum()
    for p in ax.patches:
        width = p.get_width()
        if width > 0:
            percentage = f"{100 * width / total_participants:.1f}%"
            ax.annotate(
                f'{int(width)} ({percentage})',
                (width, p.get_y() + p.get_height() / 2),
                ha='left', va='center',
                xytext=(8, 0), # 8 points offset to the right
                textcoords='offset points',
                fontsize=11,
                fontweight='bold',
                color='#333333'
            )
            
    # Styling
    plt.title("Standard Smartphone Notification Setting", fontsize=16, pad=20, fontweight='bold')
    plt.xlabel("Number of Participants", fontsize=12, labelpad=10)
    plt.ylabel("") # Left empty since categories explain themselves
    
    # Extend x-axis limit by 15% to make room for the text annotations
    max_count = counts['Count'].max()
    plt.xlim(0, max_count * 1.15)
    
    plt.tight_layout()
    
    # Save the plot
    filename = os.path.join(OUTPUT_DIR, "Standard_Smartphone_Notification_Setting.png")
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Plot successfully saved to: {filename}")

def main():
    data_file = 'data.xlsx'
    outliers_file = 'listOfManuallyIdentifiedOutliers.txt'

    # 1. Load Data
    df = load_and_filter_data(data_file, outliers_file)
    
    # 2. Generate Plot
    plot_notification_settings(df)
    
    print("\n" + "="*50)
    print("SCRIPT FINISHED")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()