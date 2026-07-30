"""Llamada de emergencia directa, sin pasar por el marcador.

Usa Intent.ACTION_CALL (en vez de ACTION_DIAL) para que la llamada inicie
de inmediato al presionar "Llamada rapida", igual que el resto de la app
evita pasos manuales adicionales en una emergencia. Requiere el permiso
CALL_PHONE concedido en tiempo de ejecucion.
"""


def call_number(phone_number):
    if not phone_number:
        print("[SOSmart] No hay numero de llamada rapida configurado")
        return False

    try:
        from jnius import autoclass

        Intent = autoclass('android.content.Intent')
        Uri = autoclass('android.net.Uri')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity

        intent = Intent(Intent.ACTION_CALL)
        intent.setData(Uri.parse(f"tel:{phone_number}"))
        activity.startActivity(intent)
        return True
    except Exception as exc:
        print(f"[SOSmart] No se pudo iniciar la llamada: {exc}")
        return False
