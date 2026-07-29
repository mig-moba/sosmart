"""Deteccion de la palabra clave configurada por el usuario.

No se mantiene un microfono escuchando todo el tiempo (Android no lo permite
de forma confiable en segundo plano). En su lugar, se abre una ventana corta
de escucha (unos segundos) cuando el usuario la activa manualmente desde la
app, y se compara el texto reconocido contra la palabra clave guardada en la
configuracion.
"""

import threading


def listen_once(timeout=8):
    """Escucha por 'timeout' segundos y devuelve el texto reconocido (minusculas).

    En Android usa el reconocimiento de voz nativo via plyer.stt. Si no esta
    disponible (por ejemplo, pruebas en escritorio), intenta usar el paquete
    SpeechRecognition con el microfono de la PC.
    """
    try:
        from plyer import stt
        return _listen_with_plyer(stt, timeout)
    except Exception:
        pass

    try:
        return _listen_with_speech_recognition(timeout)
    except Exception as exc:
        print(f"[SOSmart] No se pudo usar el microfono: {exc}")
        return ""


def _listen_with_plyer(stt, timeout):
    result = {"text": ""}
    done = threading.Event()

    def on_result(text_list):
        if text_list:
            result["text"] = text_list[0].lower()
        done.set()

    stt.start(callback=on_result)
    done.wait(timeout)
    try:
        stt.stop()
    except Exception:
        pass
    return result["text"]


def _listen_with_speech_recognition(timeout):
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=timeout)
    return recognizer.recognize_google(audio, language="es-MX").lower()


def matches_keyword(text, keyword):
    if not text or not keyword:
        return False
    return keyword.strip().lower() in text.strip().lower()
