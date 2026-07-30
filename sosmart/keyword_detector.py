"""Deteccion de la palabra clave configurada por el usuario.

No se mantiene un microfono escuchando todo el tiempo (Android no lo permite
de forma confiable en segundo plano). En su lugar, se abre una ventana corta
de escucha (unos segundos) cuando el usuario la activa manualmente desde la
app, y se compara el texto reconocido contra la palabra clave guardada en la
configuracion.
"""

import time


def listen_once(timeout=8, language="es-MX"):
    """Escucha por 'timeout' segundos y devuelve el texto reconocido (minusculas).

    En Android usa el reconocimiento de voz nativo via plyer.stt. Si no esta
    disponible (por ejemplo, pruebas en escritorio), intenta usar el paquete
    SpeechRecognition con el microfono de la PC.
    """
    try:
        from plyer import stt
        return _listen_with_plyer(stt, timeout, language)
    except Exception as exc:
        print(f"[SOSmart] plyer.stt no disponible: {exc}")

    try:
        return _listen_with_speech_recognition(timeout, language)
    except Exception as exc:
        print(f"[SOSmart] No se pudo usar el microfono: {exc}")
        return ""


def _listen_with_plyer(stt, timeout, language):
    # La lista de idiomas "soportados" del facade de plyer esta incompleta
    # (solo trae en-US y pl-PL), asi que su setter rechazaria 'es-MX'. Se
    # asigna directamente al atributo privado para saltarse esa validacion;
    # Android acepta cualquier codigo de idioma valido.
    stt._language = language
    stt.prefer_offline = False  # mas confiable sin haber descargado paquetes offline

    stt.results = []
    stt.errors = []
    stt.start()

    deadline = time.time() + timeout
    while time.time() < deadline:
        if stt.results or stt.errors:
            break
        time.sleep(0.2)

    if stt.listening:
        try:
            stt.stop()
        except Exception:
            pass

    if stt.errors:
        print(f"[SOSmart] Error de reconocimiento de voz: {stt.errors}")

    if stt.results:
        return stt.results[0].lower()
    return ""


def _listen_with_speech_recognition(timeout, language):
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=timeout)
    return recognizer.recognize_google(audio, language=language).lower()


def matches_keyword(text, keyword):
    if not text or not keyword:
        return False
    return keyword.strip().lower() in text.strip().lower()
