import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import streamlit as st
import os
from io import BytesIO
import plotly.io as pio

NOTES_FILE = "daily_notes.csv"
VERSION = "0.2"

# Log version and last modified time once
last_modified = datetime.fromtimestamp(os.path.getmtime(__file__)).strftime('%Y-%m-%d %H:%M:%S')

st.set_page_config(layout="wide")

st.markdown(f"""
    <div style='font-size: 22px; font-weight: bold;'>
        Epcoritamab Calendar - Version {VERSION}  |  Last modified: {last_modified}
    </div>
    <div style='font-size: 18px; font-weight: bold;'>
        This tool visualizes your treatment schedule with clickable dose days.
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    .custom-label {
        font-size: 18px !important;
        font-weight: bold !important;
        margin-bottom: 5px;
    }
    .stButton button, .stDownloadButton button {
        font-size: 18px !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

def load_notes():
    if os.path.exists(NOTES_FILE):
        return pd.read_csv(NOTES_FILE, parse_dates=["Date"])
    return pd.DataFrame(columns=["Date", "Note"])

def save_note(note_date, note_text):
    notes_df = load_notes()
    notes_df = notes_df[notes_df.Date != note_date]  # remove old note for this date if exists
    new_note = pd.DataFrame([[note_date, note_text]], columns=["Date", "Note"])
    notes_df = pd.concat([notes_df, new_note], ignore_index=True)
    notes_df.to_csv(NOTES_FILE, index=False)

# --- Main app logic ---
col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
with col1:
    st.markdown("<div class='custom-label'>Select the date of the first Epcoritamab dose:</div>", unsafe_allow_html=True)
    start_date = st.date_input(" ", datetime(2025, 7, 13), label_visibility="collapsed")
start_date = datetime.combine(start_date, datetime.min.time())

weekly = [start_date + timedelta(days=7 * i) for i in range(4)]
weekly += [weekly[-1] + timedelta(days=7 * (i + 1)) for i in range(5)]
biweekly = [weekly[-1] + timedelta(days=14 * (i + 1)) for i in range(7)]
treatment_dates = weekly + biweekly

doses = ["0.16 mg", "0.8 mg", "3 mg", "48 mg"] + ["48 mg"] * (len(treatment_dates) - 4)
types = ["Step-up"] * 3 + ["First full"] + ["Weekly"] * 5 + ["Biweekly"] * 7
meds = {
    "Step-up": "✔ Dexamethasone<br>✔ Promethazine<br>✔ Acamol<br>✔ Fluids",
    "First full": "✔ Acamol<br>✔ Full-day clinic",
    "Weekly": "✔ Acamol<br>✔ Monitor CBC",
    "Biweekly": "✔ Acamol<br>✔ Clinic check-in",
}

df = pd.DataFrame({"Date": treatment_dates, "Dose": doses, "Type": types})
df["Label"] = df["Date"].dt.strftime('%a %d %b')
df["Medication"] = df["Type"].map(meds)

notes_df = load_notes()

with col2:
    st.markdown("<div class='custom-label'>Select any date to add a note:</div>", unsafe_allow_html=True)
    selected_day = st.date_input(" ", datetime.today(), label_visibility="collapsed")
with col3:
    st.markdown("<div class='custom-label'>Enter note for selected date:</div>", unsafe_allow_html=True)
    note_text = st.text_area(" ", height=40, label_visibility="collapsed")
with col4:
    if st.button("Save Note"):
        save_note(selected_day, note_text)
        st.success(f"Note saved for {selected_day.strftime('%Y-%m-%d')}")

st.markdown("<div class='custom-label'>Filter calendar to show days containing this keyword (optional):</div>", unsafe_allow_html=True)
filter_text = st.text_input(" ", label_visibility="collapsed")

full_dates = pd.date_range(start=start_date, periods=120).to_frame(index=False, name="Date")
full_dates["IsTreatment"] = full_dates["Date"].isin(df["Date"])
full_dates = full_dates.merge(df, on="Date", how="left")
full_dates = full_dates.merge(notes_df, on="Date", how="left")

fig = go.Figure()

cols = 10
spacing = 1.5
row_spacing = 7.5

for i, row in full_dates.iterrows():
    note_highlight = pd.notna(row['Note']) and (filter_text.lower() in row['Note'].lower()) if filter_text else True
    if not note_highlight:
        continue

    col = i % cols
    row_num = i // cols
    x = col * spacing
    y = -row_num * row_spacing

    hover_note = f"<br><b>Note:</b> {row['Note']}" if pd.notna(row['Note']) else ""

    if row["IsTreatment"]:
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers+text',
            marker=dict(size=90, color={
                "Step-up": "#1f77b4", "First full": "#2ca02c",
                "Weekly": "#ff7f0e", "Biweekly": "#9467bd"
            }.get(row["Type"], "gray")),
            text=row["Date"].strftime('%d\n%b'),
            textfont=dict(color='black', size=22),
            textposition='middle center',
            hovertemplate=f"<b>{row['Label']}</b><br>Dose: {row['Dose']}<br><br><b>Checklist:</b><br>{row['Medication']}{hover_note}<extra></extra>",
            showlegend=False
        ))
    else:
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers',
            marker=dict(size=10, color='red' if pd.notna(row['Note']) else 'lightgray'),
            hovertemplate=f"{row['Date'].strftime('%A %d %B')}{hover_note}<br>Click and add notes above<extra></extra>",
            showlegend=False
        ))

fig.update_yaxes(visible=False)
fig.update_xaxes(visible=False)
fig.update_layout(
    title="",
    plot_bgcolor="white",
    hovermode="closest",
    autosize=True,
    height=1080,
    margin=dict(t=10, l=10, r=10, b=10),
    modebar=dict(add=['zoom', 'pan', 'reset'])
)

st.plotly_chart(fig, use_container_width=True)

st.download_button(
    label="Download PDF of calendar",
    data=pio.to_image(fig, format="pdf"),
    file_name="epcoritamab_calendar.pdf",
    mime="application/pdf"
) 
