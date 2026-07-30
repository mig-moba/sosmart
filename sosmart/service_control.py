"""Control del servicio Android de seguimiento de ubicacion en primer plano.

El servicio corre en un proceso separado del de la Activity principal (asi
lo exige Android para que sobreviva aunque el usuario cambie de app o
bloquee la pantalla), por lo que la comunicacion entre la app y el
servicio es minima: arrancarlo, pararlo, y un archivo de bandera para
saber si sigue activo.
"""

import os

PACKAGE = "org.guardianesdigitales.sosmart"
SERVICE_CLASS = f"{PACKAGE}.ServiceTracking"


def _files_dir():
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    return PythonActivity.mActivity.getFilesDir().getAbsolutePath()


def _flag_path():
    return os.path.join(_files_dir(), "tracking_active.flag")


def is_tracking_active():
    try:
        return os.path.exists(_flag_path())
    except Exception:
        return False


def start_tracking_service():
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        service = autoclass(SERVICE_CLASS)
        service.start(PythonActivity.mActivity, '')
    except Exception as exc:
        print(f"[SOSmart] No se pudo iniciar el servicio de seguimiento: {exc}")


def stop_tracking_service():
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        service = autoclass(SERVICE_CLASS)
        service.stop(PythonActivity.mActivity)
    except Exception as exc:
        print(f"[SOSmart] No se pudo detener el servicio de seguimiento: {exc}")

    try:
        path = _flag_path()
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
