import streamlit as st
import calendar
import datetime

# --- Seiteneinstellungen ---
st.set_page_config(page_title="Kalender mit Terminen", layout="centered")

st.title("📅 Mein Kalender mit Terminen")

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
cal = calendar.Calendar(firstweekday=0)
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

# --- Sitzung initialisieren ---
if "selected_date" not in st.session_state:
    st.session_state["selected_date"] = None
if "events" not in st.session_state:
    st.session_state["events"] = {}  # {"YYYY-MM-DD": ["Event 1", "Event 2"]}

# --- Monatsüberschrift ---
st.subheader(f"{calendar.month_name[monat]} {jahr}")

# --- Wochentagsnamen ---
weekday_names = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
cols = st.columns(7)
for i, wname in enumerate(weekday_names):
    cols[i].markdown(f"**{wname}**")

# --- Kalenderanzeige ---
for week in weeks:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day.month == monat:
            label = f"✅ {day.day}" if st.session_state["selected_date"] == day else str(day.day)
            # Button für den Tag
            if cols[i].button(label, key=f"{day}"):
                st.session_state["selected_date"] = day
        else:
            cols[i].write(" ")

# --- Bereich für Termine ---
if st.session_state["selected_date"]:
    sel_date = st.session_state["selected_date"]
    st.markdown("---")
    st.subheader(f"📆 {sel_date.strftime('%A, %d. %B %Y')}")

    # Aktuelle Termine anzeigen
    date_key = sel_date.isoformat()
    events = st.session_state["events"].get(date_key, [])

    if events:
        for i, event in enumerate(events, start=1):
            st.write(f"🕓 {i}. {event}")
    else:
        st.info("Keine Termine für diesen Tag.")

    # Formular zum Hinzufügen eines neuen Termins
    with st.form(f"add_event_{date_key}", clear_on_submit=True):
        new_event = st.text_input("Neuen Termin hinzufügen:")
        submitted = st.form_submit_button("➕ Termin speichern")
        if submitted and new_event.strip():
            st.session_state["events"].setdefault(date_key, []).append(new_event.strip())
            st.success(f"Termin hinzugefügt: {new_event}")
            st.rerun()
