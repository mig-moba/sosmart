import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

from .. import audio_recorder
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
            text: "Cancelar"
            size_hint_y: 0.2
            on_release: root.cancel()
"""
Builder.load_string(KV)


class AlertScreen(Screen):
    _event = None

    def on_pre_enter(self, *args):
        config = App.get_running_app().config_data
        self._remaining = config.get("countdown_seconds", 5)
        self.ids.countdown_label.text = str(self._remaining)
        self.ids.status_label.text = "Enviando alerta en..."
        self._event = Clock.schedule_interval(self._tick, 1)

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
        threading.Thread(target=self._send_worker, daemon=True).start()

    def _send_worker(self):
        config = App.get_running_app().config_data
        result = trigger_alert(config)
        Clock.schedule_once(lambda dt: self._on_sent(result))

    def _on_sent(self, result):
        sent = sum(1 for _, ok in result["results"] if ok)
        total = len(result["results"])
        if total == 0:
            self.ids.status_label.text = "Alerta procesada (sin contactos configurados)"
        else:
            self.ids.status_label.text = f"Alerta enviada a {sent}/{total} contactos"
