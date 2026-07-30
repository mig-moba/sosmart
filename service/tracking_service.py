"""Punto de entrada del servicio Android de seguimiento en primer plano.

Se ejecuta en un proceso aparte del de la app principal (Android lo exige
para que un servicio sea confiable en segundo plano), por eso vuelve a
cargar su propia configuracion desde disco en vez de depender de nada en
memoria de la pantalla de alerta.

Se detiene solo despues de 'live_tracking_duration_minutes' minutos, o de
inmediato si la app principal llama a ServiceTracking.stop(...) (ver
sosmart/service_control.py), que Android traduce en destruir este proceso.
"""

import os
import time

from android import AndroidService
from jnius import autoclass

from sosmart.config import load_config
from sosmart import location_service
from sosmart import sms_service

service = AndroidService('SOSmart', 'Compartiendo tu ubicacion con tus contactos')
service.start('SOSmart activo')

PythonService = autoclass('org.kivy.android.PythonService')
context = PythonService.mService

flag_path = os.path.join(context.getFilesDir().getAbsolutePath(), "tracking_active.flag")

try:
    with open(flag_path, "w", encoding="utf-8") as f:
        f.write("1")

    config = load_config()
    contacts = config.get("contacts", [])
    interval = config.get("live_tracking_interval_seconds", 180)
    duration_minutes = config.get("live_tracking_duration_minutes", 15)
    deadline = time.time() + duration_minutes * 60

    state = {"last_sent": 0.0}

    def on_update(lat, lon):
        now = time.time()
        if now - state["last_sent"] < interval:
            return
        state["last_sent"] = now
        link = location_service.location_to_maps_link((lat, lon))
        message = f"ALERTA SOSmart (actualizacion): nueva ubicacion: {link}"
        print(f"[SOSmart] Servicio: enviando actualizacion de ubicacion a {len(contacts)} contactos")
        sms_service.send_to_contacts(contacts, message)

    handle = location_service.start_tracking(on_update, context=context)

    while time.time() < deadline:
        time.sleep(5)

    location_service.stop_tracking(handle)
finally:
    if os.path.exists(flag_path):
        os.remove(flag_path)
