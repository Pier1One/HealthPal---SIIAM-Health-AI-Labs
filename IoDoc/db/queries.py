import sqlite3
from datetime import datetime
from db.schema import DB_PATH


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


# ── USER ──────────────────────────────────────────────────────────────────────

def get_user():
    with _conn() as c:
        return c.execute("SELECT * FROM user LIMIT 1").fetchone()


def upsert_user(nome, data_nascita, sesso, altezza_cm, peso_kg):
    with _conn() as c:
        existing = c.execute("SELECT id FROM user LIMIT 1").fetchone()
        if existing:
            c.execute(
                "UPDATE user SET nome=?, data_nascita=?, sesso=?, altezza_cm=?, peso_kg=? WHERE id=?",
                (nome, data_nascita, sesso, altezza_cm, peso_kg, existing["id"]),
            )
        else:
            c.execute(
                "INSERT INTO user (nome, data_nascita, sesso, altezza_cm, peso_kg) VALUES (?,?,?,?,?)",
                (nome, data_nascita, sesso, altezza_cm, peso_kg),
            )
        c.commit()


# ── CONDITIONS ────────────────────────────────────────────────────────────────

def get_conditions():
    with _conn() as c:
        return c.execute(
            "SELECT * FROM condition ORDER BY attiva DESC, nome"
        ).fetchall()


def add_condition(nome, data_diagnosi=None, attiva=True, note=""):
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO condition (nome, data_diagnosi, attiva, note) VALUES (?,?,?,?)",
            (nome, data_diagnosi, int(attiva), note),
        )
        c.commit()
        return cur.lastrowid


def update_condition(id, nome, data_diagnosi, attiva, note):
    with _conn() as c:
        c.execute(
            "UPDATE condition SET nome=?, data_diagnosi=?, attiva=?, note=? WHERE id=?",
            (nome, data_diagnosi, int(attiva), note, id),
        )
        c.commit()


def delete_condition(id):
    with _conn() as c:
        c.execute("DELETE FROM condition WHERE id=?", (id,))
        c.commit()


# ── MEDICATIONS ───────────────────────────────────────────────────────────────

def get_medications():
    with _conn() as c:
        return c.execute(
            "SELECT * FROM medication ORDER BY attivo DESC, nome"
        ).fetchall()


def add_medication(nome, dosaggio="", data_inizio=None, data_fine=None, attivo=True, note=""):
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO medication (nome, dosaggio, data_inizio, data_fine, attivo, note) VALUES (?,?,?,?,?,?)",
            (nome, dosaggio, data_inizio, data_fine, int(attivo), note),
        )
        c.commit()
        return cur.lastrowid


def update_medication(id, nome, dosaggio, data_inizio, data_fine, attivo, note):
    with _conn() as c:
        c.execute(
            "UPDATE medication SET nome=?, dosaggio=?, data_inizio=?, data_fine=?, attivo=?, note=? WHERE id=?",
            (nome, dosaggio, data_inizio, data_fine, int(attivo), note, id),
        )
        c.commit()


def delete_medication(id):
    with _conn() as c:
        c.execute("DELETE FROM medication_schedule WHERE medication_id=?", (id,))
        c.execute("DELETE FROM medication WHERE id=?", (id,))
        c.commit()


# ── MEDICATION SCHEDULES ──────────────────────────────────────────────────────

def get_schedules_for_medication(medication_id):
    with _conn() as c:
        return c.execute(
            "SELECT * FROM medication_schedule WHERE medication_id=? ORDER BY orario",
            (medication_id,),
        ).fetchall()


def get_schedule(id):
    with _conn() as c:
        return c.execute(
            """SELECT ms.*, m.nome AS farmaco_nome, m.dosaggio
               FROM medication_schedule ms
               JOIN medication m ON ms.medication_id = m.id
               WHERE ms.id=?""",
            (id,),
        ).fetchone()


def get_all_active_schedules():
    with _conn() as c:
        return c.execute(
            """SELECT ms.*, m.nome AS farmaco_nome, m.dosaggio
               FROM medication_schedule ms
               JOIN medication m ON ms.medication_id = m.id
               WHERE m.attivo = 1
               ORDER BY ms.orario"""
        ).fetchall()


def add_schedule(medication_id, orario):
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO medication_schedule (medication_id, orario) VALUES (?,?)",
            (medication_id, orario),
        )
        c.commit()
        return cur.lastrowid


def delete_schedule(id):
    with _conn() as c:
        c.execute("DELETE FROM medication_schedule WHERE id=?", (id,))
        c.commit()


# ── MONITORING TASKS ──────────────────────────────────────────────────────────

def get_monitoring_tasks():
    with _conn() as c:
        return c.execute("SELECT * FROM monitoring_task ORDER BY tipo").fetchall()


def add_monitoring_task(tipo, frequenza_giorni=1, orario=None, note=""):
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO monitoring_task (tipo, frequenza_giorni, orario, note) VALUES (?,?,?,?)",
            (tipo, frequenza_giorni, orario, note),
        )
        c.commit()
        return cur.lastrowid


def update_monitoring_task(id, tipo, frequenza_giorni, orario, note):
    with _conn() as c:
        c.execute(
            "UPDATE monitoring_task SET tipo=?, frequenza_giorni=?, orario=?, note=? WHERE id=?",
            (tipo, frequenza_giorni, orario, note, id),
        )
        c.commit()


def delete_monitoring_task(id):
    with _conn() as c:
        c.execute("DELETE FROM monitoring_task WHERE id=?", (id,))
        c.commit()


# ── APPOINTMENTS ──────────────────────────────────────────────────────────────

def get_appointments():
    with _conn() as c:
        return c.execute(
            "SELECT * FROM appointment_task ORDER BY data_prossima"
        ).fetchall()


def get_appointment(id):
    with _conn() as c:
        return c.execute("SELECT * FROM appointment_task WHERE id=?", (id,)).fetchone()


def add_appointment(specialista, frequenza_giorni=None, data_ultima=None, data_prossima=None, note=""):
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO appointment_task (specialista, frequenza_giorni, data_ultima, data_prossima, note) VALUES (?,?,?,?,?)",
            (specialista, frequenza_giorni, data_ultima, data_prossima, note),
        )
        c.commit()
        return cur.lastrowid


def update_appointment(id, specialista, frequenza_giorni, data_ultima, data_prossima, note):
    with _conn() as c:
        c.execute(
            "UPDATE appointment_task SET specialista=?, frequenza_giorni=?, data_ultima=?, data_prossima=?, note=? WHERE id=?",
            (specialista, frequenza_giorni, data_ultima, data_prossima, note, id),
        )
        c.commit()


def delete_appointment(id):
    with _conn() as c:
        c.execute("DELETE FROM appointment_task WHERE id=?", (id,))
        c.commit()


# ── EXAMS ─────────────────────────────────────────────────────────────────────

def get_exams():
    with _conn() as c:
        return c.execute("SELECT * FROM exam_task ORDER BY data_prossima").fetchall()


def get_exam(id):
    with _conn() as c:
        return c.execute("SELECT * FROM exam_task WHERE id=?", (id,)).fetchone()


def add_exam(tipo, frequenza_giorni=None, data_ultima=None, data_prossima=None, note=""):
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO exam_task (tipo, frequenza_giorni, data_ultima, data_prossima, note) VALUES (?,?,?,?,?)",
            (tipo, frequenza_giorni, data_ultima, data_prossima, note),
        )
        c.commit()
        return cur.lastrowid


def update_exam(id, tipo, frequenza_giorni, data_ultima, data_prossima, note):
    with _conn() as c:
        c.execute(
            "UPDATE exam_task SET tipo=?, frequenza_giorni=?, data_ultima=?, data_prossima=?, note=? WHERE id=?",
            (tipo, frequenza_giorni, data_ultima, data_prossima, note, id),
        )
        c.commit()


def delete_exam(id):
    with _conn() as c:
        c.execute("DELETE FROM exam_task WHERE id=?", (id,))
        c.commit()


# ── PRESCRIPTIONS ─────────────────────────────────────────────────────────────

def get_prescriptions():
    with _conn() as c:
        return c.execute(
            "SELECT * FROM prescription_task ORDER BY data_prossima"
        ).fetchall()


def get_prescription(id):
    with _conn() as c:
        return c.execute("SELECT * FROM prescription_task WHERE id=?", (id,)).fetchone()


def add_prescription(farmaco, frequenza_giorni=None, data_ultima=None, data_prossima=None, note=""):
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO prescription_task (farmaco, frequenza_giorni, data_ultima, data_prossima, note) VALUES (?,?,?,?,?)",
            (farmaco, frequenza_giorni, data_ultima, data_prossima, note),
        )
        c.commit()
        return cur.lastrowid


def update_prescription(id, farmaco, frequenza_giorni, data_ultima=None, data_prossima=None, note=""):
    with _conn() as c:
        c.execute(
            "UPDATE prescription_task SET farmaco=?, frequenza_giorni=?, data_ultima=?, data_prossima=?, note=? WHERE id=?",
            (farmaco, frequenza_giorni, data_ultima, data_prossima, note, id),
        )
        c.commit()


def delete_prescription(id):
    with _conn() as c:
        c.execute("DELETE FROM prescription_task WHERE id=?", (id,))
        c.commit()


# ── DOCUMENTS ─────────────────────────────────────────────────────────────────

def get_documents():
    with _conn() as c:
        return c.execute(
            "SELECT * FROM document ORDER BY data_upload DESC"
        ).fetchall()


def add_document(file_path, nome_file, tipo, testo_estratto=""):
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO document (file_path, nome_file, tipo, data_upload, testo_estratto) VALUES (?,?,?,?,?)",
            (file_path, nome_file, tipo, datetime.now().isoformat(), testo_estratto),
        )
        c.commit()
        return cur.lastrowid


def delete_document(id):
    with _conn() as c:
        doc = c.execute("SELECT file_path FROM document WHERE id=?", (id,)).fetchone()
        c.execute("DELETE FROM document WHERE id=?", (id,))
        c.commit()
        return doc["file_path"] if doc else None


# ── MEASUREMENTS ──────────────────────────────────────────────────────────────

def get_measurements(tipo=None):
    with _conn() as c:
        if tipo:
            return c.execute(
                "SELECT * FROM measurement WHERE tipo=? ORDER BY data DESC, ora DESC",
                (tipo,),
            ).fetchall()
        return c.execute(
            "SELECT * FROM measurement ORDER BY tipo, data DESC, ora DESC"
        ).fetchall()


def get_measurement_types():
    with _conn() as c:
        rows = c.execute(
            "SELECT DISTINCT tipo FROM measurement ORDER BY tipo"
        ).fetchall()
        return [r["tipo"] for r in rows]


def add_measurement(tipo, valore, unita="", data=None, ora="", note=""):
    data = data or datetime.now().strftime("%Y-%m-%d")
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO measurement (tipo, valore, unita, data, ora, note) VALUES (?,?,?,?,?,?)",
            (tipo, valore, unita, data, ora, note),
        )
        c.commit()
        return cur.lastrowid


def delete_measurement(id):
    with _conn() as c:
        c.execute("DELETE FROM measurement WHERE id=?", (id,))
        c.commit()


# ── NOTIFICATIONS ─────────────────────────────────────────────────────────────

def get_pending_notifications():
    with _conn() as c:
        now = datetime.now().isoformat()
        return c.execute(
            "SELECT * FROM notification WHERE status='pending' AND scheduled_at <= ? ORDER BY scheduled_at",
            (now,),
        ).fetchall()


def get_sent_notifications():
    with _conn() as c:
        return c.execute(
            "SELECT * FROM notification WHERE status='sent' ORDER BY scheduled_at DESC"
        ).fetchall()


def add_notification(tipo, riferimento_id, messaggio, scheduled_at):
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO notification (tipo, riferimento_id, messaggio, scheduled_at, status) VALUES (?,?,?,?,'pending')",
            (tipo, riferimento_id, messaggio, scheduled_at),
        )
        c.commit()
        return cur.lastrowid


def mark_notification_sent(id):
    with _conn() as c:
        c.execute(
            "UPDATE notification SET status='sent', sent_at=? WHERE id=?",
            (datetime.now().isoformat(), id),
        )
        c.commit()


def mark_notification_done(id):
    with _conn() as c:
        c.execute("UPDATE notification SET status='done' WHERE id=?", (id,))
        c.commit()


def mark_notification_skipped(id):
    with _conn() as c:
        c.execute("UPDATE notification SET status='skipped' WHERE id=?", (id,))
        c.commit()


def cancel_pending_notifications_for(tipo, riferimento_id):
    with _conn() as c:
        c.execute(
            "DELETE FROM notification WHERE tipo=? AND riferimento_id=? AND status='pending'",
            (tipo, riferimento_id),
        )
        c.commit()


def mark_sent_notifications_done_for(tipo, riferimento_id):
    with _conn() as c:
        c.execute(
            "UPDATE notification SET status='done' WHERE tipo=? AND riferimento_id=? AND status='sent'",
            (tipo, riferimento_id),
        )
        c.commit()
