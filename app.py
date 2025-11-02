import streamlit as st
import calendar
import datetime
import json
import os

# --- Seiteneinstellungen ---
st.set_page_config(page_title="Kalender mit Terminplanung", layout="wide")
st.title("📅 Intelligenter Kalender mit Terminplanung")

# --- Speicherdatei ---
SAVE_FILE = "events.json"

# --- Funktionen für Speichern & Laden ---
def load_events():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_events(events):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

# --- Sitzung initialisieren ---
if "events" not in st.session_state:
    st.session_state["events"] = load_events()
if "selected_date" not in st.session_state:
    st.session_state["selected_date"] = None

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
            date_key = day.isoformat()
            has_events = date_key in st.session_state["events"] and len(st.session_state["events"][date_key]) > 0
            emoji = "📌" if has_events else ""
            label = f"{emoji} {day.day}" if st.session_state["selected_date"] != day else f"✅ {day.day}"
            if cols[i].button(label.strip(), key=f"{day}"):
                st.session_state["selected_date"] = day
        else:
            cols[i].write(" ")

# --- Tagesansicht mit Terminverwaltung ---
if st.session_state["selected_date"]:
    sel_date = st.session_state["selected_date"]
    date_key = sel_date.isoformat()

    st.markdown("---")
    st.subheader(f"📆 {sel_date.strftime('%A, %d. %B %Y')}")

    if date_key not in st.session_state["events"]:
        st.session_state["events"][date_key] = []

    # Bestehende Termine sortieren und anzeigen
    events_for_day = sorted(
        st.session_state["events"][date_key],
        key=lambda e: e["start"]
    )

    if events_for_day:
        st.markdown("### 📋 Geplante Termine:")
        for idx, event in enumerate(events_for_day):
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.markdown(f"**{event['title']}**")
            col2.markdown(f"🕒 {event['start']} - {event['end']}")
            if col3.button("🗑️ Löschen", key=f"del_{date_key}_{idx}"):
                st.session_state["events"][date_key].remove(event)
                if not st.session_state["events"][date_key]:
                    del st.session_state["events"][date_key]
                save_events(st.session_state["events"])
                st.success("Termin gelöscht.")
                st.rerun()
    else:
        st.info("Keine Termine für diesen Tag.")

    st.markdown("---")
    st.markdown("### ➕ Neuen Termin hinzufügen")

    # --- Formular für neuen Termin ---
    with st.form(f"add_event_{date_key}", clear_on_submit=True):
        title = st.text_input("Titel des Termins", "")
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.time_input("Startzeit", datetime.time(9, 0))
        with col2:
            end_time = st.time_input("Endzeit", datetime.time(10, 0))
        submitted = st.form_submit_button("💾 Termin speichern")

        if submitted:
            if not title.strip():
                st.warning("Bitte gib einen Titel ein.")
            elif start_time >= end_time:
                st.warning("Endzeit muss nach der Startzeit liegen.")
            else:
                new_event = {
                    "title": title.strip(),
                    "start": start_time.strftime("%H:%M"),
                    "end": end_time.strftime("%H:%M")
                }
                st.session_state["events"][date_key].append(new_event)
                save_events(st.session_state["events"])
                st.success(f"Termin '{title}' gespeichert!")
                st.rerun()
