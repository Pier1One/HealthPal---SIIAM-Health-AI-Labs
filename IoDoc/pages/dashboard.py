import streamlit as st
from datetime import date
import db.queries as q
from notifications.actions import (
    mark_done_appointment, mark_done_exam,
    mark_done_prescription, mark_done_medication_schedule,
)

st.title("Dashboard — Oggi")
st.caption(f"Oggi: {date.today().strftime('%d/%m/%Y')}")

# ── Notifiche in sospeso ──────────────────────────────────────────────────────
sent = q.get_sent_notifications()

if sent:
    st.subheader("Notifiche in sospeso")
    for notif in sent:
        with st.container(border=True):
            col_msg, col_done, col_skip = st.columns([5, 1, 1])
            with col_msg:
                st.write(f"**{notif['messaggio']}**")
                if notif["sent_at"]:
                    sent_dt = notif["sent_at"][:16].replace("T", " ")
                    st.caption(f"Inviata: {sent_dt}")
            with col_done:
                if st.button("Fatto", key=f"done_{notif['id']}", type="primary"):
                    q.mark_notification_done(notif["id"])
                    tipo = notif["tipo"]
                    rid = notif["riferimento_id"]
                    if tipo == "appointment_task":
                        mark_done_appointment(rid)
                    elif tipo == "exam_task":
                        mark_done_exam(rid)
                    elif tipo == "prescription_task":
                        mark_done_prescription(rid)
                    elif tipo == "medication_schedule":
                        mark_done_medication_schedule(rid)
                    st.rerun()
            with col_skip:
                if st.button("Non fatto", key=f"skip_{notif['id']}"):
                    q.mark_notification_skipped(notif["id"])
                    st.rerun()
else:
    st.success("Nessuna notifica in sospeso.")

st.divider()

# ── Riepilogo giornaliero ─────────────────────────────────────────────────────
st.subheader("Farmaci di oggi")
schedules = q.get_all_active_schedules()
if schedules:
    for s in schedules:
        st.write(f"- **{s['orario']}** — {s['farmaco_nome']} {s['dosaggio'] or ''}")
else:
    st.info("Nessun farmaco programmato.")

st.subheader("Prossimi appuntamenti")
today = date.today().isoformat()
appointments = [a for a in q.get_appointments() if a["data_prossima"] and a["data_prossima"] >= today]
if appointments:
    for a in appointments[:5]:
        st.write(f"- **{a['data_prossima']}** — {a['specialista']}")
else:
    st.info("Nessun appuntamento programmato.")

st.subheader("Prossimi esami")
exams = [e for e in q.get_exams() if e["data_prossima"] and e["data_prossima"] >= today]
if exams:
    for e in exams[:5]:
        st.write(f"- **{e['data_prossima']}** — {e['tipo']}")
else:
    st.info("Nessun esame programmato.")

st.divider()

# ── Test notifica ─────────────────────────────────────────────────────────────
with st.expander("🔔 Test notifiche"):
    col_std, col_alarm = st.columns(2)
    with col_std:
        if st.button("Invia notifica di prova (reminder)", use_container_width=True):
            from notifications.notifier import send_notification
            send_notification(
                title="IoDoc — Test",
                message="Le notifiche funzionano correttamente!",
                tipo="appointment_task",
            )
            st.success("Notifica inviata.")
    with col_alarm:
        if st.button("Invia notifica di prova (allarme)", use_container_width=True):
            from notifications.notifier import send_notification
            send_notification(
                title="IoDoc — Test allarme",
                message="Suono allarme farmaci attivo.",
                tipo="medication_schedule",
            )
