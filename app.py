import streamlit as st
import calendar
import datetime
import pandas as pd

# --- Seiteneinstellungen ---
st.set_page_config(page_title="Kalender", layout="centered")

st.title("Mein Kalender (Grundgerüst)")

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
kalender = calendar.Calendar(firstweekday=0)
tage = list(kalender.itermonthdates(jahr, monat))

# --- DataFrame für Anzeige ---
df = pd.DataFrame({
    "Datum": tage,
    "Wochentag": [calendar.day_name[d.weekday()] for d in tage]
})
df = df[df["Datum"].dt.month == monat]  # Nur aktueller Monat

# --- Darstellung ---
st.subheader(f"{calendar.month_name[monat]} {jahr}")

# Raster (7 Spalten, Wochenweise)
cols = st.columns(7)
wochentage = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
for i, wtag in enumerate(wochentage):
    cols[i].markdown(f"**{wtag}**")

# Leeres Raster vorbereiten
for i, tag in enumerate(tage):
    col = cols[tag.weekday()]  # Spalte basierend auf Wochentag
    if tag.month == monat:
        if st.session_state.get("selected_date") == tag:
            button_label = f"✅ {tag.day}"
        else:
            button_label = str(tag.day)

        if col.button(button_label, key=str(tag)):
            st.session_state["selected_date"] = tag
    else:
        col.write(" ")

# --- Anzeige ausgewähltes Datum ---
if "selected_date" in st.session_state:
    st.info(f"Ausgewähltes Datum: {st.session_state['selected_date'].strftime('%d.%m.%Y')}")

    # Platzhalter für zukünftige Features
    st.write("📝 Hier kannst du später Termine oder Notizen hinzufügen.")


