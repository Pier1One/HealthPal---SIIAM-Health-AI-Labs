from datetime import date, timedelta
import db.queries as q


def mark_done_medication_schedule(schedule_id: int):
    sched = q.get_schedule(schedule_id)
    if not sched:
        return
    from notifications.scheduler import schedule_medication
    schedule_medication(schedule_id, sched["farmaco_nome"], sched["orario"])


def mark_done_appointment(appointment_id):
    appt = q.get_appointment(appointment_id)
    if not appt:
        return
    today_str = date.today().isoformat()
    next_date = None
    if appt["frequenza_giorni"]:
        next_date = (date.today() + timedelta(days=appt["frequenza_giorni"])).strftime("%Y-%m-%d")
    q.update_appointment(appointment_id, appt["specialista"], appt["frequenza_giorni"],
                         today_str, next_date, appt["note"] or "")
    q.cancel_pending_notifications_for("appointment_task", appointment_id)
    q.mark_sent_notifications_done_for("appointment_task", appointment_id)
    if next_date:
        from notifications.scheduler import schedule_appointment
        schedule_appointment(appointment_id, appt["specialista"], next_date)


def mark_done_exam(exam_id):
    exam = q.get_exam(exam_id)
    if not exam:
        return
    today_str = date.today().isoformat()
    next_date = None
    if exam["frequenza_giorni"]:
        next_date = (date.today() + timedelta(days=exam["frequenza_giorni"])).strftime("%Y-%m-%d")
    q.update_exam(exam_id, exam["tipo"], exam["frequenza_giorni"],
                  today_str, next_date, exam["note"] or "")
    q.cancel_pending_notifications_for("exam_task", exam_id)
    q.mark_sent_notifications_done_for("exam_task", exam_id)
    if next_date:
        from notifications.scheduler import schedule_exam
        schedule_exam(exam_id, exam["tipo"], next_date)


def mark_done_prescription(prescription_id):
    pres = q.get_prescription(prescription_id)
    if not pres:
        return
    today_str = date.today().isoformat()
    next_date = None
    if pres["frequenza_giorni"]:
        next_date = (date.today() + timedelta(days=pres["frequenza_giorni"])).strftime("%Y-%m-%d")
    q.update_prescription(prescription_id, pres["farmaco"], pres["frequenza_giorni"],
                          today_str, next_date, pres["note"] or "")
    q.cancel_pending_notifications_for("prescription_task", prescription_id)
    q.mark_sent_notifications_done_for("prescription_task", prescription_id)
    if next_date:
        from notifications.scheduler import schedule_prescription
        schedule_prescription(prescription_id, pres["farmaco"], next_date)
