"""Orquesta el envio de la alerta inicial: arma el mensaje (con o sin
ubicacion, segun si el GPS respondio a tiempo) y lo manda por SMS a todos
los contactos configurados. Las actualizaciones de ubicacion posteriores
(seguimiento en tiempo real) las maneja aparte el servicio en segundo
plano, ver service/tracking_service.py.
"""

from . import location_service
from . import sms_service


def build_message(user_label="Usuario de SOSmart"):
    fix = location_service.get_location_once(timeout=20)
    link = location_service.location_to_maps_link(fix)
    if link:
        return f"ALERTA SOSmart: {user_label} necesita ayuda. Ubicacion: {link}"
    return f"ALERTA SOSmart: {user_label} necesita ayuda. No se pudo obtener la ubicacion."


def trigger_alert(config):
    message = build_message()
    contacts = config.get("contacts", [])
    results = sms_service.send_to_contacts(contacts, message)
    return {"message": message, "results": results}
