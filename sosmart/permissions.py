"""Solicita permisos en tiempo de ejecucion en Android (API 23+).

Aunque los permisos esten declarados en buildozer.spec (AndroidManifest.xml),
el sistema los deja en estado "no otorgado" hasta que la app los pide
explicitamente y el usuario los acepta en el dialogo del sistema. Sin este
paso, las llamadas a GPS, SMS y microfono fallan en silencio (se capturan
como excepcion y no hacen nada visible).
"""


def request_android_permissions():
    try:
        from android.permissions import Permission, request_permissions
    except Exception:
        return  # No es Android (por ejemplo, pruebas en escritorio).

    request_permissions([
        Permission.RECORD_AUDIO,
        Permission.ACCESS_FINE_LOCATION,
        Permission.ACCESS_COARSE_LOCATION,
        Permission.SEND_SMS,
    ])
