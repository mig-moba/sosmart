"""Ubicacion GPS via pyjnius directo.

plyer.gps tiene un bug conocido en Android 13+: el sistema invoca la
sobrecarga por lote LocationListener.onLocationChanged(List<Location>) en
vez de (o ademas de) la version individual onLocationChanged(Location), y
plyer solo implementa esta ultima, asi que la app nunca recibe ninguna
lectura (se ve en el log como "NotImplementedError: ... onLocationChanged
... List ... is not implemented", repetido sin parar). Aqui se implementa
un listener propio que cubre ambas sobrecargas.
"""

import threading


def _make_listener(on_update):
    """Crea un LocationListener de Android que llama a on_update(lat, lon)
    cada vez que hay una lectura nueva. Cubre ambas sobrecargas de
    onLocationChanged (individual y por lote, esta ultima usada en
    Android 13+)."""
    from jnius import java_method, PythonJavaClass

    class _Listener(PythonJavaClass):
        __javainterfaces__ = ['android/location/LocationListener']

        @java_method('(Landroid/location/Location;)V')
        def onLocationChanged(self, location):
            on_update(location.getLatitude(), location.getLongitude())

        @java_method('(Ljava/util/List;)V', name='onLocationChanged')
        def onLocationChangedBatch(self, locations):
            size = locations.size()
            if size > 0:
                location = locations.get(size - 1)
                on_update(location.getLatitude(), location.getLongitude())

        @java_method('(Ljava/lang/String;)V')
        def onProviderEnabled(self, provider):
            print(f"[SOSmart] GPS proveedor activado: {provider}")

        @java_method('(Ljava/lang/String;)V')
        def onProviderDisabled(self, provider):
            print(f"[SOSmart] GPS proveedor desactivado: {provider}")

        @java_method('(Ljava/lang/String;ILandroid/os/Bundle;)V')
        def onStatusChanged(self, provider, status, extras):
            pass

    return _Listener()


def _request_updates(listener, min_time_ms, min_distance_m):
    """Registra el listener en todos los proveedores de ubicacion
    disponibles. Devuelve el LocationManager usado (para poder detener las
    actualizaciones despues), o None si no fue posible."""
    from jnius import autoclass
    from plyer.platforms.android import activity

    Looper = autoclass('android.os.Looper')
    Context = autoclass('android.content.Context')

    location_manager = activity.getSystemService(Context.LOCATION_SERVICE)
    providers = location_manager.getProviders(False).toArray()

    if not providers:
        print("[SOSmart] GPS: no hay ningun proveedor de ubicacion disponible")
        return None

    for provider in providers:
        location_manager.requestLocationUpdates(
            provider, min_time_ms, min_distance_m, listener, Looper.getMainLooper()
        )
    return location_manager


def get_location_once(timeout=20):
    """Pide una sola lectura de GPS y espera hasta 'timeout' segundos."""
    result = {"fix": None}
    done = threading.Event()

    def _report(lat, lon):
        result["fix"] = (lat, lon)
        done.set()

    location_manager = None
    listener = None

    try:
        listener = _make_listener(_report)
        location_manager = _request_updates(listener, min_time_ms=1000, min_distance_m=0)
        if location_manager is None:
            return None
        print("[SOSmart] GPS: solicitud de ubicacion iniciada, esperando fix...")
    except Exception as exc:
        print(f"[SOSmart] GPS no disponible: {exc}")
        return None

    if not done.wait(timeout):
        print(f"[SOSmart] GPS: no se recibio ninguna lectura en {timeout}s "
              f"(revisa que la Ubicacion este activada en el sistema, no solo el permiso de la app)")

    try:
        location_manager.removeUpdates(listener)
    except Exception:
        pass

    return result["fix"]


def start_tracking(on_update, min_time_ms=60000, min_distance_m=20):
    """Deja el GPS escuchando de forma continua. on_update(lat, lon) se
    llama cada vez que hay una lectura nueva (puede ser desde otro hilo).
    Devuelve un 'handle' que se debe pasar a stop_tracking(), o None si no
    se pudo iniciar."""
    try:
        listener = _make_listener(on_update)
        location_manager = _request_updates(listener, min_time_ms, min_distance_m)
        if location_manager is None:
            return None
        return (location_manager, listener)
    except Exception as exc:
        print(f"[SOSmart] No se pudo iniciar el seguimiento de ubicacion: {exc}")
        return None


def stop_tracking(handle):
    if not handle:
        return
    location_manager, listener = handle
    try:
        location_manager.removeUpdates(listener)
    except Exception:
        pass


def location_to_maps_link(fix):
    if not fix:
        return None
    lat, lon = fix
    return f"https://maps.google.com/?q={lat},{lon}"
