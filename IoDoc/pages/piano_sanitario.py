import streamlit as st
from datetime import date, datetime, timedelta
import db.queries as q
from notifications.scheduler import (
    schedule_medication, schedule_appointment,
    schedule_exam, schedule_prescription, schedule_monitoring,
)


def _auto_data_prossima(data_u, freq_days):
    """Return data_prossima calculated from data_ultima + freq if not provided."""
    if data_u and freq_days:
        d = data_u if isinstance(data_u, date) else datetime.strptime(data_u, "%Y-%m-%d").date()
        return (d + timedelta(days=freq_days)).strftime("%Y-%m-%d")
    return None

st.title("Piano Sanitario")

FREQ_OPTIONS = {
    "Giornaliero": 1,
    "Settimanale": 7,
    "Mensile": 30,
    "Trimestrale": 90,
    "Semestrale": 180,
    "Annuale": 365,
}
FREQ_LABELS = {v: k for k, v in FREQ_OPTIONS.items()}


def _freq_label(days):
    if days is None:
        return "—"
    return FREQ_LABELS.get(days, f"{days} giorni")


def _date_str(d):
    if not d:
        return None
    if isinstance(d, (date, datetime)):
        return d.strftime("%Y-%m-%d")
    return d


tabs = st.tabs(["Patologie", "Farmaci", "Monitoraggi", "Visite", "Esami", "Ricette"])

# ── TAB 1: Patologie ──────────────────────────────────────────────────────────
with tabs[0]:
    st.subheader("Patologie")
    conditions = q.get_conditions()
    for cond in conditions:
        with st.expander(f"{'✅' if cond['attiva'] else '⬜'} {cond['nome']}", expanded=False):
            with st.form(f"edit_cond_{cond['id']}"):
                nome = st.text_input("Nome", value=cond["nome"])
                data_d = st.date_input(
                    "Data diagnosi",
                    value=datetime.strptime(cond["data_diagnosi"], "%Y-%m-%d").date() if cond["data_diagnosi"] else None,
                    format="DD/MM/YYYY",
                )
                attiva = st.checkbox("Attiva", value=bool(cond["attiva"]))
                note = st.text_area("Note", value=cond["note"] or "")
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Salva modifiche", type="primary"):
                        q.update_condition(cond["id"], nome, _date_str(data_d), attiva, note)
                        st.rerun()
                with col2:
                    if st.form_submit_button("Elimina", type="secondary"):
                        q.delete_condition(cond["id"])
                        st.rerun()

    st.divider()
    st.subheader("Aggiungi patologia")
    with st.form("add_cond"):
        nome = st.text_input("Nome patologia")
        data_d = st.date_input("Data diagnosi (opzionale)", value=None, format="DD/MM/YYYY")
        note = st.text_area("Note")
        if st.form_submit_button("Aggiungi", type="primary"):
            if nome:
                q.add_condition(nome, _date_str(data_d), note=note)
                st.rerun()
            else:
                st.error("Il nome è obbligatorio.")

# ── TAB 2: Farmaci ────────────────────────────────────────────────────────────
with tabs[1]:
    st.subheader("Farmaci")
    medications = q.get_medications()
    for med in medications:
        schedules = q.get_schedules_for_medication(med["id"])
        orari_str = ", ".join(s["orario"] for s in schedules) or "—"
        label = f"{'✅' if med['attivo'] else '⬜'} {med['nome']} {med['dosaggio'] or ''} | {orari_str}"
        with st.expander(label, expanded=False):
            with st.form(f"edit_med_{med['id']}"):
                nome = st.text_input("Nome farmaco", value=med["nome"])
                dosaggio = st.text_input("Dosaggio", value=med["dosaggio"] or "")
                data_i = st.date_input(
                    "Data inizio",
                    value=datetime.strptime(med["data_inizio"], "%Y-%m-%d").date() if med["data_inizio"] else None,
                    format="DD/MM/YYYY",
                )
                data_f = st.date_input(
                    "Data fine (opzionale)",
                    value=datetime.strptime(med["data_fine"], "%Y-%m-%d").date() if med["data_fine"] else None,
                    format="DD/MM/YYYY",
                )
                attivo = st.checkbox("Attivo", value=bool(med["attivo"]))
                note = st.text_area("Note", value=med["note"] or "")
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Salva modifiche", type="primary"):
                        q.update_medication(med["id"], nome, dosaggio, _date_str(data_i), _date_str(data_f), attivo, note)
                        st.rerun()
                with col2:
                    if st.form_submit_button("Elimina farmaco", type="secondary"):
                        q.delete_medication(med["id"])
                        st.rerun()

            st.markdown("**Orari di assunzione**")
            for s in schedules:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"- {s['orario']}")
                with col2:
                    if st.button("Rimuovi", key=f"rm_sch_{s['id']}"):
                        q.delete_schedule(s["id"])
                        st.rerun()

            with st.form(f"add_sch_{med['id']}"):
                new_orario = st.time_input("Nuovo orario")
                if st.form_submit_button("Aggiungi orario"):
                    orario_str = new_orario.strftime("%H:%M")
                    sch_id = q.add_schedule(med["id"], orario_str)
                    schedule_medication(sch_id, med["nome"], orario_str)
                    st.rerun()

    st.divider()
    st.subheader("Aggiungi farmaco")
    with st.form("add_med"):
        nome = st.text_input("Nome farmaco")
        dosaggio = st.text_input("Dosaggio (es. 10mg)")
        data_i = st.date_input("Data inizio", value=date.today(), format="DD/MM/YYYY")
        note = st.text_area("Note")
        orario_nuovo = st.time_input("Primo orario di assunzione (opzionale)")
        add_orario = st.checkbox("Aggiungi questo orario")
        if st.form_submit_button("Aggiungi farmaco", type="primary"):
            if nome:
                med_id = q.add_medication(nome, dosaggio, _date_str(data_i), note=note)
                if add_orario:
                    orario_str = orario_nuovo.strftime("%H:%M")
                    sch_id = q.add_schedule(med_id, orario_str)
                    schedule_medication(sch_id, nome, orario_str)
                st.rerun()
            else:
                st.error("Il nome è obbligatorio.")

# ── TAB 3: Monitoraggi ────────────────────────────────────────────────────────
with tabs[2]:
    st.subheader("Monitoraggi periodici")
    tasks = q.get_monitoring_tasks()
    for t in tasks:
        with st.expander(f"{t['tipo']} — {t['orario'] or '—'}", expanded=False):
            with st.form(f"edit_mon_{t['id']}"):
                tipo = st.text_input("Tipo misurazione", value=t["tipo"])
                freq_label = st.selectbox(
                    "Frequenza",
                    list(FREQ_OPTIONS.keys()),
                    index=list(FREQ_OPTIONS.values()).index(t["frequenza_giorni"]) if t["frequenza_giorni"] in FREQ_OPTIONS.values() else 0,
                )
                orario = st.time_input(
                    "Orario",
                    value=datetime.strptime(t["orario"], "%H:%M").time() if t["orario"] else datetime.now().replace(minute=0).time(),
                )
                note = st.text_area("Note", value=t["note"] or "")
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Salva modifiche", type="primary"):
                        orario_str = orario.strftime("%H:%M")
                        q.update_monitoring_task(t["id"], tipo, FREQ_OPTIONS[freq_label], orario_str, note)
                        schedule_monitoring(t["id"], tipo, orario_str)
                        st.rerun()
                with col2:
                    if st.form_submit_button("Elimina", type="secondary"):
                        q.delete_monitoring_task(t["id"])
                        st.rerun()

    st.divider()
    st.subheader("Aggiungi monitoraggio")
    with st.form("add_mon"):
        tipo = st.text_input("Tipo (es. Pressione arteriosa)")
        freq_label = st.selectbox("Frequenza", list(FREQ_OPTIONS.keys()))
        orario = st.time_input("Orario")
        note = st.text_area("Note")
        if st.form_submit_button("Aggiungi", type="primary"):
            if tipo:
                orario_str = orario.strftime("%H:%M")
                task_id = q.add_monitoring_task(tipo, FREQ_OPTIONS[freq_label], orario_str, note)
                schedule_monitoring(task_id, tipo, orario_str)
                st.rerun()
            else:
                st.error("Il tipo è obbligatorio.")

# ── TAB 4: Visite ─────────────────────────────────────────────────────────────
with tabs[3]:
    st.subheader("Visite specialistiche")
    appointments = q.get_appointments()
    for a in appointments:
        with st.expander(f"{a['specialista']} — ultima: {a['data_ultima'] or '—'}", expanded=False):
            with st.form(f"edit_appt_{a['id']}"):
                specialista = st.text_input("Specialista", value=a["specialista"])
                freq_label = st.selectbox(
                    "Frequenza",
                    ["—"] + list(FREQ_OPTIONS.keys()),
                    index=(list(FREQ_OPTIONS.values()).index(a["frequenza_giorni"]) + 1) if a["frequenza_giorni"] in (FREQ_OPTIONS.values() if a["frequenza_giorni"] else []) else 0,
                )
                data_u = st.date_input(
                    "Data ultima visita",
                    value=datetime.strptime(a["data_ultima"], "%Y-%m-%d").date() if a["data_ultima"] else None,
                    format="DD/MM/YYYY",
                )
                note = st.text_area("Note", value=a["note"] or "")
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Salva modifiche", type="primary"):
                        freq_days = FREQ_OPTIONS.get(freq_label)
                        data_p_str = _auto_data_prossima(data_u, freq_days)
                        q.update_appointment(a["id"], specialista, freq_days, _date_str(data_u), data_p_str, note)
                        if data_p_str:
                            schedule_appointment(a["id"], specialista, data_p_str)
                            st.info(f"Prossima visita calcolata: {data_p_str}")
                        st.rerun()
                with col2:
                    if st.form_submit_button("Elimina", type="secondary"):
                        q.delete_appointment(a["id"])
                        st.rerun()

    st.divider()
    st.subheader("Aggiungi visita")
    with st.form("add_appt"):
        specialista = st.text_input("Specialista")
        freq_label = st.selectbox("Frequenza", ["—"] + list(FREQ_OPTIONS.keys()))
        data_u_new = st.date_input("Data ultima visita (opzionale)", value=None, format="DD/MM/YYYY")
        note = st.text_area("Note")
        if st.form_submit_button("Aggiungi", type="primary"):
            if specialista:
                freq_days = FREQ_OPTIONS.get(freq_label)
                data_p_str = _auto_data_prossima(data_u_new, freq_days)
                appt_id = q.add_appointment(specialista, freq_days, data_ultima=_date_str(data_u_new),
                                            data_prossima=data_p_str, note=note)
                if data_p_str:
                    schedule_appointment(appt_id, specialista, data_p_str)
                    st.info(f"Prossima visita calcolata: {data_p_str}")
                st.rerun()
            else:
                st.error("Lo specialista è obbligatorio.")

# ── TAB 5: Esami ─────────────────────────────────────────────────────────────
with tabs[4]:
    st.subheader("Esami e analisi")
    exams = q.get_exams()
    for e in exams:
        with st.expander(f"{e['tipo']} — ultimo: {e['data_ultima'] or '—'}", expanded=False):
            with st.form(f"edit_exam_{e['id']}"):
                tipo = st.text_input("Tipo esame", value=e["tipo"])
                freq_label = st.selectbox(
                    "Frequenza",
                    ["—"] + list(FREQ_OPTIONS.keys()),
                    index=(list(FREQ_OPTIONS.values()).index(e["frequenza_giorni"]) + 1) if e["frequenza_giorni"] in (FREQ_OPTIONS.values() if e["frequenza_giorni"] else []) else 0,
                )
                data_u = st.date_input(
                    "Data ultimo esame",
                    value=datetime.strptime(e["data_ultima"], "%Y-%m-%d").date() if e["data_ultima"] else None,
                    format="DD/MM/YYYY",
                )
                note = st.text_area("Note", value=e["note"] or "")
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Salva modifiche", type="primary"):
                        freq_days = FREQ_OPTIONS.get(freq_label)
                        data_p_str = _auto_data_prossima(data_u, freq_days)
                        q.update_exam(e["id"], tipo, freq_days, _date_str(data_u), data_p_str, note)
                        if data_p_str:
                            schedule_exam(e["id"], tipo, data_p_str)
                            st.info(f"Prossimo esame calcolato: {data_p_str}")
                        st.rerun()
                with col2:
                    if st.form_submit_button("Elimina", type="secondary"):
                        q.delete_exam(e["id"])
                        st.rerun()

    st.divider()
    st.subheader("Aggiungi esame")
    with st.form("add_exam"):
        tipo = st.text_input("Tipo esame (es. Emocromo)")
        freq_label = st.selectbox("Frequenza", ["—"] + list(FREQ_OPTIONS.keys()))
        data_u_new = st.date_input("Data ultimo esame (opzionale)", value=None, format="DD/MM/YYYY")
        note = st.text_area("Note")
        if st.form_submit_button("Aggiungi", type="primary"):
            if tipo:
                freq_days = FREQ_OPTIONS.get(freq_label)
                data_p_str = _auto_data_prossima(data_u_new, freq_days)
                exam_id = q.add_exam(tipo, freq_days, data_ultima=_date_str(data_u_new), data_prossima=data_p_str, note=note)
                if data_p_str:
                    schedule_exam(exam_id, tipo, data_p_str)
                    st.info(f"Prossimo esame calcolato: {data_p_str}")
                st.rerun()
            else:
                st.error("Il tipo è obbligatorio.")

# ── TAB 6: Ricette ────────────────────────────────────────────────────────────
with tabs[5]:
    st.subheader("Ricette e rinnovi")
    prescriptions = q.get_prescriptions()
    for p in prescriptions:
        with st.expander(f"{p['farmaco']} — ultimo rinnovo: {p['data_ultima'] or '—'}", expanded=False):
            with st.form(f"edit_pres_{p['id']}"):
                farmaco = st.text_input("Farmaco", value=p["farmaco"])
                freq_label = st.selectbox(
                    "Frequenza rinnovo",
                    ["—"] + list(FREQ_OPTIONS.keys()),
                    index=(list(FREQ_OPTIONS.values()).index(p["frequenza_giorni"]) + 1) if p["frequenza_giorni"] in (FREQ_OPTIONS.values() if p["frequenza_giorni"] else []) else 0,
                )
                data_u = st.date_input(
                    "Ultimo rinnovo",
                    value=datetime.strptime(p["data_ultima"], "%Y-%m-%d").date() if p["data_ultima"] else None,
                    format="DD/MM/YYYY",
                )
                note = st.text_area("Note", value=p["note"] or "")
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Salva modifiche", type="primary"):
                        freq_days = FREQ_OPTIONS.get(freq_label)
                        data_p_str = _auto_data_prossima(data_u, freq_days)
                        q.update_prescription(p["id"], farmaco, freq_days, _date_str(data_u), data_p_str, note)
                        if data_p_str:
                            schedule_prescription(p["id"], farmaco, data_p_str)
                            st.info(f"Prossimo rinnovo calcolato: {data_p_str}")
                        st.rerun()
                with col2:
                    if st.form_submit_button("Elimina", type="secondary"):
                        q.delete_prescription(p["id"])
                        st.rerun()

    st.divider()
    st.subheader("Aggiungi ricetta")
    with st.form("add_pres"):
        farmaco = st.text_input("Farmaco")
        freq_label = st.selectbox("Frequenza rinnovo", ["—"] + list(FREQ_OPTIONS.keys()))
        data_u_new = st.date_input("Ultimo rinnovo (opzionale)", value=None, format="DD/MM/YYYY")
        note = st.text_area("Note")
        if st.form_submit_button("Aggiungi", type="primary"):
            if farmaco:
                freq_days = FREQ_OPTIONS.get(freq_label)
                data_p_str = _auto_data_prossima(data_u_new, freq_days)
                pres_id = q.add_prescription(farmaco, freq_days, data_ultima=_date_str(data_u_new),
                                             data_prossima=data_p_str, note=note)
                if data_p_str:
                    schedule_prescription(pres_id, farmaco, data_p_str)
                    st.info(f"Prossimo rinnovo calcolato: {data_p_str}")
                st.rerun()
            else:
                st.error("Il farmaco è obbligatorio.")
