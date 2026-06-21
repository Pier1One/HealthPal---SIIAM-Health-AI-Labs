import streamlit as st
from datetime import date, datetime
import db.queries as q

st.title("Profilo Paziente")

user = q.get_user()

# Defaults
_nome = user["nome"] or "" if user else ""
_data_nascita = None
if user and user["data_nascita"]:
    try:
        _data_nascita = datetime.strptime(user["data_nascita"], "%Y-%m-%d").date()
    except ValueError:
        pass
_sesso = user["sesso"] or "M" if user else "M"
_altezza = int(user["altezza_cm"]) if user and user["altezza_cm"] else 170
_peso = float(user["peso_kg"]) if user and user["peso_kg"] else 70.0

with st.form("profilo"):
    nome = st.text_input("Nome completo", value=_nome)
    data_nascita = st.date_input(
        "Data di nascita",
        value=_data_nascita,
        min_value=date(1900, 1, 1),
        max_value=date.today(),
        format="DD/MM/YYYY",
    )
    sesso = st.selectbox("Sesso", ["M", "F", "Altro"], index=["M", "F", "Altro"].index(_sesso) if _sesso in ["M", "F", "Altro"] else 0)
    col1, col2 = st.columns(2)
    with col1:
        altezza = st.number_input("Altezza (cm)", min_value=50, max_value=250, value=_altezza)
    with col2:
        peso = st.number_input("Peso (kg)", min_value=10.0, max_value=300.0, value=_peso, step=0.1)

    if st.form_submit_button("Salva profilo", type="primary"):
        q.upsert_user(nome, data_nascita.strftime("%Y-%m-%d") if data_nascita else None, sesso, altezza, peso)
        st.success("Profilo salvato.")

# ── Riepilogo ─────────────────────────────────────────────────────────────────
if user:
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Altezza", f"{user['altezza_cm']} cm" if user["altezza_cm"] else "—")
    with col2:
        st.metric("Peso", f"{user['peso_kg']} kg" if user["peso_kg"] else "—")
    with col3:
        if user["altezza_cm"] and user["peso_kg"]:
            bmi = user["peso_kg"] / ((user["altezza_cm"] / 100) ** 2)
            st.metric("BMI", f"{bmi:.1f}")
