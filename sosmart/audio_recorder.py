"""Grabacion de audio como evidencia, iniciada al activarse una alerta."""

try:
    from plyer import audio
except Exception:
    audio = None

_state = {"active": False}


def start_recording(filename="sosmart_evidencia.3gp"):
    if audio is None:
        print("[SOSmart] Grabacion de audio no disponible en esta plataforma.")
        return False
    try:
        audio.file_path = filename
        audio.start()
        _state["active"] = True
        return True
    except Exception as exc:
        print(f"[SOSmart] No se pudo iniciar la grabacion: {exc}")
        return False


def stop_recording():
    if audio is None or not _state["active"]:
        return None
    try:
        audio.stop()
        _state["active"] = False
        return audio.file_path
    except Exception as exc:
        print(f"[SOSmart] No se pudo detener la grabacion: {exc}")
        return None
