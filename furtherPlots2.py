import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re
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
    
    # Clean column names (remove non-breaking spaces)
    df.columns = [str(c).replace('\xa0', ' ').strip() for c in df.columns]
    
    raw_count = len(df)
    
    # Filter by Date
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
    base_filename = "Standard_Smartphone_Notification_Setting"
    
    if col_name not in df.columns:
        print(f"\n❌ Error: Column '{col_name}' not found in the dataset.")
        return
        
    plot_df = df.dropna(subset=[col_name]).copy()
    
    # Shorten labels by removing text in parentheses
    plot_df[col_name] = plot_df[col_name].astype(str).apply(lambda x: x.split('(')[0].strip())
    
    counts = plot_df[col_name].value_counts().reset_index()
    counts.columns = [col_name, 'Count']
    
    if counts.empty: return

    # Calculate percentages for the JSON export
    total_participants = counts['Count'].sum()
    counts['Percentage'] = (counts['Count'] / total_participants * 100).round(1).astype(str) + '%'

    # Save data to JSON
    json_path = os.path.join(OUTPUT_DIR, f"{base_filename}.json")
    counts.to_json(json_path, orient='records', indent=4)

    print("\nGenerating plot for Standard Smartphone Notification Settings...")
    
    plt.figure(figsize=(10, 6))
    sns.set_theme(style="whitegrid")
    
    color_map = {
        'Visual only': '#6baed6',                  
        'Visual and Vibration': '#2171b5',         
        'Visual and Audio': '#fd8d3c',             
        'Visual, Vibration, and Audio': '#d94801', 
        'No notification at all': '#969696'        
    }
    colors = [color_map.get(label, '#cccccc') for label in counts[col_name]]
    
    ax = sns.barplot(data=counts, x='Count', y=col_name, palette=colors)
    
    for p in ax.patches:
        width = p.get_width()
        if width > 0:
            percentage = f"{100 * width / total_participants:.1f}%"
            ax.annotate(
                f'{int(width)} ({percentage})',
                (width, p.get_y() + p.get_height() / 2),
                ha='left', va='center', xytext=(8, 0), textcoords='offset points',
                fontsize=11, fontweight='bold', color='#333333'
            )
            
    plt.title("Standard Smartphone Notification Setting", fontsize=16, pad=20, fontweight='bold')
    plt.xlabel("Number of Participants", fontsize=12, labelpad=10)
    plt.ylabel("") 
    
    plt.xlim(0, counts['Count'].max() * 1.15)
    plt.tight_layout()
    
    img_path = os.path.join(OUTPUT_DIR, f"{base_filename}.png")
    plt.savefig(img_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Plot saved to: {img_path}")
    print(f"✅ Data saved to: {json_path}")

def plot_notification_reasons(df):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    col_name = 'My Notif SettingsWhy'
    base_filename = "Reasons_For_Notification_Setting"
    
    if col_name not in df.columns:
        print(f"\n❌ Error: Column '{col_name}' not found in the dataset.")
        return
        
    plot_df = df.dropna(subset=[col_name]).copy()
    total_participants = len(plot_df) 
    
    if total_participants == 0: return

    # Flatten the comma-separated multiple choice answers
    all_responses = []
    for val in plot_df[col_name]:
        # Split by comma ONLY if it's NOT followed by a space
        items = re.split(r',(?!\s)', str(val))
        
        for item in items:
            clean_item = item.split('(')[0].strip() # Clean up and remove parentheses
            if clean_item:
                all_responses.append(clean_item)
                
    # Count frequencies of each reason
    counts = pd.Series(all_responses).value_counts().reset_index()
    counts.columns = ['Reason', 'Count']

    # Calculate percentages for the JSON export
    counts['Percentage_of_Participants'] = (counts['Count'] / total_participants * 100).round(1).astype(str) + '%'

    # Save data to JSON
    json_path = os.path.join(OUTPUT_DIR, f"{base_filename}.json")
    counts.to_json(json_path, orient='records', indent=4)

    print("\nGenerating plot for Reasons for Chosen Setting...")
    
    plt.figure(figsize=(10, 6))
    sns.set_theme(style="whitegrid")
    
    ax = sns.barplot(data=counts, x='Count', y='Reason', palette="flare")
    
    for p in ax.patches:
        width = p.get_width()
        if width > 0:
            percentage = f"{100 * width / total_participants:.1f}%"
            ax.annotate(
                f'{int(width)} ({percentage})',
                (width, p.get_y() + p.get_height() / 2),
                ha='left', va='center', xytext=(8, 0), textcoords='offset points',
                fontsize=11, fontweight='bold', color='#333333'
            )
            
    plt.title("Reasons for Chosen Smartphone Notification Setting", fontsize=16, pad=20, fontweight='bold')
    plt.xlabel(f"Number of Participants (n={total_participants})", fontsize=12, labelpad=10)
    plt.ylabel("") 
    
    plt.xlim(0, counts['Count'].max() * 1.25)
    plt.tight_layout()
    
    img_path = os.path.join(OUTPUT_DIR, f"{base_filename}.png")
    plt.savefig(img_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Plot saved to: {img_path}")
    print(f"✅ Data saved to: {json_path}")

def main():
    data_file = 'data.xlsx'
    outliers_file = 'listOfManuallyIdentifiedOutliers.txt'

    # 1. Load Data
    df = load_and_filter_data(data_file, outliers_file)
    
    # 2. Generate Plots & JSONs
    plot_notification_settings(df)
    plot_notification_reasons(df)
    
    print("\n" + "="*50)
    print("SCRIPT FINISHED")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()