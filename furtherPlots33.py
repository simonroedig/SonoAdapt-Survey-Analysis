import json
import matplotlib.pyplot as plt
import os
import numpy as np

# ==========================================
# CONFIGURATION
# ==========================================
JSON_FILE = "preferencePlots/scenario_preferences_summary.json"
OUTPUT_DIR = "furtherPlots32"

# Explicitly tell Matplotlib to use the sans-serif list for all text by default
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Segoe UI Emoji', 'Tahoma', 'DejaVu Sans']

# Format Colors
FORMAT_COLORS = {
    'No Audio': '#A6A6A6',      # Grey
    'Earcon': '#FFC300',        # Yellow
    'Short Speech': '#AF7AC5',  # Light Purple
    'Rich Speech': '#694487'    # Dark Purple
}

FORMAT_MAP = {
    "Earcon (V1)": "Earcon",
    "Short Speech (V2)": "Short Speech",
    "Rich Speech (V3)": "Rich Speech",
    "None / No Audio": "No Audio"
}

TIMING_MAP = {
    "Later, when I am done working": "After Task is Finished",
    "When I briefly pause while writing / thinking": "Micro-Break Within Task",
    "After I finish the current task (e.g., finish writing (part of the) code)": "Break Between Subtasks",
    "Later, when the meeting is over": "After Task is Finished",
    "After the meeting segment I am currently involved in ends": "Break Between Subtasks",
    "When I am not speaking and there is a natural break in conversation": "Micro-Break Within Task",
    "Later, when I am done with music and relaxing": "After Task is Finished",
    "When I am between songs / during a natural pause in music": "Break Between Subtasks",
    "Later, when the whole tent is set up and we are done working": "After Task is Finished",
    "After I finish setting up the current part of the tent (e.g., finishing putting in a pole)": "Break Between Subtasks",
    "When there is a brief pause in the physical setup (e.g., stopping to look at instructions or taking a breath)": "Micro-Break Within Task",
    "After I have finished cycling / reached my destination": "After Task is Finished",
    "After I reach a safe stopping point (e.g., at a traffic light)": "Break Between Subtasks",
    "When I am not actively crossing a street or making a decision about movement": "Micro-Break Within Task",
    "After I am done shopping": "After Task is Finished",
    "Between picking up items on my shopping list": "Micro-Break Within Task",
    "Once I have collected all items and start walking to the checkout": "Break Between Subtasks",
    "Later, when dinner is completely cooked and I am done in the kitchen": "After Task is Finished",
    "When there is a natural pause in the podcast or a brief break in cooking (e.g., waiting for water to boil)": "Micro-Break Within Task",
    "Later, when I am completely done studying": "After Task is Finished",
    "After I finish completing the current study task": "Break Between Subtasks",
    "When I briefly pause my studying/reading to take a sip of coffee or look up": "Micro-Break Within Task",
    "Later, after Jessica has left / our hangout is over": "After Task is Finished",
    "After we completely conclude our current topic of conversation": "Break Between Subtasks",
    "At the next natural pause in the conversation after we resume talking": "Micro-Break Within Task",
    "Other": "Other"
}

TIMING_ORDER = [
    'Immediate', 
    'Micro-Break Within Task', 
    'Break Between Subtasks', 
    'After Task is Finished',
    'Other'
]

FORMAT_ORDER = ['No Audio', 'Earcon', 'Short Speech', 'Rich Speech']

def plot_100_percent_stacked_bar(cross_data, title, filename):
    """Creates a 100% stacked bar chart to easily compare format distributions across timings."""
    fig, ax = plt.subplots(figsize=(11, 7))
    
    # Filter out timings with 0 total responses
    valid_timings = [t for t in TIMING_ORDER if sum(cross_data[t].values()) > 0]
    
    bottoms = np.zeros(len(valid_timings))
    
    for fmt in FORMAT_ORDER:
        values = []
        for t in valid_timings:
            total_for_timing = sum(cross_data[t].values())
            # Calculate percentage
            pct = (cross_data[t][fmt] / total_for_timing * 100) if total_for_timing > 0 else 0
            values.append(pct)
            
        bars = ax.bar(valid_timings, values, bottom=bottoms, 
                      label=fmt, color=FORMAT_COLORS[fmt], edgecolor='white', width=0.6)
        
        # Add text labels inside the bars if the percentage is large enough to read
        for i, bar in enumerate(bars):
            if values[i] > 5:
                # Determine text color for contrast
                text_color = 'white' if fmt in ['Rich Speech', 'Short Speech'] else 'black'
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2,
                        f'{values[i]:.1f}%', ha='center', va='center', 
                        color=text_color, weight='bold', fontsize=10)
                
        bottoms += values

    # Formatting
    ax.set_title(title, fontsize=14, weight='bold', pad=20)
    ax.set_ylabel('Percentage of Preferred Formats (%)', fontsize=12, weight='bold')
    
    # Clean up X-axis labels to prevent overlap
    formatted_labels = [label.replace(' ', '\n', 2) for label in valid_timings]
    ax.set_xticks(range(len(valid_timings)))
    ax.set_xticklabels(formatted_labels, fontsize=11)
    
    # Adjust legend
    ax.legend(title="Audio Format", bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"Saved Stacked Bar Chart: {out_path}")
    plt.close()

def plot_individual_pies(cross_data):
    """Generates a separate pie chart for each timing category."""
    for timing in TIMING_ORDER:
        total = sum(cross_data[timing].values())
        if total == 0:
            continue
            
        labels = []
        sizes = []
        colors = []
        
        for fmt in FORMAT_ORDER:
            if cross_data[timing][fmt] > 0:
                labels.append(fmt)
                sizes.append(cross_data[timing][fmt])
                colors.append(FORMAT_COLORS[fmt])
                
        # Handle <5% label positioning
        display_labels = []
        for lbl, size in zip(labels, sizes):
            pct = (size / total) * 100
            if pct < 5.0:
                display_labels.append(f"{lbl}\n{pct:.1f}% (n={size})")
            else:
                display_labels.append(lbl)

        def custom_autopct(pct):
            return f"{pct:.1f}%\n(n={int(round(pct * total / 100))})" if pct >= 5.0 else ""
            
        fig, ax = plt.subplots(figsize=(8, 6))
        # pyrefly: ignore [bad-unpacking]
        wedges, texts, autotexts = ax.pie(sizes, labels=display_labels, colors=colors, 
                                          autopct=custom_autopct, startangle=90,
                                          textprops=dict(color="black", fontsize=11))
                                          
        for i, autotext in enumerate(autotexts):
            if labels[i] in ['Earcon', 'No Audio']:
                wedges[i].set_edgecolor('white')
            else:
                wedges[i].set_edgecolor('#4A235A')
                wedges[i].set_linewidth(2)
                
            if autotext.get_text() != "":
                autotext.set_color('black' if labels[i] in ['Earcon', 'No Audio'] else 'white')
                autotext.set_weight('bold')
                
        safe_timing_name = timing.replace(' ', '_').replace('-', '_')
        plt.title(f"Format Preference for Timing:\n{timing}", fontsize=13, weight='bold', pad=20)
        plt.tight_layout()
        
        out_path = os.path.join(OUTPUT_DIR, f"04_Pie_{safe_timing_name}.png")
        plt.savefig(out_path, dpi=300)
        print(f"Saved Pie Chart: {out_path}")
        plt.close()

def main():
    if not os.path.exists(JSON_FILE):
        print(f"Error: {JSON_FILE} not found.")
        return
        
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Initialize the nested dictionary
    cross_data = {t: {f: 0 for f in FORMAT_ORDER} for t in TIMING_ORDER}
    
    # Populate the data
    for scene_key, scene_data in data.items():
        # 1. Grab Immediate Data
        imm_data = scene_data.get("macro_timing", {}).get("Immediate", {})
        for raw_fmt, clean_fmt in FORMAT_MAP.items():
            cross_data["Immediate"][clean_fmt] += imm_data.get(raw_fmt, 0)
            
        # 2. Grab Delayed Micro Breakdown Data
        delayed_data = scene_data.get("micro_timing_delayed_breakdown", {})
        for raw_timing, timing_counts in delayed_data.items():
            clean_timing = TIMING_MAP.get(raw_timing, "Other")
            for raw_fmt, clean_fmt in FORMAT_MAP.items():
                cross_data[clean_timing][clean_fmt] += timing_counts.get(raw_fmt, 0)

    # Generate visual outputs
    plot_100_percent_stacked_bar(
        cross_data, 
        "Correlation: Audio Format Preferences across Delivery Timings", 
        "04_Correlation_Stacked_Bar.png"
    )
    
    plot_individual_pies(cross_data)

if __name__ == "__main__":
    main()