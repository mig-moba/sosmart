import threading
import time

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

from .. import audio_recorder
from .. import location_service
from .. import sms_service
from ..alert_service import trigger_alert

KV = """
<AlertScreen>:
    canvas.before:
        Color:
            rgba: 0.5, 0.05, 0.05, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: "vertical"
        padding: 24
        spacing: 16

        Label:
            id: countdown_label
            text: "5"
            font_size: "80sp"
            bold: True

        Label:
            id: status_label
            text: "Enviando alerta en..."
            font_size: "18sp"

        Button:
            id: action_button
            text: "Cancelar"
            size_hint_y: 0.2
            on_release: root.cancel()
"""
Builder.load_string(KV)

RECORDING_SECONDS = 60


class AlertScreen(Screen):
    _event = None
    _recording_stop_event = None
    _tracking_handle = None
    _tracking_deadline_event = None
    _tracking_contacts = None
    _tracking_interval = 180
    _last_update_sent = 0

    def on_pre_enter(self, *args):
        config = App.get_running_app().config_data
        self._remaining = config.get("countdown_seconds", 5)
        self.ids.countdown_label.text = str(self._remaining)
        self.ids.status_label.text = "Enviando alerta en..."
        self.ids.action_button.text = "Cancelar"
        self._event = Clock.schedule_interval(self._tick, 1)

    def on_leave(self, *args):
        # Red de seguridad: si salimos de esta pantalla por cualquier via
        # (cancelar, volver, etc.) nos aseguramos de no dejar el microfono
        # grabando ni el GPS escuchando en segundo plano.
        if self._recording_stop_event:
            self._recording_stop_event.cancel()
            self._recording_stop_event = None
        audio_recorder.stop_recording()
        self._stop_live_tracking()

    def _tick(self, dt):
        self._remaining -= 1
        if self._remaining <= 0:
            self._event.cancel()
            self._send_alert()
        else:
            self.ids.countdown_label.text = str(self._remaining)

    def cancel(self):
        if self._event:
            self._event.cancel()
        self.manager.current = "home"

    def _send_alert(self):
        self.ids.status_label.text = "Enviando alerta..."
        audio_recorder.start_recording()
        self._recording_stop_event = Clock.schedule_once(self._stop_recording, RECORDING_SECONDS)
        threading.Thread(target=self._send_worker, daemon=True).start()

    def _stop_recording(self, *args):
        audio_recorder.stop_recording()
        self._recording_stop_event = None

    def _send_worker(self):
        config = App.get_running_app().config_data
        result = trigger_alert(config)
        Clock.schedule_once(lambda dt: self._on_sent(result))

    def _on_sent(self, result):
        sent = sum(1 for _, ok in result["results"] if ok)
        total = len(result["results"])
        self.ids.action_button.text = "Detener alerta"
        if total == 0:
            self.ids.status_label.text = "Alerta procesada (sin contactos configurados)"
        else:
            self.ids.status_label.text = f"Alerta enviada a {sent}/{total} contactos"

        config = App.get_running_app().config_data
        if total > 0 and config.get("live_tracking_enabled", True):
            self._start_live_tracking(config)

    # --- Ubicacion en tiempo real ---

    def _start_live_tracking(self, config):
        self._tracking_contacts = config.get("contacts", [])
        self._tracking_interval = config.get("live_tracking_interval_seconds", 180)
        self._last_update_sent = time.time()

        self._tracking_handle = location_service.start_tracking(self._on_location_update)
        if self._tracking_handle is None:
            return

        duration_min = config.get("live_tracking_duration_minutes", 15)
        self._tracking_deadline_event = Clock.schedule_once(
            self._stop_live_tracking, duration_min * 60
        )

    def _on_location_update(self, lat, lon):
        # Puede llegar desde el hilo/looper de Android; se agenda en el
        # hilo principal de Kivy antes de tocar cualquier estado.
        Clock.schedule_once(lambda dt: self._maybe_send_update(lat, lon))

    def _maybe_send_update(self, lat, lon):
        now = time.time()
        if now - self._last_update_sent < self._tracking_interval:
            return
        self._last_update_sent = now

        link = location_service.location_to_maps_link((lat, lon))
        message = f"ALERTA SOSmart (actualizacion): nueva ubicacion: {link}"
        contacts = self._tracking_contacts
        threading.Thread(
            target=sms_service.send_to_contacts, args=(contacts, message), daemon=True
        ).start()

    def _stop_live_tracking(self, *args):
        if self._tracking_handle:
            location_service.stop_tracking(self._tracking_handle)
            self._tracking_handle = None
        if self._tracking_deadline_event:
            self._tracking_deadline_event.cancel()
            self._tracking_deadline_event = None
