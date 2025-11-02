import streamlit as st
import calendar
import datetime
import json
import os

# --- Seiteneinstellungen ---
st.set_page_config(page_title="Kalender Übersicht & Stundenplan", layout="wide")
st.title("📅 Kalenderübersicht mit Stundenplan")

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

# --- Session State initialisieren ---
if "events" not in st.session_state:
    st.session_state["events"] = load_events()
if "selected_date" not in st.session_state:
    st.session_state["selected_date"] = None

# --- Monat und Jahr auswählen ---
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

st.subheader(f"{calendar.month_name[monat]} {jahr}")

# --- Monatsübersicht: Wochentagsnamen ---
weekday_names = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
cols = st.columns(7)
for i, wname in enumerate(weekday_names):
    cols[i].markdown(f"**{wname}**")

# --- Monatsübersicht: Tage anzeigen ---
for week in weeks:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day.month != monat:
            cols[i].write(" ")
            continue

        date_key = day.isoformat()
        events_for_day = st.session_state["events"].get(date_key, [])

        # Anzeige der Termine in der Monatsübersicht
        if events_for_day:
            # nur die ersten 2 Termine anzeigen, um Übersicht zu behalten
            summary = "\n".join([f"{e['start']} {e['title']}" for e in events_for_day[:2]])
            if len(events_for_day) > 2:
                summary += f"\n+{len(events_for_day)-2} weitere"
        else:
            summary = ""

        label = f"**{day.day}**\n{summary}"

        if cols[i].button(label, key=f"day_{date_key}"):
            st.session_state["selected_date"] = day

# --- Detaillierte Stundenansicht beim Klick auf Tag ---
if st.session_state["selected_date"]:
    sel_date = st.session_state["selected_date"]
    date_key = sel_date.isoformat()

    st.markdown("---")
    st.subheader(f"🕒 Stundenplan für {sel_date.strftime('%A, %d. %B %Y')}")

    if date_key not in st.session_state["events"]:
        st.session_state["events"][date_key] = []

    # Termine nach Startzeit sortieren
    events_for_day = sorted(st.session_state["events"][date_key], key=lambda e: e["start"])

    # Anzeige aller 24 Stunden
    for hour in range(24):
        hour_str = f"{hour:02d}:00"
        events_in_hour = [e for e in events_for_day if int(e["start"].split(":")[0]) == hour]

        with st.expander(f"{hour_str} — {len(events_in_hour)} Termin(e)"):
            # Bestehende Termine anzeigen
            for idx, e in enumerate(events_in_hour):
                col1, col2, col3 = st.columns([4, 2, 1])
                col1.markdown(f"**{e['title']}**")
                col2.markdown(f"{e['start']} - {e['end']}")
                if col3.button("🗑️ Löschen", key=f"del_{date_key}_{hour}_{idx}"):
                    st.session_state["events"][date_key].remove(e)
                    if not st.session_state["events"][date_key]:
                        del st.session_state["events"][date_key]
                    save_events(st.session_state["events"])
                    st.success("Termin gelöscht")
                    st.rerun()

            # Formular zum Hinzufügen neuer Termine in dieser Stunde
            with st.form(f"form_{date_key}_{hour}", clear_on_submit=True):
                title = st.text_input("Titel des Termins", key=f"title_{date_key}_{hour}")
                col1, col2 = st.columns(2)
                with col1:
                    start_time = st.time_input("Startzeit", datetime.time(hour, 0), key=f"start_{date_key}_{hour}")
                with col2:
                    end_time = st.time_input("Endzeit", datetime.time(min(hour+1,23), 0), key=f"end_{date_key}_{hour}")
                submitted = st.form_submit_button("💾 Termin speichern")

                if submitted:
                    if not title.strip():
                        st.warning("Bitte Titel eingeben")
                    elif start_time >= end_time:
                        st.warning("Endzeit muss nach Startzeit liegen")
                    else:
                        new_event = {
                            "title": title.strip(),
                            "start": start_time.strftime("%H:%M"),
                            "end": end_time.strftime("%H:%M")
                        }
                        st.session_state["events"].setdefault(date_key, []).append(new_event)
                        save_events(st.session_state["events"])
                        st.success(f"Termin '{title}' gespeichert!")
                        st.rerun()
