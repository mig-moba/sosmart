import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

from ..keyword_detector import listen_once, matches_keyword
from ..shake_trigger import ShakeTrigger
from ..volume_trigger import VolumeTripleTrigger

KV = """
<HomeScreen>:
    canvas.before:
        Color:
            rgba: 0.07, 0.07, 0.1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: "vertical"
        padding: 24
        spacing: 16

        Label:
            text: "SOSmart"
            font_size: "32sp"
            bold: True
            size_hint_y: 0.15

        Label:
            id: keyword_label
            text: "Palabra clave: ..."
            font_size: "16sp"
            size_hint_y: 0.08

        Label:
            id: status_label
            text: "Presiona SOS o escucha tu palabra clave"
            font_size: "14sp"
            size_hint_y: 0.1

        Button:
            text: "SOS"
            font_size: "40sp"
            background_color: 0.8, 0.1, 0.1, 1
            size_hint_y: 0.35
            on_release: root.trigger_manual_alert()

        Button:
            text: "Escuchar palabra clave"
            size_hint_y: 0.15
            on_release: root.listen_for_keyword()

        Button:
            text: "Configuracion"
            size_hint_y: 0.12
            on_release: root.manager.current = "settings"
"""
Builder.load_string(KV)


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._volume_trigger = VolumeTripleTrigger(on_trigger=self.trigger_manual_alert)
        self._shake_trigger = ShakeTrigger(on_trigger=self.trigger_manual_alert)

    def on_pre_enter(self, *args):
        config = App.get_running_app().config_data
        self.ids.keyword_label.text = f"Palabra clave: {config.get('keyword', '')}"
        self.ids.status_label.text = "Presiona SOS o escucha tu palabra clave"

        if config.get("volume_trigger_enabled", True):
            self._volume_trigger.enable()
        else:
            self._volume_trigger.disable()

        if config.get("shake_trigger_enabled", True):
            self._shake_trigger.enable()
        else:
            self._shake_trigger.disable()

    def on_leave(self, *args):
        self._volume_trigger.disable()
        self._shake_trigger.disable()

    def trigger_manual_alert(self):
        self.manager.current = "alert"

    def listen_for_keyword(self):
        self.ids.status_label.text = "Escuchando..."
        threading.Thread(target=self._listen_worker, daemon=True).start()

    def _listen_worker(self):
        config = App.get_running_app().config_data
        text = listen_once(timeout=config.get("listen_seconds", 8))
        matched = matches_keyword(text, config.get("keyword", ""))
        Clock.schedule_once(lambda dt: self._on_listen_done(matched, text))

    def _on_listen_done(self, matched, text):
        if matched:
            self.ids.status_label.text = f"Palabra clave detectada: '{text}'"
            self.trigger_manual_alert()
        else:
            shown = text if text else "(nada reconocido)"
            self.ids.status_label.text = f"No coincide. Se escucho: {shown}"
