import streamlit as st
from datetime import date, datetime, timedelta
import db.queries as q
from notifications.actions import mark_done_appointment, mark_done_exam, mark_done_prescription

st.title("Timeline")
st.caption("Tutti gli eventi in ordine cronologico.")

today = date.today()
today_str = today.isoformat()
year_end = date(today.year, 12, 31)


def _expand_future(data_prossima_str, freq_giorni):
    """Return all future occurrence dates from data_prossima until end of year."""
    if not data_prossima_str:
        return []
    try:
        d = datetime.strptime(data_prossima_str, "%Y-%m-%d").date()
    except ValueError:
        return []
    dates = []
    if not freq_giorni:
        if d >= today:
            dates.append(d.strftime("%Y-%m-%d"))
        return dates
    while d <= year_end:
        if d >= today:
            dates.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=freq_giorni)
    return dates


# ── Raccoglie tutti gli eventi ────────────────────────────────────────────────
events = []

# Misurazioni (passate)
for m in q.get_measurements():
    events.append({
        "data": m["data"],
        "label": f"Misurazione — {m['tipo']}: {m['valore']} {m['unita'] or ''}",
        "icon": "📊",
        "passato": m["data"] < today_str,
    })

# Appuntamenti
for a in q.get_appointments():
    if a["data_ultima"]:
        events.append({
            "data": a["data_ultima"],
            "label": f"Visita effettuata — {a['specialista']}",
            "icon": "✅",
            "passato": True,
        })
    for d_str in _expand_future(a["data_prossima"], a["frequenza_giorni"]):
        events.append({
            "data": d_str,
            "label": f"Visita — {a['specialista']}",
            "icon": "🏥",
            "passato": False,
            "freq": a["frequenza_giorni"],
            "item_id": a["id"],
            "tipo": "appointment_task",
        })

# Esami
for e in q.get_exams():
    if e["data_ultima"]:
        events.append({
            "data": e["data_ultima"],
            "label": f"Esame effettuato — {e['tipo']}",
            "icon": "✅",
            "passato": True,
        })
    for d_str in _expand_future(e["data_prossima"], e["frequenza_giorni"]):
        events.append({
            "data": d_str,
            "label": f"Esame — {e['tipo']}",
            "icon": "🔬",
            "passato": False,
            "freq": e["frequenza_giorni"],
            "item_id": e["id"],
            "tipo": "exam_task",
        })

# Ricette
for p in q.get_prescriptions():
    if p["data_ultima"]:
        events.append({
            "data": p["data_ultima"],
            "label": f"Rinnovo effettuato — {p['farmaco']}",
            "icon": "✅",
            "passato": True,
        })
    for d_str in _expand_future(p["data_prossima"], p["frequenza_giorni"]):
        events.append({
            "data": d_str,
            "label": f"Rinnovo ricetta — {p['farmaco']}",
            "icon": "💊",
            "passato": False,
            "freq": p["frequenza_giorni"],
            "item_id": p["id"],
            "tipo": "prescription_task",
        })

# Documenti caricati
for doc in q.get_documents():
    if doc["data_upload"]:
        data_doc = doc["data_upload"][:10]
        events.append({
            "data": data_doc,
            "label": f"Documento caricato — {doc['nome_file']}",
            "icon": "📄",
            "passato": data_doc < today_str,
        })

# ── Ordina ────────────────────────────────────────────────────────────────────
events.sort(key=lambda x: x["data"])

if not events:
    st.info("Nessun evento da mostrare. Aggiungi documenti, visite o misurazioni.")
    st.stop()

# Mappa (tipo, item_id) → data della prima occorrenza futura (la più vicina)
MARKABLE_TYPES = {"appointment_task", "exam_task", "prescription_task"}
nearest_future: dict[tuple, str] = {}
for ev in events:  # in ordine cronologico
    if not ev.get("passato") and ev.get("tipo") in MARKABLE_TYPES:
        key = (ev["tipo"], ev["item_id"])
        if key not in nearest_future:
            nearest_future[key] = ev["data"]

# ── Filtro ────────────────────────────────────────────────────────────────────
vista = st.radio("Mostra", ["Tutti", "Passati", "Futuri"], horizontal=True)

filtered = events
if vista == "Passati":
    filtered = [e for e in events if e["passato"]]
elif vista == "Futuri":
    filtered = [e for e in events if not e["passato"]]

# Passati e "Tutti" mostrano il più recente prima; Futuri in ordine cronologico
if vista != "Futuri":
    filtered = list(reversed(filtered))

if not filtered:
    st.info("Nessun evento in questa vista.")
    st.stop()

# ── Render ────────────────────────────────────────────────────────────────────
FREQ_LABELS = {1: "giornaliero", 7: "settimanale", 30: "mensile",
               90: "trimestrale", 180: "semestrale", 365: "annuale"}

current_month = None
for ev in filtered:
    month = ev["data"][:7]
    if month != current_month:
        current_month = month
        try:
            dt = datetime.strptime(ev["data"], "%Y-%m-%d")
            st.markdown(f"### {dt.strftime('%B %Y').capitalize()}")
        except ValueError:
            st.markdown(f"### {month}")

    is_future = not ev["passato"]
    can_mark = (
        is_future
        and ev.get("tipo") in MARKABLE_TYPES
        and nearest_future.get((ev["tipo"], ev["item_id"])) == ev["data"]
    )

    prefix = "🔜 " if is_future else ""
    freq_txt = FREQ_LABELS.get(ev.get("freq"), f"ogni {ev.get('freq')} giorni") if ev.get("freq") else None

    if can_mark:
        col_label, col_btn = st.columns([6, 1])
        with col_label:
            st.write(f"{ev['icon']} **{ev['data']}** — {prefix}{ev['label']}")
            if freq_txt:
                st.caption(f"Periodicità: {freq_txt}")
        with col_btn:
            if st.button("Fatto", key=f"fatto_{ev['tipo']}_{ev['item_id']}"):
                if ev["tipo"] == "appointment_task":
                    mark_done_appointment(ev["item_id"])
                elif ev["tipo"] == "exam_task":
                    mark_done_exam(ev["item_id"])
                elif ev["tipo"] == "prescription_task":
                    mark_done_prescription(ev["item_id"])
                st.rerun()
    else:
        st.write(f"{ev['icon']} **{ev['data']}** — {prefix}{ev['label']}")
        if is_future and freq_txt:
            st.caption(f"Periodicità: {freq_txt}")
