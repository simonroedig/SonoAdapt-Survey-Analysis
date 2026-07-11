import json
import matplotlib.pyplot as plt
import os
import textwrap

# ==========================================
# CONFIGURATION
# ==========================================
JSON_FILE = "preferencePlots/scenario_preferences_summary_othersmerged.json"
OUTPUT_DIR = "preferencePlots/new"

# Fonts
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Segoe UI Emoji', 'Tahoma', 'DejaVu Sans']

# Format mapping for cleaner text in the bracket label
FORMAT_MAP = {
    "Earcon (V1)": "Earcon",
    "Short Speech (V2)": "Short Speech",
    "Rich Speech (V3)": "Rich Speech",
    "None / No Audio": "No Audio"
}

# Mapping the specific scenario texts to the timeline categories
TIMING_MAP = {
    "Later, when I am done working": "After Task is Finished",
    "When I briefly pause while writing / thinking": "Micro-Break",
    "After I finish the current task (e.g., finish writing (part of the) code)": "Subtask Break",
    
    "Later, when the meeting is over": "After Task is Finished",
    "After the meeting segment I am currently involved in ends": "Subtask Break",
    "When I am not speaking and there is a natural break in conversation": "Micro-Break",
    
    "Later, when I am done with music and relaxing": "After Task is Finished",
    "When I am between songs / during a natural pause in music": "Subtask Break", 
    
    "Later, when the whole tent is set up and we are done working": "After Task is Finished",
    "After I finish setting up the current part of the tent (e.g., finishing putting in a pole)": "Subtask Break",
    "When there is a brief pause in the physical setup (e.g., stopping to look at instructions or taking a breath)": "Micro-Break",
    
    "After I have finished cycling / reached my destination": "After Task is Finished",
    "After I reach a safe stopping point (e.g., at a traffic light)": "Subtask Break",
    "When I am not actively crossing a street or making a decision about movement": "Micro-Break",
    
    "After I am done shopping": "After Task is Finished",
    "Between picking up items on my shopping list": "Micro-Break",
    "Once I have collected all items and start walking to the checkout": "Subtask Break",
    
    "Later, when dinner is completely cooked and I am done in the kitchen": "After Task is Finished",
    "When there is a natural pause in the podcast or a brief break in cooking (e.g., waiting for water to boil)": "Micro-Break",
    
    "Later, when I am completely done studying": "After Task is Finished",
    "After I finish completing the current study task": "Subtask Break",
    "When I briefly pause my studying/reading to take a sip of coffee or look up": "Micro-Break",
    
    "Later, after Jessica has left / our hangout is over": "After Task is Finished",
    "After we completely conclude our current topic of conversation": "Subtask Break",
    "At the next natural pause in the conversation after we resume talking": "Micro-Break",
    "Other": "Other"
}

# The explicit timeline order for the X-Axis
TIMING_ORDER = [
    'Immediate', 
    'Micro-Break', 
    'Subtask Break', 
    'After Task is Finished'
]

def get_top_format(macro_data):
    """Helper to extract the total and top format from macro timing dicts."""
    total = macro_data.get("Total", 0)
    format_counts = {k: v for k, v in macro_data.items() if k != "Total"}
    top_format_raw = max(format_counts, key=format_counts.get) if format_counts else "None"
    top_format_clean = FORMAT_MAP.get(top_format_raw, top_format_raw)
    return total, top_format_clean

def plot_timeline_with_dual_brackets(scene_num, scene_name, timing_totals, macro_imm_data, macro_delayed_data, filename):
    """Plots a line chart with two overhead brackets, highlighting the winning macro timing."""
    fig, ax = plt.subplots(figsize=(9, 6), dpi=300)
    
    x_pos = range(len(TIMING_ORDER))
    values = [timing_totals[t] for t in TIMING_ORDER]

    # Draw the main line with markers
    ax.plot(x_pos, values, color='#2980B9', marker='o', linestyle='-', 
            linewidth=3, markersize=10, markerfacecolor='#FFFFFF', 
            markeredgewidth=2.5, zorder=3)
            
    # Add a subtle fill under the line
    ax.fill_between(x_pos, values, color='#2980B9', alpha=0.1, zorder=2)

    # Add text labels right above the markers
    for i, val in enumerate(values):
        if val > 0:
            ax.text(i, val + (max(values)*0.05 if max(values) > 0 else 1), f'n={val}', 
                    ha='center', va='bottom', color='black', weight='bold', fontsize=11)

    # ==========================================
    # DUAL BRACKET LOGIC & HIGHLIGHTING
    # ==========================================
    imm_total, top_imm_format = get_top_format(macro_imm_data)
    delayed_total, top_del_format = get_top_format(macro_delayed_data)
    
    # Determine bracket height (must be above the highest peak on the chart)
    max_val = max(values) if values else 0
    bracket_y = max_val + max(3, max_val * 0.25)
    drop = max(1, bracket_y * 0.05) # How far the bracket "legs" point down
    
    # Define styles for the winning box vs the losing box
    winner_box = dict(facecolor='#EAFaf1', edgecolor='#2ECC71', boxstyle='round,pad=0.5', alpha=0.95, lw=2)
    loser_box = dict(facecolor='#F8F9F9', edgecolor='#CCCCCC', boxstyle='round,pad=0.5', alpha=0.85, lw=1)
    
    # Assign styles based on which total is higher (ties get neutral loser styling)
    imm_style = winner_box if imm_total > delayed_total else loser_box
    del_style = winner_box if delayed_total > imm_total else loser_box

    # --- Draw Immediate Bracket ---
    imm_start, imm_end = -0.2, 0.2
    ax.plot([imm_start, imm_end], [bracket_y, bracket_y], color='#555555', lw=1.5, zorder=4)
    ax.plot([imm_start, imm_start], [bracket_y, bracket_y - drop], color='#555555', lw=1.5, zorder=4)
    ax.plot([imm_end, imm_end], [bracket_y, bracket_y - drop], color='#555555', lw=1.5, zorder=4)
    
    ax.text(0, bracket_y + (drop * 0.5), f"Immediate: n={imm_total}\nTop: {top_imm_format}",
            ha='center', va='bottom', color='#2C3E50', weight='bold', fontsize=9.5,
            bbox=imm_style, zorder=5)

    # --- Draw Delayed Bracket ---
    del_start, del_end = 1, 3
    ax.plot([del_start, del_end], [bracket_y, bracket_y], color='#555555', lw=1.5, zorder=4)
    ax.plot([del_start, del_start], [bracket_y, bracket_y - drop], color='#555555', lw=1.5, zorder=4)
    ax.plot([del_end, del_end], [bracket_y, bracket_y - drop], color='#555555', lw=1.5, zorder=4)
    
    ax.text(2, bracket_y + (drop * 0.5), f"Total Delayed: n={delayed_total}\nTop: {top_del_format}",
            ha='center', va='bottom', color='#2C3E50', weight='bold', fontsize=9.5,
            bbox=del_style, zorder=5)

    # ==========================================
    # FORMATTING
    # ==========================================
    # Updated Title Logic
    ax.set_title(f'Notification Timing Flow\n(Scenario {scene_num}: {scene_name})', fontsize=14, weight='bold', pad=25)
    ax.set_ylabel('Number of Participants', fontsize=12, weight='bold')
    
    # Clean up X-axis labels
    formatted_labels = [textwrap.fill(label, width=15) for label in TIMING_ORDER]
    ax.set_xticks(x_pos)
    ax.set_xticklabels(formatted_labels, fontsize=11, weight='bold')
    
    # Dynamically adjust the Y-limit so the text box never gets cut off at the top
    plt.ylim(0, bracket_y + max(5, bracket_y * 0.4)) 
    
    # Give a tiny bit of extra X margin on the left for the immediate bracket
    plt.xlim(-0.6, 3.5)

    # Clean up spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.3, zorder=1)
    ax.grid(axis='x', linestyle='--', alpha=0.1, zorder=1) 
    
    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(out_path)
    # Removing the redundant plot save print since we're printing the full stats block below
    plt.close()

def main():
    if not os.path.exists(JSON_FILE):
        print(f"Error: {JSON_FILE} not found. Ensure the filename is correct.")
        return
        
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for scene_key, scene_data in data.items():
        scene_name = scene_data["scenario_name"]
        
        # Extract the scenario number from the key (e.g., "Scene_1_Home_Alone_Computer" -> "1")
        scene_num = scene_key.split('_')[1]
        
        # Initialize the dictionary to hold just the totals
        timing_totals = {t: 0 for t in TIMING_ORDER}
        
        # 1. Grab Immediate Total
        macro_imm_data = scene_data.get("macro_timing", {}).get("Immediate", {})
        timing_totals["Immediate"] += macro_imm_data.get("Total", 0)
            
        # 2. Grab Delayed Breakdown Totals and map to the timeline stages
        delayed_breakdown_data = scene_data.get("micro_timing_delayed_breakdown", {})
        for raw_timing, timing_counts in delayed_breakdown_data.items():
            clean_timing = TIMING_MAP.get(raw_timing, "Other")
            
            if clean_timing in TIMING_ORDER:
                timing_totals[clean_timing] += timing_counts.get("Total", 0)

        # 3. Grab the Macro Delayed data
        macro_delayed_data = scene_data.get("macro_timing", {}).get("Delayed", {})
        
        # --- NEW: Print console data summary ---
        imm_total, top_imm_format = get_top_format(macro_imm_data)
        delayed_total, top_del_format = get_top_format(macro_delayed_data)
        
        print(f"\n{'='*50}")
        print(f"SCENARIO {scene_num}: {scene_name.upper()}")
        print(f"{'='*50}")
        print("TIMELINE DISTRIBUTION:")
        for t in TIMING_ORDER:
            print(f"  - {t:<25} : n={timing_totals[t]}")
        
        print("\nAGGREGATED TOTALS & TOP FORMATS:")
        print(f"  - Immediate Total: n={imm_total} (Top Pick: {top_imm_format})")
        print(f"  - Delayed Total  : n={delayed_total} (Top Pick: {top_del_format})")
        print(f"{'-'*50}")

        # Generate the plot for this scene, passing scene_num into the function
        safe_filename = f"Flow_DualBrackets_{scene_key}.png"
        plot_timeline_with_dual_brackets(scene_num, scene_name, timing_totals, macro_imm_data, macro_delayed_data, safe_filename)

    print("\nAll dual-bracket flow charts generated successfully in 'preferencePlots/new'!")

if __name__ == "__main__":
    main()