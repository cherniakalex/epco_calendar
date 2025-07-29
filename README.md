# Epcoritamab Treatment Calendar

This is a **Streamlit web app** to track and visualize **Epcoritamab treatment schedules** for lymphoma patients.  
It shows clickable treatment days, allows entering daily notes, and exports to PDF for documentation or sharing.

---

## 📅 Features

- Interactive calendar with treatment days marked
- Step-up, full dose, weekly, and biweekly color-coded circles
- Add personal health notes to any date
- Filter view based on note content (e.g. only show fever days)
- Download annotated calendar as a PDF

---

## 🚀 Run Locally

1. Clone this repo:
   ```bash
   git clone https://github.com/your_username/epcoritamab-calendar.git
   cd epcoritamab-calendar

2. Create a virtual environment:
    python -m venv venv
    venv\\Scripts\\activate  # On Windows

3. Install requirements:
    pip install -r requirements.txt

4. Run the app:
    streamlit run app.py


📦 Deployment
You can deploy this app for free using Streamlit Community Cloud.
Just connect your GitHub repo and select app.py as the main file.

📝 Notes Storage
Notes are saved in daily_notes.csv in the local folder. Make sure to back it up if needed.

🔒 Privacy
No external data is stored or transmitted. All notes remain local unless deployed.


