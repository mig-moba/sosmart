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


def get_location_once(timeout=20):
    try:
        from jnius import autoclass, java_method, PythonJavaClass
        from plyer.platforms.android import activity
    except Exception:
        return None  # No es Android (por ejemplo, pruebas en escritorio).

    result = {"fix": None}
    done = threading.Event()

    def _report(lat, lon):
        result["fix"] = (lat, lon)
        done.set()

    location_manager = None
    listener = None

    try:
        Looper = autoclass('android.os.Looper')
        LocationManager = autoclass('android.location.LocationManager')
        Context = autoclass('android.content.Context')

        class _Listener(PythonJavaClass):
            __javainterfaces__ = ['android/location/LocationListener']

            @java_method('(Landroid/location/Location;)V')
            def onLocationChanged(self, location):
                _report(location.getLatitude(), location.getLongitude())

            @java_method('(Ljava/util/List;)V', name='onLocationChanged')
            def onLocationChangedBatch(self, locations):
                size = locations.size()
                if size > 0:
                    location = locations.get(size - 1)
                    _report(location.getLatitude(), location.getLongitude())

            @java_method('(Ljava/lang/String;)V')
            def onProviderEnabled(self, provider):
                print(f"[SOSmart] GPS proveedor activado: {provider}")

            @java_method('(Ljava/lang/String;)V')
            def onProviderDisabled(self, provider):
                print(f"[SOSmart] GPS proveedor desactivado: {provider}")

            @java_method('(Ljava/lang/String;ILandroid/os/Bundle;)V')
            def onStatusChanged(self, provider, status, extras):
                pass

        listener = _Listener()
        location_manager = activity.getSystemService(Context.LOCATION_SERVICE)
        providers = location_manager.getProviders(False).toArray()

        if not providers:
            print("[SOSmart] GPS: no hay ningun proveedor de ubicacion disponible")

        for provider in providers:
            location_manager.requestLocationUpdates(
                provider, 1000, 0, listener, Looper.getMainLooper()
            )
        print("[SOSmart] GPS: solicitud de ubicacion iniciada, esperando fix...")
    except Exception as exc:
        print(f"[SOSmart] GPS no disponible: {exc}")
        return None

    if not done.wait(timeout):
        print(f"[SOSmart] GPS: no se recibio ninguna lectura en {timeout}s "
              f"(revisa que la Ubicacion este activada en el sistema, no solo el permiso de la app)")

    if location_manager is not None and listener is not None:
        try:
            location_manager.removeUpdates(listener)
        except Exception:
            pass

    return result["fix"]


def location_to_maps_link(fix):
    if not fix:
        return None
    lat, lon = fix
    return f"https://maps.google.com/?q={lat},{lon}"
