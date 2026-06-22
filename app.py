import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re

# --- Page Configuration ---
st.set_page_config(page_title="Smart Glasses Audio Notifs", page_icon="🕶️", layout="wide")

# --- Define Full Likert Scales ---
SCALE_AGREE = [
    'Strongly disagree', 'Disagree', 'Somewhat disagree', 
    'Neither agree nor disagree', 'Somewhat agree', 'Agree', 'Strongly agree'
]
SCALE_APPROPRIATE = [
    'Completely inappropriate', 'Inappropriate', 'Somewhat inappropriate', 
    'Neither appropriate nor inappropriate', 'Somewhat appropriate', 'Appropriate', 'Completely appropriate'
]
SCALE_DETECT = [
    'Very difficult to detect', 'Difficult to detect', 'Somewhat difficult to detect', 
    'Neither easy nor difficult to detect', 'Somewhat easy to detect', 'Easy to detect', 'Very easy to detect'
]
SCALE_DISRUPT = [
    'Not disruptive at all', 'Slightly disruptive', 'Somewhat disruptive', 
    'Moderately disruptive', 'Disruptive', 'Very disruptive', 'Extremely disruptive'
]
SCALE_SOCIAL = [
    'Completely unacceptable', 'Unacceptable', 'Somewhat unacceptable', 
    'Neither acceptable nor unacceptable', 'Somewhat acceptable', 'Acceptable', 'Completely Acceptable'
]
SCALE_IMMERSION = [
    'Very difficult', 'Difficult', 'Somewhat difficult', 
    'Neither easy nor difficult (or just "Neutral")', 'Somewhat easy', 'Easy', 'Very easy'
]
SCALE_ENGLISH = [
    'Cannot understand at all', 'Understand very little', 'Understand somewhat', 
    'Understand moderately well', 'Understand well', 'Understand very well', 'Understand perfectly'
]
SCALE_PREF_MATRIX = [
    'Mute (Do not notify me auditorily at all) 🔕', 
    "Sound Only 'Version 1' 🔔", 
    "Speech 'Version 2' (Sender) 🗣️", 
    "Speech 'Version 3' (Sender + Full/Summarized Content) 🗣️🗣️"
]
SCALE_DELAY_MATRIX = [
    'No delay: Must interrupt me immediately, regardless of my situation.',
    'Brief delay (Seconds): Can wait for a quick safe moment (e.g., until I finish crossing the street, silence).',
    'Moderate delay (Minutes): Can wait until I finish my current task (e.g., finishing an email or a conversation).',
    'Indefinite delay (Hours): Can be withheld entirely until I manually check my phone or ask the device.'
]

# --- Helper Functions ---
@st.cache_data
def load_data(filepath):
    try:
        raw_df = pd.read_excel(filepath)
        descriptions = raw_df.iloc[0].to_dict()
        df = raw_df.iloc[1:].reset_index(drop=True)
        # Clean column names (remove non-breaking spaces)
        df.columns = [str(c).replace('\xa0', ' ').strip() for c in df.columns]
        return df, descriptions
    except Exception as e:
        return None, str(e)

def get_counts_with_ids(df, col, category_order=None):
    """Aggregates counts and maps ResponseIds for chart tooltips."""
    has_id = 'ResponseId' in df.columns
    counts = df[col].value_counts().reset_index()
    counts.columns = [col, 'Count']
    
    if has_id:
        grouped = df.dropna(subset=[col]).groupby(col)['ResponseId'].apply(lambda x: ', '.join(x.astype(str))).reset_index()
        grouped.columns = [col, 'Participants']
        counts = pd.merge(counts, grouped, on=col, how='left')
    else:
        counts['Participants'] = ""
        
    if category_order:
        cat_df = pd.DataFrame({col: category_order})
        counts = pd.merge(cat_df, counts, on=col, how='left').fillna({'Count': 0, 'Participants': ''})
    return counts

def plot_bar(df, col, title, orientation='v', category_order=None):
    if col not in df.columns: return
    
    counts = get_counts_with_ids(df, col, category_order)
    
    fig = px.bar(counts, x=col if orientation=='v' else 'Count', 
                 y='Count' if orientation=='v' else col, 
                 title=title, text='Count', color=col,
                 hover_data=['Participants'],
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    
    if category_order:
        if orientation == 'v':
            fig.update_xaxes(categoryorder='array', categoryarray=category_order)
        else:
            fig.update_yaxes(categoryorder='array', categoryarray=category_order)

    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

def plot_multiple_choice(df, col, title):
    if col not in df.columns: return
    
    flat_records = []
    for _, row in df.dropna(subset=[col]).iterrows():
        items = re.split(r',(?!\s)', str(row[col]))
        for item in items:
            clean_item = item.strip()
            if clean_item:
                flat_records.append({
                    'Response': clean_item, 
                    'Participant': str(row['ResponseId']) if 'ResponseId' in df.columns else ''
                })
                
    flat_df = pd.DataFrame(flat_records)
    if flat_df.empty: return
    
    counts = flat_df.groupby('Response').agg(
        Count=('Participant', 'size'),
        Participants=('Participant', lambda x: ', '.join(x))
    ).reset_index().sort_values('Count', ascending=True)

    fig = px.bar(counts, x='Count', y='Response', orientation='h', title=title, text='Count',
                 color='Response', hover_data=['Participants'], 
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

def plot_scenario_comparison(df, prefix, metric, title, category_order=None):
    col1, col2, col3 = f"{prefix}. {metric}_1", f"{prefix}. {metric}_2", f"{prefix}. {metric}_3"
    if not any(c in df.columns for c in [col1, col2, col3]): return

    counts_dict = []
    versions = {'🔔 V1 (Sound)': col1, '🗣️ V2 (Sender)': col2, '🗣️🗣️ V3 (Full)': col3}
    
    for name, col in versions.items():
        if col in df.columns:
            merged = get_counts_with_ids(df, col, category_order)
            merged['Version'] = name
            merged.rename(columns={col: 'Rating'}, inplace=True)
            counts_dict.append(merged)
            
    counts_df = pd.concat(counts_dict)
    fig = px.bar(counts_df, x='Rating', y='Count', color='Version', barmode='group', title=title, 
                 hover_data=['Participants'],
                 color_discrete_sequence=['#F4D03F', '#AF7AC5', '#5B2C6F'])
                 
    if category_order:
        fig.update_xaxes(categoryorder='array', categoryarray=category_order)
        
    fig.update_layout(xaxis_title="Rating", yaxis_title="Number of Participants", legend_title="Version")
    st.plotly_chart(fig, use_container_width=True)

def plot_matrix(df, cols, labels, title, barmode='group', category_order=None):
    melted = []
    for col, label in zip(cols, labels):
        if col in df.columns:
            merged = get_counts_with_ids(df, col, category_order)
            merged.rename(columns={col: 'Preference'}, inplace=True)
            merged['Message Type'] = label
            melted.append(merged)
    if not melted: return
    
    plot_df = pd.concat(melted)
    fig = px.bar(plot_df, x='Message Type', y='Count', color='Preference', 
                 barmode=barmode, title=title, hover_data=['Participants'],
                 color_discrete_sequence=px.colors.qualitative.Safe,
                 category_orders={'Preference': category_order} if category_order else None)
    st.plotly_chart(fig, use_container_width=True)

def display_text_table(df, text_col, title, extra_cols=None):
    """Helper to display open text cleanly with Participant IDs and related context."""
    if text_col not in df.columns: return
    cols_to_get = ['ResponseId'] + (extra_cols if extra_cols else []) + [text_col]
    available_cols = [c for c in cols_to_get if c in df.columns]
    
    temp_df = df[available_cols].dropna(subset=[text_col])
    temp_df = temp_df[temp_df[text_col].astype(str).str.strip() != ""]
    if temp_df.empty: return
    
    # Prettify column headers
    rename_dict = {'ResponseId': 'Participant ID'}
    if extra_cols:
        for c in extra_cols: rename_dict[c] = c.split('.')[-1].strip()
    
    temp_df = temp_df.rename(columns=rename_dict)
    
    with st.expander(f"📖 {title} ({len(temp_df)} responses)"):
        # Sort by the contextual column if we have one
        if extra_cols and extra_cols[0] in rename_dict:
            temp_df = temp_df.sort_values(by=rename_dict[extra_cols[0]])
        st.dataframe(temp_df, use_container_width=True, hide_index=True)

# --- Main App ---
st.title("🕶️ Auditory Notifications on Smart Glasses - Dashboard")
st.markdown("Interactive analysis of the Qualtrics user study results. **Hover over bars to see Participant IDs.**")

df, descriptions = load_data("data.xlsx")

if df is None:
    st.error("Could not load `data.xlsx`. Make sure it's in the same folder.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("⚙️ Data Filters")
if 'Finished' in df.columns:
    only_finished = st.sidebar.checkbox("Only include 'Finished' responses", value=True)
    if only_finished:
        df = df[df['Finished'].astype(str) == 'True']

if 'Headphones' in df.columns:
    req_headphones = st.sidebar.checkbox("Only users wearing headphones", value=True)
    if req_headphones:
        df = df[df['Headphones'].astype(str).str.contains("Yes", na=False)]

if 'ResponseId' in df.columns:
    all_ids = df['ResponseId'].dropna().tolist()
    selected_ids = st.sidebar.multiselect("Select Participants (ResponseId)", all_ids, default=all_ids)
    df = df[df['ResponseId'].isin(selected_ids)]

st.sidebar.success(f"**{len(df)}** participants matching criteria.")

# --- Dashboard Tabs ---
tabs = st.tabs([
    "👥 Demographics", 
    "📊 Baseline & General Prefs", 
    "🎬 Scenarios (A-F)", 
    "🧮 Final Matrices", 
    "💬 General Feedback"
])

# ==========================================
# TAB 1: Demographics
# ==========================================
with tabs[0]:
    st.header("Participant Demographics")
    c1, c2, c3 = st.columns(3)
    with c1:
        if 'Age' in df.columns:
            fig_age = px.histogram(df, x='Age', title="Age Distribution", nbins=15, hover_data=['ResponseId'], color_discrete_sequence=['#5DADE2'])
            st.plotly_chart(fig_age, use_container_width=True)
    with c2:
        if 'Gender' in df.columns:
            fig_gender = px.pie(df, names='Gender', title="Gender Breakdown", hover_data=['ResponseId'], hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_gender, use_container_width=True)
    with c3:
        plot_bar(df, 'English Skill_1', "English Proficiency", category_order=SCALE_ENGLISH)

    c4, c5 = st.columns(2)
    with c4:
        plot_bar(df, 'Culture', "Country of Origin", orientation='h')
    with c5:
        plot_bar(df, 'Musical Background', "Musical Background", orientation='h')
        
    display_text_table(df, 'Impairment_2_TEXT', "Hearing Impairment Details")

# ==========================================
# TAB 2: Baseline & General Preferences
# ==========================================
with tabs[1]:
    st.header("Baseline Settings & Smart Glass Familiarity")
    
    c1, c2 = st.columns(2)
    with c1:
        plot_bar(df, 'My Notif Settings', "Standard Smartphone Notification Setting", orientation='h')
    with c2:
        plot_multiple_choice(df, 'My Notif SettingsWhy', "Reasons for Chosen Setting")
    
    display_text_table(df, 'My Notif SettingsWhy_6_TEXT', "Other Specific Settings (Text)")

    c3, c4 = st.columns(2)
    with c3:
        plot_bar(df, 'Glass Knowledge_1', "Smart Glass Familiarity")
    with c4:
        plot_bar(df, 'Glass Experience_1', "Smart Glass Experience")

    st.divider()
    st.subheader("Auditory Preferences Independent of Context")
    plot_multiple_choice(df, 'Which Notif Auditory', "Apps Desired for Auditory Notifications via Glasses")
    display_text_table(df, 'Which Notif Auditory_9_TEXT', "Other Specific Apps (Text)")
    
    c5, c6 = st.columns(2)
    with c5:
        plot_bar(df, 'Notif ImprtancUrgent_1', "Only notify me for IMPORTANT messages", category_order=SCALE_AGREE)
    with c6:
        plot_bar(df, 'Notif ImprtancUrgent_2', "Only notify me for URGENT messages", category_order=SCALE_AGREE)
        
    st.divider()
    st.subheader("💬 Contextual Reasoning: Baseline Preference")
    c_pref1, c_pref2 = st.columns(2)
    with c_pref1:
        display_text_table(df, 'Preference Text', "Why prefer chosen version?", extra_cols=['Preference'])
    with c_pref2:
        display_text_table(df, 'Scenes Inappropriate', "Inappropriate Scenarios for preferred version", extra_cols=['Preference'])

    st.divider()
    st.subheader("Attitudes Towards Speech Output")
    c7, c8 = st.columns(2)
    with c7:
        plot_bar(df, 'Speech Opinion_1', "Assumption: If speech, it must be urgent", category_order=SCALE_AGREE)
    with c8:
        plot_bar(df, 'Speech Opinion_2', "Acceptable to read out loud without explicit request?", category_order=SCALE_AGREE)
        
    plot_multiple_choice(df, 'Speech Opinion 2', "Factors influencing attitude towards speech output")
    display_text_table(df, 'Speech Opinion 2_10_TEXT', "Other factors influencing speech attitude (Text)")
    
    c9, c10 = st.columns(2)
    with c9:
        plot_multiple_choice(df, 'Maximum Length', "Maximum Acceptable Length for Spoken Notifications")
        display_text_table(df, 'Maximum Length_7_TEXT', "Other Maximum Length specs (Text)")
    with c10:
        plot_bar(df, 'Summary Acceptance_1', "Acceptance of AI Summarization for LONG messages", category_order=SCALE_AGREE)

# ==========================================
# TAB 3: Scenarios Analysis (A-F)
# ==========================================
with tabs[2]:
    st.header("Contextual Scenarios")
    
    scenarios = {
        'A': 'Home Alone (Computer Work)',
        'B': 'Team Meeting (Office)',
        'C': 'Home Music (Relaxing)',
        'D': 'Coffee Bar (Conversation)',
        'E': 'Cycle City (Traffic)',
        'F': 'Grocery Shopping'
    }
    
    scenario_tabs = st.tabs([f"{k}: {v}" for k, v in scenarios.items()])
    
    for idx, (prefix, name) in enumerate(scenarios.items()):
        with scenario_tabs[idx]:
            st.subheader(f"Scenario {prefix}: {name}")
            
            c1, c2 = st.columns(2)
            with c1:
                plot_scenario_comparison(df, prefix, 'Appropriateness', "Appropriateness", category_order=SCALE_APPROPRIATE)
                plot_scenario_comparison(df, prefix, 'Disruption', "Disruption Level", category_order=SCALE_DISRUPT)
            with c2:
                plot_scenario_comparison(df, prefix, 'Detectability', "Detectability", category_order=SCALE_DETECT)
                plot_scenario_comparison(df, prefix, 'Social', "Social Acceptability", category_order=SCALE_SOCIAL)

            st.divider()
            
            c3, c4, c5 = st.columns(3)
            with c3:
                plot_bar(df, f"{prefix}. Overall", "Overall Preferred Version")
            with c4:
                plot_bar(df, f"{prefix}. Timing", "Preferred Delivery Timing")
            with c5:
                plot_bar(df, f"{prefix}. Timing Follow", "If Delayed, Preferred Version")
                
            st.markdown("**Factors Influencing Choice:**")
            plot_multiple_choice(df, f"{prefix}. Overall Why", f"Why did they choose this? (Scenario {prefix})")
            
            # --- CONTEXTUAL OPEN TEXT TABLES ---
            st.divider()
            st.subheader("💬 Participant Reasoning (Correlated with their Choices)")
            
            col_overall = f"{prefix}. Overall"
            col_overall_txt = f"{prefix}. Why Text"
            display_text_table(df, col_overall_txt, "Reasons for Overall Preference", extra_cols=[col_overall])
            
            display_text_table(df, f"{prefix}. Overall Why_6_TEXT", "Other factors influencing choice (Text)", extra_cols=[col_overall])

            col_timing = f"{prefix}. Timing"
            col_timing_fol = f"{prefix}. Timing Follow"
            col_timing_txt = f"{prefix}. Why Timing Text"
            display_text_table(df, col_timing_txt, "Reasons for Delivery Timing & Delayed Version", extra_cols=[col_timing, col_timing_fol])


# ==========================================
# TAB 4: Final Matrices & System Opinion
# ==========================================
with tabs[3]:
    st.header("Final Notification Matrices")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Delivery Modality Preference Matrix")
        pref_cols = ['Preference Matrix_1', 'Preference Matrix_2', 'Preference Matrix_3', 'Preference Matrix_4']
        pref_labels = ['Simple Ack (e.g. "Ok")', 'Routine Update', 'Great News', 'Time-sensitive / Action req.']
        plot_matrix(df, pref_cols, pref_labels, "Preferred Version by Message Type", category_order=SCALE_PREF_MATRIX)
        
    with c2:
        st.subheader("Interruption Delay Tolerance Matrix")
        delay_cols = ['Delay Matrix_1', 'Delay Matrix_2', 'Delay Matrix_3', 'Delay Matrix_4']
        plot_matrix(df, delay_cols, pref_labels, "Maximum Delay Tolerance by Message Type", category_order=SCALE_DELAY_MATRIX)

    st.divider()
    st.subheader("Overall AI System Opinions")
    c3, c4, c5 = st.columns(3)
    with c3:
        plot_bar(df, 'System Opinion_1', "Such a system would be useful to me", category_order=SCALE_AGREE)
    with c4:
        plot_bar(df, 'System Opinion_2', "I would trust such a system to make the right choice", category_order=SCALE_AGREE)
    with c5:
        plot_bar(df, 'System Opinion_3', "Concerned about system choosing wrong type/moment", category_order=SCALE_AGREE)
        
    plot_bar(df, 'Realistic Feeling_1', "Ease of Immersion (Mental visualization of scenarios)", category_order=SCALE_IMMERSION)

# ==========================================
# TAB 5: General Feedback
# ==========================================
with tabs[4]:
    st.header("💬 General & Additional Open Text Feedback")
    st.info("These responses represent overall feedback and general concerns not tied to a specific scenario.")
    
    display_text_table(df, ' System Opinion Why', "General AI System Concerns")
    display_text_table(df, 'Final', "Final Additional Comments & Thoughts")