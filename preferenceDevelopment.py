import matplotlib.pyplot as plt
import os
import numpy as np
from matplotlib.patches import Polygon

# ==========================================
# CONFIGURATION
# ==========================================
OUTPUT_DIR = "furtherPlots32"

# Explicitly tell Matplotlib to use the sans-serif list for all text by default
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Segoe UI Emoji', 'Tahoma', 'DejaVu Sans']

# Format Colors matching previous visualizations
FORMAT_COLORS = {
    'No Audio': '#A6A6A6',      # Grey
    'Earcon': '#FFC300',        # Yellow
    'Short Speech': '#AF7AC5',  # Light Purple
    'Rich Speech': '#694487'    # Dark Purple
}

FORMAT_ORDER = ['No Audio', 'Earcon', 'Short Speech', 'Rich Speech']

STAGES_ORDER = [
    'Stage 1: Independent\n(Initial Preference)', 
    'Stage 2: Scenario-Based\n(Aggregated)', 
    'Stage 3: Timing-Based\n(Aggregated)'
]

# Hardcoded data based on your provided stats
SURVEY_DATA = {
    'Stage 1: Independent\n(Initial Preference)': {
        'Rich Speech': 17,
        'Short Speech': 10,
        'No Audio': 6,
        'Earcon': 4
    },
    'Stage 2: Scenario-Based\n(Aggregated)': {
        'Earcon': 109,
        'Rich Speech': 95,
        'No Audio': 72,
        'Short Speech': 57
    },
    'Stage 3: Timing-Based\n(Aggregated)': {
        'Rich Speech': 165,
        'Earcon': 94,
        'Short Speech': 69,
        'No Audio': 5
    }
}

def plot_development_flow(data, title, filename):
    """Creates a 100% stacked bar chart showing the flow of preference over stages."""
    fig, ax = plt.subplots(figsize=(11, 7)) # Slightly wider to accommodate side labels
    
    num_stages = len(STAGES_ORDER)
    
    # Pre-calculate percentage values and bottom positions for the stacked bars
    values_matrix = np.zeros((len(FORMAT_ORDER), num_stages))
    bottoms_matrix = np.zeros((len(FORMAT_ORDER), num_stages))
    current_bottom = np.zeros(num_stages)
    
    column_totals = []
    
    for j, stage in enumerate(STAGES_ORDER):
        total_for_stage = sum(data[stage].values())
        column_totals.append(total_for_stage)
        
        for i, fmt in enumerate(FORMAT_ORDER):
            # Calculate percentages precisely
            pct = (data[stage][fmt] / total_for_stage * 100) if total_for_stage > 0 else 0
            values_matrix[i, j] = pct
            bottoms_matrix[i, j] = current_bottom[j]
            current_bottom[j] += pct

    bar_width = 0.4
    x_positions = np.arange(num_stages)
    
    # 1. Draw the connecting ribbons FIRST (so they sit behind the crisp bar borders)
    for i, fmt in enumerate(FORMAT_ORDER):
        for j in range(num_stages - 1):
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
                      edgecolor='white', linewidth=1.5, zorder=4)
        
        # Add text labels inside the bars if the percentage is large enough to read
        for j, bar in enumerate(bars):
            val = values_matrix[i, j]
            if val > 3:  
                text_color = 'white' if fmt in ['Rich Speech', 'Short Speech'] else 'black'
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2,
                        f'{val:.1f}%', ha='center', va='center', 
                        color=text_color, weight='bold', fontsize=11, zorder=5)

    # 3. Add the Column Totals on top of each bar
    for j, x in enumerate(x_positions):
        ax.text(x, 102, f"Total responses:\nn={column_totals[j]}", 
                ha='center', va='bottom', fontsize=11, weight='bold', color='#333333')

    # 4. Add "Overall Speech" Brackets on the left of each bar
    for j, stage in enumerate(STAGES_ORDER):
        # Index 2 is 'Short Speech', Index 3 is 'Rich Speech'
        speech_bottom = bottoms_matrix[2, j]
        speech_top = bottoms_matrix[3, j] + values_matrix[3, j]
        
        # Calculate combined stats perfectly matched to the visual rounded labels
        raw_short = SURVEY_DATA[stage]['Short Speech']
        raw_rich = SURVEY_DATA[stage]['Rich Speech']
        total_for_stage = column_totals[j]
        
        short_pct = round((raw_short / total_for_stage) * 100, 1)
        rich_pct = round((raw_rich / total_for_stage) * 100, 1)
        combined_pct = short_pct + rich_pct
        combined_n = raw_short + raw_rich
        
        bracket_x = x_positions[j] - (bar_width / 2) - 0.015
        cap_len = 0.05
        
        # Draw the vertical line for the bracket
        ax.plot([bracket_x, bracket_x], [speech_bottom, speech_top], color='#4A235A', lw=2.5, zorder=6)
        # Draw the top horizontal cap
        ax.plot([bracket_x, bracket_x + cap_len], [speech_top, speech_top], color='#4A235A', lw=2.5, zorder=6)
        # Draw the bottom horizontal cap
        ax.plot([bracket_x, bracket_x + cap_len], [speech_bottom, speech_bottom], color='#4A235A', lw=2.5, zorder=6)
        
        # Draw the text box containing the summary
        ax.text(bracket_x - 0.04, (speech_bottom + speech_top) / 2, 
                f"Overall Speech\n{combined_pct:.1f}%\n(n={combined_n})", 
                ha='right', va='center', color='#4A235A', weight='bold', fontsize=10,
                bbox=dict(boxstyle="round,pad=0.4", fc="#F5EEF8", ec="#4A235A", lw=1.5),
                zorder=7)

    # Formatting and aesthetics
    ax.set_title(title, fontsize=14, weight='bold', pad=30)
    ax.set_ylabel('Percentage of Preferred Formats (%)', fontsize=12, weight='bold')
    
    # Adjust axes limits to fit the new left-aligned brackets cleanly
    ax.set_ylim(0, 115)
    ax.set_xlim(-0.7, num_stages - 0.4)
    
    # Set X-axis labels
    ax.set_xticks(x_positions)
    ax.set_xticklabels(STAGES_ORDER, fontsize=12, weight='bold')
    
    # Remove y-axis ticks above 100 since the bar caps at 100
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    
    # Adjust legend
    ax.legend(title="Audio Format", bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=11, title_fontsize=12)
    
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
    print("Generating preference development chart...")
    plot_development_flow(
        SURVEY_DATA, 
        "Evolution of Important/Urgent Notification Type Preferences Throughout the Survey", 
        "06_Preference_Development_Flow.png"
    )

if __name__ == "__main__":
    main()