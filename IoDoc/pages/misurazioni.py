import streamlit as st
from datetime import date, datetime
import db.queries as q

st.title("Misurazioni")

TIPI_COMUNI = [
    "Pressione arteriosa",
    "Glicemia",
    "Peso",
    "Temperatura corporea",
    "Frequenza cardiaca",
    "Saturazione O2",
    "Altro",
]

UNITA_DEFAULT = {
    "Pressione arteriosa": "mmHg",
    "Glicemia": "mg/dL",
    "Peso": "kg",
    "Temperatura corporea": "°C",
    "Frequenza cardiaca": "bpm",
    "Saturazione O2": "%",
}

# ── Aggiungi misurazione ───────────────────────────────────────────────────────
with st.expander("Aggiungi nuova misurazione", expanded=True):
    with st.form("add_mis"):
        tipo_sel = st.selectbox("Tipo", TIPI_COMUNI)
        tipo_custom = ""
        if tipo_sel == "Altro":
            tipo_custom = st.text_input("Specifica tipo")
        tipo_finale = tipo_custom if tipo_sel == "Altro" else tipo_sel

        col1, col2 = st.columns(2)
        with col1:
            valore = st.text_input("Valore", placeholder="es. 120/80 o 98")
        with col2:
            unita = st.text_input("Unità", value=UNITA_DEFAULT.get(tipo_finale, ""))

        col3, col4 = st.columns(2)
        with col3:
            data_mis = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")
        with col4:
            ora_mis = st.time_input("Ora", value=datetime.now().replace(second=0, microsecond=0).time())

        note = st.text_input("Note (opzionale)")

        if st.form_submit_button("Salva misurazione", type="primary"):
            if tipo_finale and valore:
                q.add_measurement(
                    tipo_finale,
                    valore,
                    unita,
                    data_mis.strftime("%Y-%m-%d"),
                    ora_mis.strftime("%H:%M"),
                    note,
                )
                st.success("Misurazione salvata.")
                st.rerun()
            else:
                st.error("Tipo e valore sono obbligatori.")

st.divider()

# ── Visualizzazione ───────────────────────────────────────────────────────────
tipi_db = q.get_measurement_types()
filtro = st.selectbox("Filtra per tipo", ["Tutti"] + tipi_db)

misurazioni = q.get_measurements(filtro if filtro != "Tutti" else None)

if not misurazioni:
    st.info("Nessuna misurazione registrata.")
else:
    # Raggruppa per tipo
    current_tipo = None
    for m in misurazioni:
        if m["tipo"] != current_tipo:
            current_tipo = m["tipo"]
            st.subheader(current_tipo)
        col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
        with col1:
            st.write(f"**{m['data']}** {m['ora'] or ''}")
        with col2:
            st.write(f"**{m['valore']}** {m['unita'] or ''}")
        with col3:
            st.caption(m["note"] or "")
        with col4:
            if st.button("🗑️", key=f"del_mis_{m['id']}"):
                q.delete_measurement(m["id"])
                st.rerun()
