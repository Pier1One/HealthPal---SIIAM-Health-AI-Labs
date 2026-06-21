import subprocess
import sys

try:
    from plyer import notification as _plyer
    _PLYER_OK = True
except Exception:
    _PLYER_OK = False

# Medication uses a looping alarm; everything else uses the standard reminder sound.
_SOUND_MAP = {
    "medication_schedule": "ms-winsoundevent:Notification.Looping.Alarm2",
}
_DEFAULT_SOUND = "ms-winsoundevent:Notification.Reminder"


def send_notification(title: str, message: str, tipo: str = "") -> None:
    if sys.platform == "win32":
        sound = _SOUND_MAP.get(tipo, _DEFAULT_SOUND)
        _win_toast(title, message, sound=sound)
        return

    sent = False
    if _PLYER_OK:
        try:
            _plyer.notify(title=title, message=message, app_name="IoDoc", timeout=10)
            sent = True
        except Exception as e:
            print(f"[IoDoc] plyer error: {e}")
    if not sent:
        print(f"[IoDoc] NOTIFICA: {title} — {message}")


def _win_toast(title: str, message: str, sound: str = _DEFAULT_SOUND) -> None:
    safe_title = title.replace("'", "\\'").replace('"', '&quot;')
    safe_msg = message.replace("'", "\\'").replace('"', '&quot;')
    xml = (
        "<toast>"
        "<visual><binding template='ToastGeneric'>"
        f"<text>{safe_title}</text><text>{safe_msg}</text>"
        "</binding></visual>"
        f"<audio src='{sound}'/>"
        "</toast>"
    )
    script = (
        "[void][Windows.UI.Notifications.ToastNotificationManager,"
        " Windows.UI.Notifications, ContentType=WindowsRuntime];"
        "[void][Windows.Data.Xml.Dom.XmlDocument,"
        " Windows.Data.Xml.Dom, ContentType=WindowsRuntime];"
        "$xml = [Windows.Data.Xml.Dom.XmlDocument]::new();"
        f"$xml.LoadXml('{xml}');"
        "$notif = [Windows.UI.Notifications.ToastNotification]::new($xml);"
        "[Windows.UI.Notifications.ToastNotificationManager]"
        "::CreateToastNotifier('IoDoc').Show($notif)"
    )
    try:
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-NonInteractive", "-Command", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"[IoDoc] win_toast error: {e}")
