from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, time, date
import db.queries as q

_scheduler = None


# ── Background job ────────────────────────────────────────────────────────────

def _check_and_send():
    from notifications.notifier import send_notification
    for notif in q.get_pending_notifications():
        send_notification("IoDoc", notif["messaggio"], tipo=notif["tipo"])
        q.mark_notification_sent(notif["id"])


# ── Scheduler lifecycle ───────────────────────────────────────────────────────

def _reschedule_on_startup():
    """Recalculate triggers for all active medication and monitoring schedules."""
    try:
        for s in q.get_all_active_schedules():
            schedule_medication(s["id"], s["farmaco_nome"], s["orario"])
        for t in q.get_monitoring_tasks():
            if t["orario"]:
                schedule_monitoring(t["id"], t["tipo"], t["orario"])
    except Exception as e:
        print(f"[IoDoc] _reschedule_on_startup error: {e}")


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(_check_and_send, "interval", minutes=1, id="notify_check")
    _scheduler.start()
    _reschedule_on_startup()


# ── Internal: trigger resolution ──────────────────────────────────────────────

def _resolve_trigger(deadline_date: date, days_before: int) -> datetime | None:
    """Return the notification datetime, or None if the deadline has passed."""
    if deadline_date < date.today():
        return None
    trigger = datetime.combine(deadline_date - timedelta(days=days_before), time(9, 0))
    now = datetime.now()
    if trigger <= now:
        # Deadline still in the future but advance notice already passed → notify in 1 min
        trigger = now + timedelta(minutes=1)
    return trigger


# ── Schedule helpers ──────────────────────────────────────────────────────────

def schedule_medication(schedule_id: int, farmaco_nome: str, orario_str: str):
    try:
        now = datetime.now()
        h, m = map(int, orario_str.split(":"))
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        trigger = target - timedelta(minutes=30)
        if trigger <= now:
            if target > now:
                # Lead time passed but medication time hasn't → fire immediately
                trigger = now + timedelta(minutes=1)
            else:
                # Both passed → next occurrence tomorrow
                trigger = target + timedelta(days=1) - timedelta(minutes=30)
        q.cancel_pending_notifications_for("medication_schedule", schedule_id)
        q.add_notification(
            tipo="medication_schedule",
            riferimento_id=schedule_id,
            messaggio=f"Ricorda: assumere {farmaco_nome} alle {orario_str}",
            scheduled_at=trigger.isoformat(),
        )
    except Exception as e:
        print(f"[IoDoc] schedule_medication error: {e}")


def schedule_monitoring(task_id: int, tipo: str, orario_str: str):
    try:
        now = datetime.now()
        h, m = map(int, orario_str.split(":"))
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        trigger = target - timedelta(minutes=30)
        if trigger <= now:
            if target > now:
                trigger = now + timedelta(minutes=1)
            else:
                trigger = target + timedelta(days=1) - timedelta(minutes=30)
        q.cancel_pending_notifications_for("monitoring_task", task_id)
        q.add_notification(
            tipo="monitoring_task",
            riferimento_id=task_id,
            messaggio=f"Ricorda: misurare {tipo} alle {orario_str}",
            scheduled_at=trigger.isoformat(),
        )
    except Exception as e:
        print(f"[IoDoc] schedule_monitoring error: {e}")


def schedule_appointment(appointment_id: int, specialista: str, data_prossima_str: str):
    try:
        deadline = datetime.strptime(data_prossima_str, "%Y-%m-%d").date()
        trigger = _resolve_trigger(deadline, days_before=15)
        if trigger is None:
            return
        q.cancel_pending_notifications_for("appointment_task", appointment_id)
        q.add_notification(
            tipo="appointment_task",
            riferimento_id=appointment_id,
            messaggio=f"Visita {specialista} il {data_prossima_str} (tra {(deadline - date.today()).days} giorni)",
            scheduled_at=trigger.isoformat(),
        )
    except Exception as e:
        print(f"[IoDoc] schedule_appointment error: {e}")


def schedule_exam(exam_id: int, tipo: str, data_prossima_str: str):
    try:
        deadline = datetime.strptime(data_prossima_str, "%Y-%m-%d").date()
        trigger = _resolve_trigger(deadline, days_before=7)
        if trigger is None:
            return
        q.cancel_pending_notifications_for("exam_task", exam_id)
        q.add_notification(
            tipo="exam_task",
            riferimento_id=exam_id,
            messaggio=f"Esame {tipo} il {data_prossima_str} (tra {(deadline - date.today()).days} giorni)",
            scheduled_at=trigger.isoformat(),
        )
    except Exception as e:
        print(f"[IoDoc] schedule_exam error: {e}")


def schedule_prescription(prescription_id: int, farmaco: str, data_prossima_str: str):
    try:
        deadline = datetime.strptime(data_prossima_str, "%Y-%m-%d").date()
        trigger = _resolve_trigger(deadline, days_before=7)
        if trigger is None:
            return
        q.cancel_pending_notifications_for("prescription_task", prescription_id)
        q.add_notification(
            tipo="prescription_task",
            riferimento_id=prescription_id,
            messaggio=f"Rinnovo ricetta {farmaco} il {data_prossima_str} (tra {(deadline - date.today()).days} giorni)",
            scheduled_at=trigger.isoformat(),
        )
    except Exception as e:
        print(f"[IoDoc] schedule_prescription error: {e}")


# ── Mark done + reschedule (from Dashboard or Timeline) ───────────────────────

def mark_done_appointment(appointment_id: int, today_str: str | None = None):
    appt = q.get_appointment(appointment_id)
    if not appt:
        return
    today_str = today_str or date.today().isoformat()
    next_date = None
    if appt["frequenza_giorni"]:
        next_date = (date.today() + timedelta(days=appt["frequenza_giorni"])).strftime("%Y-%m-%d")
    q.update_appointment(appointment_id, appt["specialista"], appt["frequenza_giorni"],
                         today_str, next_date, appt["note"] or "")
    q.cancel_pending_notifications_for("appointment_task", appointment_id)
    if next_date:
        schedule_appointment(appointment_id, appt["specialista"], next_date)


def mark_done_exam(exam_id: int, today_str: str | None = None):
    exam = q.get_exam(exam_id)
    if not exam:
        return
    today_str = today_str or date.today().isoformat()
    next_date = None
    if exam["frequenza_giorni"]:
        next_date = (date.today() + timedelta(days=exam["frequenza_giorni"])).strftime("%Y-%m-%d")
    q.update_exam(exam_id, exam["tipo"], exam["frequenza_giorni"],
                  today_str, next_date, exam["note"] or "")
    q.cancel_pending_notifications_for("exam_task", exam_id)
    if next_date:
        schedule_exam(exam_id, exam["tipo"], next_date)


def mark_done_prescription(prescription_id: int, today_str: str | None = None):
    pres = q.get_prescription(prescription_id)
    if not pres:
        return
    today_str = today_str or date.today().isoformat()
    next_date = None
    if pres["frequenza_giorni"]:
        next_date = (date.today() + timedelta(days=pres["frequenza_giorni"])).strftime("%Y-%m-%d")
    q.update_prescription(prescription_id, pres["farmaco"], pres["frequenza_giorni"],
                          today_str, next_date, pres["note"] or "")
    q.cancel_pending_notifications_for("prescription_task", prescription_id)
    if next_date:
        schedule_prescription(prescription_id, pres["farmaco"], next_date)


# ── Reschedule after "Fatto" from Dashboard (keeps data_prossima as base) ─────

def reschedule_appointment(appointment_id: int):
    mark_done_appointment(appointment_id)


def reschedule_exam(exam_id: int):
    mark_done_exam(exam_id)


def reschedule_prescription(prescription_id: int):
    mark_done_prescription(prescription_id)
