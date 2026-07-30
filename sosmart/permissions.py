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
        Permission.CALL_PHONE,
    ])


def show_over_lock_screen():
    """Permite que la app se muestre sobre la pantalla de bloqueo y
    encienda la pantalla al abrirse.

    Util cuando la app se abre mediante un acceso directo del propio
    telefono (por ejemplo, doble pulsacion de la tecla lateral en
    Samsung configurada desde Ajustes) estando el telefono bloqueado: sin
    esto, Android pediria desbloquear primero antes de mostrar la app.
    """
    try:
        from jnius import autoclass
        from android.runnable import run_on_ui_thread
    except Exception:
        return  # No es Android.

    @run_on_ui_thread
    def _apply():
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            LayoutParams = autoclass('android.view.WindowManager$LayoutParams')
            VERSION = autoclass('android.os.Build$VERSION')
            activity = PythonActivity.mActivity

            window = activity.getWindow()
            window.addFlags(
                LayoutParams.FLAG_SHOW_WHEN_LOCKED
                | LayoutParams.FLAG_TURN_SCREEN_ON
                | LayoutParams.FLAG_DISMISS_KEYGUARD
                | LayoutParams.FLAG_KEEP_SCREEN_ON
            )

            # API 27+: forma recomendada actual, mas confiable que las
            # banderas de WindowManager en versiones recientes de Android.
            if VERSION.SDK_INT >= 27:
                activity.setShowWhenLocked(True)
                activity.setTurnScreenOn(True)

            print("[SOSmart] Configurado para mostrarse sobre la pantalla bloqueada")
        except Exception as exc:
            print(f"[SOSmart] No se pudo configurar mostrar sobre pantalla bloqueada: {exc}")

    # addFlags()/setShowWhenLocked() deben ejecutarse en el hilo de UI de
    # Android; llamarlos desde el hilo donde corre build() puede fallar en
    # silencio o no surtir efecto.
    _apply()
