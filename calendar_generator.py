import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import os
from io import BytesIO
import plotly.io as pio

NOTES_FILE = "daily_notes.csv"


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


def generate_calendar_html():
    # Ask user to select start date
    start_date = st.date_input("Select the date of the first Epcoritamab dose:", datetime(2025, 7, 13))
    start_date = datetime.combine(start_date, datetime.min.time())

    # Create treatment dates
    weekly = [start_date + timedelta(days=7 * i) for i in range(4)]
    weekly += [weekly[-1] + timedelta(days=7 * (i + 1)) for i in range(5)]
    biweekly = [weekly[-1] + timedelta(days=14 * (i + 1)) for i in range(7)]
    treatment_dates = weekly + biweekly

    doses = ["0.16 mg", "0.8 mg", "3 mg", "48 mg"] + ["48 mg"] * (len(treatment_dates) - 4)
    types = ["Step-up"] * 3 + ["First full"] + ["Weekly"] * 5 + ["Biweekly"] * 7
    meds = {
        "Step-up": "\u2713 Dexamethasone<br>\u2713 Promethazine<br>\u2713 Acamol<br>\u2713 Fluids",
        "First full": "\u2713 Acamol<br>\u2713 Full-day clinic",
        "Weekly": "\u2713 Acamol<br>\u2713 Monitor CBC",
        "Biweekly": "\u2713 Acamol<br>\u2713 Clinic check-in",
    }

    df = pd.DataFrame({
        "Date": treatment_dates,
        "Dose": doses,
        "Type": types
    })
    df["Label"] = df["Date"].dt.strftime('%a %d %b')
    df["Medication"] = df["Type"].map(meds)

    # Load saved notes
    notes_df = load_notes()

    # Select a date to annotate
    selected_day = st.date_input("Select any date to add a note:")
    note_text = st.text_area("Enter note for selected date:")
    if st.button("Save Note"):
        save_note(selected_day, note_text)
        st.success(f"Note saved for {selected_day.strftime('%Y-%m-%d')}")

    # Optional filter for notes
    filter_text = st.text_input("Filter calendar to show days containing this keyword (optional):")

    # Create full range of dates (90 days window)
    full_dates = pd.date_range(start=start_date, periods=120).to_frame(index=False, name="Date")
    full_dates["IsTreatment"] = full_dates["Date"].isin(df["Date"])
    full_dates = full_dates.merge(df, on="Date", how="left")
    full_dates = full_dates.merge(notes_df, on="Date", how="left")

    fig = go.Figure()

    for _, row in full_dates.iterrows():
        note_highlight = pd.notna(row['Note']) and (filter_text.lower() in row['Note'].lower()) if filter_text else True
        hover_note = f"<br><b>Note:</b> {row['Note']}" if pd.notna(row['Note']) else ""

        if not note_highlight:
            continue

        if row["IsTreatment"]:
            fig.add_trace(go.Scatter(
                x=[row["Date"]], y=[1],
                mode='markers+text',
                marker=dict(size=40, color={
                    "Step-up": "#1f77b4", "First full": "#2ca02c",
                    "Weekly": "#ff7f0e", "Biweekly": "#9467bd"
                }.get(row["Type"], "gray")),
                text=row["Date"].strftime('%d\n%b'),
                textposition='middle center',
                hovertemplate=f"<b>{row['Label']}</b><br>Dose: {row['Dose']}<br><br><b>Checklist:</b><br>{row['Medication']}{hover_note}<extra></extra>",
                showlegend=False
            ))
        else:
            fig.add_trace(go.Scatter(
                x=[row["Date"]], y=[1],
                mode='markers',
                marker=dict(size=10, color='red' if pd.notna(row['Note']) else 'lightgray'),
                hovertemplate=f"{row['Date'].strftime('%A %d %B')}{hover_note}<br>Click and add notes above<extra></extra>",
                showlegend=False
            ))

    fig.update_yaxes(visible=False)
    fig.update_layout(title="", plot_bgcolor="white", hovermode="closest", height=700)

    st.download_button(
        label="Download PDF of calendar",
        data=pio.to_image(fig, format="pdf"),
        file_name="epcoritamab_calendar.pdf",
        mime="application/pdf"
    )

    return fig.to_html(full_html=False)
