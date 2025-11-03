import streamlit as st
import calendar
import datetime
import json
import os
import requests
from typing import List, Dict

# --- Einstellungen ---
st.set_page_config(page_title="Kalender mit Aktivitätenvorschlägen", layout="wide")
st.title("📅 Kalender mit Aktivitäts-Vorschlägen (MySwitzerland API)")

SAVE_FILE = "events.json"
API_BASE = "https://api.myswitzerland.io"
API_KEY = "52Z9AebZ8p7IKitCg7cgv2KizmVUr91z3kVYX9Y6"  # <-- Dein echter API-Key

# --- Hilfsfunktionen für Laden/Speichern ---
def load_events() -> Dict:
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_events(events: Dict):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


# --- API: Vorschläge holen ---
def get_activity_suggestions(lat: float = None, lon: float = None, limit: int = 3) -> List[Dict]:
    """Holt Vorschläge direkt über die MySwitzerland API"""
    if lat is None or lon is None:
        lat, lon = 47.3769, 8.5417  # Zürich Standardposition

    headers = {"accept": "application/json", "x-api-key": API_KEY}
    endpoint = f"{API_BASE}/v1/points-of-interest"
    params = {
        "latitude": lat,
        "longitude": lon,
        "limit": limit,
    }

    try:
        r = requests.get(endpoint, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        suggestions = []
        items = data.get("items") or data.get("results") or data
        for it in (items[:limit] if isinstance(items, list) else []):
            suggestions.append({
                "title": it.get("name") or it.get("title") or "Unbekannt",
                "type": it.get("category") or it.get("type") or "Aktivität",
                "city": (it.get("address") or {}).get("city", "") if isinstance(it.get("address"), dict) else "",
                "duration_min": 90,
            })
        return suggestions or [{"title": "Keine Vorschläge gefunden", "type": "", "city": "", "duration_min": 60}]
    except Exception as e:
        return [{"title": f"Fehler beim Laden: {e}", "type": "", "city": "", "duration_min": 60}]


# --- Free-slot Finder ---
def parse_time(t_str: str) -> datetime.time:
    return datetime.datetime.strptime(t_str, "%H:%M").time()


def find_free_slots_for_day(events: List[Dict], min_minutes: int = 60) -> List[Dict]:
    day_start = datetime.datetime.combine(datetime.date.today(), datetime.time(0, 0))
    day_end = datetime.datetime.combine(datetime.date.today(), datetime.time(23, 59))
    intervals = []
    for e in events:
        try:
            s = datetime.datetime.combine(datetime.date.today(), parse_time(e["start"]))
            en = datetime.datetime.combine(datetime.date.today(), parse_time(e["end"]))
            if en <= s:
                en = s + datetime.timedelta(minutes=30)
            intervals.append((s, en))
        except Exception:
            continue
    intervals.sort(key=lambda x: x[0])

    free_slots = []
    cursor = day_start
    for s, en in intervals:
        if s > cursor:
            gap = (s - cursor).total_seconds() / 60
            if gap >= min_minutes:
                free_slots.append({"start": cursor.time().strftime("%H:%M"), "end": s.time().strftime("%H:%M"), "duration_min": int(gap)})
        cursor = max(cursor, en)

    if day_end > cursor:
        gap = (day_end - cursor).total_seconds() / 60
        if gap >= min_minutes:
            free_slots.append({"start": cursor.time().strftime("%H:%M"), "end": day_end.time().strftime("%H:%M"), "duration_min": int(gap)})

    return free_slots


# --- App State ---
if "events" not in st.session_state:
    st.session_state["events"] = load_events()
if "selected_date" not in st.session_state:
    st.session_state["selected_date"] = None

# --- UI: Monat & Jahr ---
now = datetime.date.today()
jahr = st.number_input("Jahr auswählen", min_value=1900, max_value=2100, value=now.year)
monat = st.selectbox("Monat auswählen", list(range(1, 13)), index=now.month - 1, format_func=lambda x: calendar.month_name[x])

# Kalender rendern
cal = calendar.Calendar(firstweekday=0)
month_days = [d for d in cal.itermonthdates(jahr, monat)]
weeks = []
week = []
for d in month_days:
    if len(week) == 7:
        weeks.append(week)
        week = []
    week.append(d)
if week:
    weeks.append(week)

st.subheader(f"{calendar.month_name[monat]} {jahr}")
weekday_names = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
cols = st.columns(7)
for i, n in enumerate(weekday_names):
    cols[i].markdown(f"**{n}**")

for w in weeks:
    cols = st.columns(7)
    for i, d in enumerate(w):
        if d.month != monat:
            cols[i].write(" ")
            continue
        key = d.isoformat()
        evs = st.session_state["events"].get(key, [])
        summary = "\n".join([f"{e['start']} {e['title']}" for e in evs[:2]])
        if len(evs) > 2:
            summary += f"\n+{len(evs)-2} weitere"
        label = f"**{d.day}**\n{summary}"
        if cols[i].button(label, key=f"day_{key}"):
            st.session_state["selected_date"] = d

# --- Tagesansicht ---
if st.session_state["selected_date"]:
    sel = st.session_state["selected_date"]
    key = sel.isoformat()
    st.markdown("---")
    st.subheader(f"🕒 Stundenplan für {sel.strftime('%A, %d. %B %Y')}")

    if key not in st.session_state["events"]:
        st.session_state["events"][key] = []

    day_events = sorted(st.session_state["events"][key], key=lambda e: e['start'])

    colA, colB = st.columns([1, 2])
    min_slot = colA.number_input("Minimale Slot-Dauer (Minuten)", min_value=15, max_value=720, value=60)
    if colB.button("🔎 Vorschläge für freie Slots automatisch finden und anzeigen"):
        free = find_free_slots_for_day(day_events, min_minutes=min_slot)
        if not free:
            st.info("Keine freien Slots mit der angegebenen Mindestdauer gefunden.")
        else:
            st.success(f"{len(free)} freier Slot(s) gefunden.")
            for si, slot in enumerate(free):
                st.markdown(f"### Slot {si+1}: {slot['start']} - {slot['end']} ({slot['duration_min']} Min)")
                with st.expander("🎯 Aktivitätenvorschläge anzeigen"):
                    suggestions = get_activity_suggestions(limit=3)
                    for s in suggestions:
                        cols = st.columns([4, 2, 1])
                        cols[0].markdown(f"**{s['title']}** — {s.get('type','')} ({s.get('city','')})")
                        cols[1].markdown(f"Dauer (min): {s.get('duration_min', 60)}")
                        if cols[2].button("➕ In Kalender eintragen", key=f"add_sugg_{key}_{si}_{s['title']}"):
                            start_dt = datetime.datetime.combine(sel, parse_time(slot['start']))
                            dur = min(s.get('duration_min', 60), slot['duration_min'])
                            end_dt = start_dt + datetime.timedelta(minutes=dur)
                            new_event = {
                                "title": s['title'],
                                "start": start_dt.time().strftime("%H:%M"),
                                "end": end_dt.time().strftime("%H:%M")
                            }
                            st.session_state["events"].setdefault(key, []).append(new_event)
                            save_events(st.session_state["events"])
                            st.success(f"'{s['title']}' in Kalender eingetragen: {new_event['start']} - {new_event['end']}")
                            st.experimental_rerun()

    st.markdown("---")
    st.markdown("### Übersicht (alle 24 Stunden)")
    for hour in range(24):
        hstr = f"{hour:02d}:00"
        in_hour = [e for e in day_events if int(e['start'].split(":")[0]) == hour]
        with st.expander(f"{hstr} — {len(in_hour)} Termin(e)"):
            if in_hour:
                for idx, e in enumerate(in_hour):
                    c1, c2, c3 = st.columns([4,2,1])
                    c1.markdown(f"**{e['title']}**")
                    c2.markdown(f"{e['start']} - {e['end']}")
                    if c3.button("🗑️ Löschen", key=f"del_{key}_{hour}_{idx}"):
                        st.session_state["events"][key].remove(e)
                        if not st.session_state["events"][key]:
                            del st.session_state["events"][key]
                        save_events(st.session_state["events"])
                        st.success("Termin gelöscht")
                        st.experimental_rerun()
            else:
                st.caption("Keine Termine in dieser Stunde.")
            with st.form(f"add_form_{key}_{hour}", clear_on_submit=True):
                title = st.text_input("Titel des Termins", key=f"t_{key}_{hour}")
                c1, c2 = st.columns(2)
                with c1:
                    start_time = st.time_input("Startzeit", datetime.time(hour, 0), key=f"s_{key}_{hour}")
                with c2:
                    end_time = st.time_input("Endzeit", datetime.time(min(hour+1,23), 0), key=f"e_{key}_{hour}")
                submitted = st.form_submit_button("💾 Termin speichern")
                if submitted:
                    if not title.strip():
                        st.warning("Bitte Titel eingeben")
                    elif start_time >= end_time:
                        st.warning("Endzeit muss nach Startzeit liegen")
                    else:
                        new_event = {"title": title.strip(), "start": start_time.strftime("%H:%M"), "end": end_time.strftime("%H:%M")}
                        st.session_state["events"].setdefault(key, []).append(new_event)
                        save_events(st.session_state["events"])
                        st.success("Termin gespeichert")
                        st.experimental_rerun()

st.markdown("---")
st.caption("Alle Vorschläge werden nun live über die MySwitzerland API (x-api-key Header) geladen.")
