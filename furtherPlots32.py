import json
import matplotlib.pyplot as plt
import os

# ==========================================
# CONFIGURATION
# ==========================================
JSON_FILE = "preferencePlots/scenario_preferences_summary.json"
OUTPUT_DIR = "furtherPlots32"

# Explicitly tell Matplotlib to use the sans-serif list for all text by default
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Segoe UI Emoji', 'Tahoma', 'DejaVu Sans']

# Define a color palette that shows a logical progression (Immediate -> Micro -> Subtask -> After)
COLORS = {
    'Immediate': '#E74C3C',                 # Red (Action-oriented)
    'Micro-Break Within Task': '#85C1E9',   # Light Blue (Brief pause)
    'Break Between Subtasks': '#2E86C1',    # Medium Blue (Distinct pause)
    'After Task is Finished': '#1B4F72',    # Dark Blue (Complete stop)
    'Other': '#A6A6A6'                      # Grey
}

# Exact mapping from JSON keys to the supervisor's standardized categories
TIMING_MAP = {
    # Scenario A: Home Alone Computer
    "Later, when I am done working": "After Task is Finished",
    "When I briefly pause while writing / thinking": "Micro-Break Within Task",
    "After I finish the current task (e.g., finish writing (part of the) code)": "Break Between Subtasks",

    # Scenario B: Team Meeting
    "Later, when the meeting is over": "After Task is Finished",
    "After the meeting segment I am currently involved in ends": "Break Between Subtasks",
    "When I am not speaking and there is a natural break in conversation": "Micro-Break Within Task",

    # Scenario C: Home Music
    "Later, when I am done with music and relaxing": "After Task is Finished",
    "When I am between songs / during a natural pause in music": "Break Between Subtasks",

    # Scenario D: Tent
    "Later, when the whole tent is set up and we are done working": "After Task is Finished",
    "After I finish setting up the current part of the tent (e.g., finishing putting in a pole)": "Break Between Subtasks",
    "When there is a brief pause in the physical setup (e.g., stopping to look at instructions or taking a breath)": "Micro-Break Within Task",

    # Scenario E: Cycle City
    "After I have finished cycling / reached my destination": "After Task is Finished",
    "After I reach a safe stopping point (e.g., at a traffic light)": "Break Between Subtasks",
    "When I am not actively crossing a street or making a decision about movement": "Micro-Break Within Task",

    # Scenario F: Grocery Shopping
    "After I am done shopping": "After Task is Finished",
    "Between picking up items on my shopping list": "Micro-Break Within Task",
    "Once I have collected all items and start walking to the checkout": "Break Between Subtasks",

    # Scenario G: Cooking Dinner
    "Later, when dinner is completely cooked and I am done in the kitchen": "After Task is Finished",
    "When there is a natural pause in the podcast or a brief break in cooking (e.g., waiting for water to boil)": "Micro-Break Within Task",

    # Scenario H: Study Coffee Shop
    "Later, when I am completely done studying": "After Task is Finished",
    "After I finish completing the current study task": "Break Between Subtasks",
    "When I briefly pause my studying/reading to take a sip of coffee or look up": "Micro-Break Within Task",

    # Scenario I: Quiet Friend Over
    "Later, after Jessica has left / our hangout is over": "After Task is Finished",
    "After we completely conclude our current topic of conversation": "Break Between Subtasks",
    "At the next natural pause in the conversation after we resume talking": "Micro-Break Within Task",

    "Other": "Other"
}

def plot_pie_chart(agg_data, title, filename):
    """Generates and saves the pie chart based on aggregated timing data."""
    labels = []
    sizes = []
    colors = []
    
    # Specify the exact order the slices should appear in the pie chart
    order = [
        'Immediate', 
        'Micro-Break Within Task', 
        'Break Between Subtasks', 
        'After Task is Finished',
        'Other'
    ]
    
    # Filter out categories with 0 values
    for cat in order:
        if agg_data.get(cat, 0) > 0:
            labels.append(cat)
            sizes.append(agg_data[cat])
            colors.append(COLORS[cat])
            
    fig, ax = plt.subplots(figsize=(9, 7))
    
    # Create the pie chart
    # pyrefly: ignore [bad-unpacking]
    wedges, texts, autotexts = ax.pie(  
        sizes, 
        labels=labels, 
        colors=colors, 
        autopct=lambda pct: f"{pct:.1f}%\n(n={int(round(pct * sum(sizes) / 100))})",
        startangle=140, # Angle adjusted for a balanced look
        textprops=dict(color="black", fontsize=11)
    )
    
    # Style the wedges and text inside the pie for readability
    for i, autotext in enumerate(autotexts):
        # Use white text on the darker blue wedges for contrast
        if labels[i] in ['Break Between Subtasks', 'After Task is Finished']:
            autotext.set_color('white')
        else:
            autotext.set_color('black')
            
        wedges[i].set_edgecolor('white')
        wedges[i].set_linewidth(1.5)
        autotext.set_weight('bold')
        
    plt.title(title, fontsize=14, weight='bold', pad=20)
    plt.tight_layout()
    
    # Save the plot
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"Saved plot: {out_path}")
    plt.close()

def main():
    if not os.path.exists(JSON_FILE):
        print(f"Error: {JSON_FILE} not found. Please ensure it is in the same directory.")
        return
        
    print(f"Reading data from {JSON_FILE}...")
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Initialize our clean category counters
    aggregated_timing = {
        'Immediate': 0,
        'Micro-Break Within Task': 0,
        'Break Between Subtasks': 0,
        'After Task is Finished': 0,
        'Other': 0
    }
    
    # Iterate through all 9 scenarios and tally up the numbers
    for scene_key, scene_data in data.items():
        
        # 1. Add "Immediate" totals
        if "Immediate" in scene_data["macro_timing"]:
            aggregated_timing["Immediate"] += scene_data["macro_timing"]["Immediate"]["Total"]
            
        # 2. Add specific "Delayed" breakdowns mapped to our broader categories
        if "micro_timing_delayed_breakdown" in scene_data:
            for specific_timing, counts in scene_data["micro_timing_delayed_breakdown"].items():
                mapped_category = TIMING_MAP.get(specific_timing, "Other")
                aggregated_timing[mapped_category] += counts["Total"]

    # Generate the plot
    plot_pie_chart(
        aggregated_timing, 
        "Overall Timing Preference\n(Independent of Context)", 
        "02_Overall_Timing_Preference.png"
    )

if __name__ == "__main__":
    main()