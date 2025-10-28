import streamlit as st
import calendar
import datetime

# --- Seiteneinstellungen ---
st.set_page_config(page_title="Kalender", layout="centered")

st.title("📅 Mein Kalender (Grundgerüst)")

# --- Auswahl Monat und Jahr ---
today = datetime.date.today()
jahr = st.number_input("Jahr auswählen", min_value=1900, max_value=2100, value=today.year)
monat = st.selectbox(
    "Monat auswählen",
    options=list(range(1, 13)),
    format_func=lambda x: calendar.month_name[x],
    index=today.month - 1
)

# --- Kalenderdaten generieren ---
cal = calendar.Calendar(firstweekday=0)  # Montag als erster Tag
month_days = [day for day in cal.itermonthdates(jahr, monat)]

# --- Wochenweise gruppieren ---
weeks = []
week = []
for day in month_days:
    if len(week) == 7:
        weeks.append(week)
        week = []
    week.append(day)
if week:
    weeks.append(week)

# --- Überschrift ---
st.subheader(f"{calendar.month_name[monat]} {jahr}")

# --- Wochentagsnamen ---
weekday_names = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
cols = st.columns(7)
for i, wname in enumerate(weekday_names):
    cols[i].markdown(f"**{wname}**")

# --- Sitzungsstatus initialisieren ---
if "selected_date" not in st.session_state:
    st.session_state["selected_date"] = None

# --- Kalenderanzeige ---
for week in weeks:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day.month == monat:
            label = f"✅ {day.day}" if st.session_state["selected_date"] == day else str(day.day)
            if cols[i].button(label, key=f"{day}"):
                st.session_state["selected_date"] = day
        else:
            cols[i].write(" ")

# --- Anzeige ausgewähltes Datum ---
if st.session_state["selected_date"]:
    st.info(f"Ausgewähltes Datum: {st.session_state['selected_date'].strftime('%d.%m.%Y')}")
    st.write("📝 Hier kannst du später Termine oder Notizen hinzufügen.")
