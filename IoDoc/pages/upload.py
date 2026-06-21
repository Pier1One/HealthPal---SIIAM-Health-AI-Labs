import streamlit as st
import os
import time as _time
from datetime import datetime
import pdfplumber
import db.queries as q
from ai.extractor import extract_from_text, extract_from_image
from notifications.scheduler import schedule_medication, schedule_appointment, schedule_exam, schedule_prescription

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "documents")
os.makedirs(DOCS_DIR, exist_ok=True)

IMAGE_MIME = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}


def _save_file(uploaded):
    ts = int(_time.time())
    dest = os.path.join(DOCS_DIR, f"{ts}_{uploaded.name}")
    with open(dest, "wb") as f:
        f.write(uploaded.getbuffer())
    return dest, uploaded.name


def _extract_text_pdf(path):
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def _save_extracted(data):
    today = datetime.now().strftime("%Y-%m-%d")

    for c in data.get("conditions", []):
        q.add_condition(c["nome"], c.get("data_diagnosi"), note=c.get("note") or "")

    for m in data.get("medications", []):
        med_id = q.add_medication(
            m["nome"], m.get("dosaggio") or "", m.get("data_inizio") or today
        )
        for orario in m.get("orari") or []:
            sch_id = q.add_schedule(med_id, orario)
            schedule_medication(sch_id, m["nome"], orario)

    for a in data.get("appointments", []):
        appt_id = q.add_appointment(a["specialista"], data_prossima=a.get("data_prossima"))
        if a.get("data_prossima"):
            schedule_appointment(appt_id, a["specialista"], a["data_prossima"])

    for e in data.get("exams", []):
        exam_id = q.add_exam(e["tipo"], data_prossima=e.get("data_prossima"))
        if e.get("data_prossima"):
            schedule_exam(exam_id, e["tipo"], e["data_prossima"])

    for p in data.get("prescriptions", []):
        pres_id = q.add_prescription(p["farmaco"], data_prossima=p.get("data_prossima"))
        if p.get("data_prossima"):
            schedule_prescription(pres_id, p["farmaco"], p["data_prossima"])


# ── UI ────────────────────────────────────────────────────────────────────────

st.title("Carica Documento")

if st.session_state.get("_upload_saved"):
    st.session_state["_upload_saved"] = False
    st.success("Dati salvati nel piano sanitario.")
    st.balloons()

uploaded = st.file_uploader(
    "Trascina qui un PDF o un'immagine",
    type=["pdf", "jpg", "jpeg", "png", "webp"],
)

if uploaded and "extracted_data" not in st.session_state:
    if st.button("Analizza documento", type="primary"):
        with st.spinner("Estrazione in corso…"):
            try:
                file_path, nome_file = _save_file(uploaded)
                ext = nome_file.rsplit(".", 1)[-1].lower()
                tipo = "pdf" if ext == "pdf" else "immagine"

                if tipo == "pdf":
                    testo = _extract_text_pdf(file_path)
                    data = extract_from_text(testo)
                else:
                    mime = IMAGE_MIME.get(ext, "image/jpeg")
                    with open(file_path, "rb") as fh:
                        img_bytes = fh.read()
                    testo = ""
                    data = extract_from_image(img_bytes, mime)

                doc_id = q.add_document(file_path, nome_file, tipo, testo)
                st.session_state["extracted_data"] = data
                st.session_state["extracted_doc_id"] = doc_id
                st.rerun()
            except Exception as exc:
                st.error(f"Errore durante l'analisi: {exc}")

# ── Revisione dati estratti ───────────────────────────────────────────────────
if "extracted_data" in st.session_state:
    data = st.session_state["extracted_data"]
    total = sum(len(v) for v in data.values())

    if total == 0:
        st.warning("Nessuna informazione clinica trovata nel documento.")
        if st.button("Carica un altro documento"):
            del st.session_state["extracted_data"]
            st.rerun()
    else:
        st.success(f"Trovati {total} elementi. Rivedi e conferma prima di salvare.")

        # Patologie
        conditions = data.get("conditions", [])
        if conditions:
            st.subheader("Patologie")
            to_remove = []
            for i, c in enumerate(conditions):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"**{c['nome']}** — diagnosi: {c.get('data_diagnosi') or 'non specificata'}")
                    if c.get("note"):
                        st.caption(c["note"])
                with col2:
                    if st.button("Rimuovi", key=f"rm_cond_{i}"):
                        to_remove.append(i)
            for i in reversed(to_remove):
                data["conditions"].pop(i)
            if to_remove:
                st.rerun()

        # Farmaci
        medications = data.get("medications", [])
        if medications:
            st.subheader("Farmaci")
            to_remove = []
            for i, m in enumerate(medications):
                col1, col2 = st.columns([5, 1])
                with col1:
                    orari = ", ".join(m.get("orari") or []) or "non specificati"
                    st.write(f"**{m['nome']}** {m.get('dosaggio') or ''} — orari: {orari}")
                with col2:
                    if st.button("Rimuovi", key=f"rm_med_{i}"):
                        to_remove.append(i)
            for i in reversed(to_remove):
                data["medications"].pop(i)
            if to_remove:
                st.rerun()

        # Visite
        appointments = data.get("appointments", [])
        if appointments:
            st.subheader("Visite")
            to_remove = []
            for i, a in enumerate(appointments):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"**{a['specialista']}** — data: {a.get('data_prossima') or 'non specificata'}")
                with col2:
                    if st.button("Rimuovi", key=f"rm_app_{i}"):
                        to_remove.append(i)
            for i in reversed(to_remove):
                data["appointments"].pop(i)
            if to_remove:
                st.rerun()

        # Esami
        exams = data.get("exams", [])
        if exams:
            st.subheader("Esami")
            to_remove = []
            for i, e in enumerate(exams):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"**{e['tipo']}** — data: {e.get('data_prossima') or 'non specificata'}")
                with col2:
                    if st.button("Rimuovi", key=f"rm_ex_{i}"):
                        to_remove.append(i)
            for i in reversed(to_remove):
                data["exams"].pop(i)
            if to_remove:
                st.rerun()

        # Ricette
        prescriptions = data.get("prescriptions", [])
        if prescriptions:
            st.subheader("Ricette")
            to_remove = []
            for i, p in enumerate(prescriptions):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"**{p['farmaco']}** — rinnovo: {p.get('data_prossima') or 'non specificata'}")
                with col2:
                    if st.button("Rimuovi", key=f"rm_pres_{i}"):
                        to_remove.append(i)
            for i in reversed(to_remove):
                data["prescriptions"].pop(i)
            if to_remove:
                st.rerun()

        st.divider()
        col_save, col_cancel = st.columns([2, 1])
        with col_save:
            if st.button("Conferma e salva tutto", type="primary"):
                _save_extracted(data)
                del st.session_state["extracted_data"]
                del st.session_state["extracted_doc_id"]
                st.session_state["_upload_saved"] = True
                st.rerun()
        with col_cancel:
            if st.button("Annulla"):
                del st.session_state["extracted_data"]
                st.rerun()

# ── Documenti caricati ────────────────────────────────────────────────────────
st.divider()
st.subheader("Documenti caricati")
docs = q.get_documents()
if docs:
    for doc in docs:
        col1, col2 = st.columns([5, 1])
        with col1:
            ts = doc["data_upload"][:16].replace("T", " ") if doc["data_upload"] else ""
            st.write(f"**{doc['nome_file']}** ({doc['tipo']}) — {ts}")
        with col2:
            if st.button("Elimina", key=f"del_doc_{doc['id']}"):
                path = q.delete_document(doc["id"])
                if path and os.path.exists(path):
                    os.remove(path)
                st.rerun()
else:
    st.info("Nessun documento caricato.")
