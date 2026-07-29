import threading

try:
    from plyer import gps
except Exception:
    gps = None


def get_location_once(timeout=10):
    """Intenta obtener una sola lectura de GPS. Devuelve (lat, lon) o None."""
    if gps is None:
        return None

    result = {"fix": None}
    done = threading.Event()

    def on_location(**kwargs):
        lat = kwargs.get("lat")
        lon = kwargs.get("lon")
        if lat is not None and lon is not None:
            result["fix"] = (lat, lon)
            done.set()

    def on_status(stype, status):
        pass

    try:
        gps.configure(on_location=on_location, on_status=on_status)
        gps.start(minTime=1000, minDistance=0)
    except Exception as exc:
        print(f"[SOSmart] GPS no disponible: {exc}")
        return None

    done.wait(timeout)

    try:
        gps.stop()
    except Exception:
        pass

    return result["fix"]


def location_to_maps_link(fix):
    if not fix:
        return None
    lat, lon = fix
    return f"https://maps.google.com/?q={lat},{lon}"
