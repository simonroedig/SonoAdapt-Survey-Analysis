import json
import matplotlib.pyplot as plt
import os
import numpy as np
from matplotlib.patches import Polygon

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

def plot_flow_stacked_bar(cross_data, title, filename):
    """Creates a 100% stacked bar chart with connecting ribbons and column totals."""
    fig, ax = plt.subplots(figsize=(12, 7))
    
    valid_timings = [t for t in TIMING_ORDER if sum(cross_data[t].values()) > 0]
    num_timings = len(valid_timings)
    
    # Calculate the grand total of all responses to figure out column percentages
    overall_total = sum(sum(cross_data[t].values()) for t in valid_timings)
    
    # Pre-calculate percentage values and bottom positions for the stacked bars
    values_matrix = np.zeros((len(FORMAT_ORDER), num_timings))
    bottoms_matrix = np.zeros((len(FORMAT_ORDER), num_timings))
    current_bottom = np.zeros(num_timings)
    
    column_totals = []
    column_pcts = []
    
    for j, t in enumerate(valid_timings):
        total_for_timing = sum(cross_data[t].values())
        column_totals.append(total_for_timing)
        column_pcts.append((total_for_timing / overall_total * 100) if overall_total > 0 else 0)
        
        for i, fmt in enumerate(FORMAT_ORDER):
            pct = (cross_data[t][fmt] / total_for_timing * 100) if total_for_timing > 0 else 0
            values_matrix[i, j] = pct
            bottoms_matrix[i, j] = current_bottom[j]
            current_bottom[j] += pct

    bar_width = 0.5
    x_positions = np.arange(num_timings)
    
    # 1. Draw the connecting ribbons FIRST (so they sit behind the crisp bar borders)
    for i, fmt in enumerate(FORMAT_ORDER):
        for j in range(num_timings - 1):
            if values_matrix[i, j] > 0 or values_matrix[i, j+1] > 0:
                # Right edge of the left bar
                x1 = x_positions[j] + (bar_width / 2)
                y1_bottom = bottoms_matrix[i, j]
                y1_top = y1_bottom + values_matrix[i, j]
                
                # Left edge of the right bar
                x2 = x_positions[j+1] - (bar_width / 2)
                y2_bottom = bottoms_matrix[i, j+1]
                y2_top = y2_bottom + values_matrix[i, j+1]
                
                # Create the polygon connecting them
                poly_x = [x1, x2, x2, x1]
                poly_y = [y1_top, y2_top, y2_bottom, y1_bottom]
                
                poly = Polygon(list(zip(poly_x, poly_y)), 
                               facecolor=FORMAT_COLORS[fmt], 
                               alpha=0.3, # Semi-transparent for the "flow" look
                               edgecolor='none')
                ax.add_patch(poly)

    # 2. Draw the solid stacked bars ON TOP of the ribbons
    for i, fmt in enumerate(FORMAT_ORDER):
        bars = ax.bar(x_positions, values_matrix[i, :], bottom=bottoms_matrix[i, :], 
                      width=bar_width, label=fmt, color=FORMAT_COLORS[fmt], 
                      edgecolor='white', linewidth=1.5)
        
        # Add text labels inside the bars if the percentage is large enough to read
        for j, bar in enumerate(bars):
            val = values_matrix[i, j]
            if val > 5:
                text_color = 'white' if fmt in ['Rich Speech', 'Short Speech'] else 'black'
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2,
                        f'{val:.1f}%', ha='center', va='center', 
                        color=text_color, weight='bold', fontsize=10)

    # 3. Add the Column Totals on top of each bar
    for j, x in enumerate(x_positions):
        ax.text(x, 102, f"Total:\n{column_pcts[j]:.1f}%\n(n={column_totals[j]})", 
                ha='center', va='bottom', fontsize=10, weight='bold', color='#333333')

    # Formatting and aesthetics
    ax.set_title(title, fontsize=14, weight='bold', pad=25)
    ax.set_ylabel('Percentage of Preferred Formats (%)', fontsize=12, weight='bold')
    
    # Increase upper limit of Y-axis so the top labels don't get cut off
    ax.set_ylim(0, 115)
    
    # Clean up X-axis labels to prevent overlap
    formatted_labels = [label.replace(' ', '\n', 2) for label in valid_timings]
    ax.set_xticks(x_positions)
    ax.set_xticklabels(formatted_labels, fontsize=11, weight='bold')
    
    # Remove y-axis ticks above 100 since the bar caps at 100
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    
    # Adjust legend
    ax.legend(title="Audio Format", bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Remove top and right borders for a cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Ensure it saves perfectly
    plt.tight_layout()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"Saved Flow Chart: {out_path}")
    plt.close()


def main():
    if not os.path.exists(JSON_FILE):
        print(f"Error: {JSON_FILE} not found.")
        return
        
    print(f"Reading data from {JSON_FILE}...")
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Initialize the nested dictionary to hold our cross-tabulated data
    cross_data = {t: {f: 0 for f in FORMAT_ORDER} for t in TIMING_ORDER}
    
    # Populate the data by looping through the JSON
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

    # Generate the visual output
    plot_flow_stacked_bar(
        cross_data, 
        "Shifts in Type Preference Based on Selected Timing\n(Aggregated across all 9 scenarios)", 
        "05_Format_Timing_Flow_Chart.png"
    )

if __name__ == "__main__":
    main()