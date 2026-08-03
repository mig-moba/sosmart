"""Pantalla principal: boton SOS, llamada rapida, escucha de la palabra
clave y los disparadores pasivos (sacudida, volumen). La escucha de voz
se activa sola una vez por sesion al abrir la app; despues de eso solo se
reactiva a mano (boton) o reabriendo la app, para no seguir escuchando
una palabra clave vieja si el usuario la cambia en Configuracion.
"""

import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

from .. import call_service
from .. import service_control
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
            size_hint_y: 0.3
            on_release: root.trigger_manual_alert()

        Button:
            text: "Llamada rapida"
            font_size: "20sp"
            background_color: 0.1, 0.4, 0.7, 1
            size_hint_y: 0.15
            on_release: root.call_emergency_number()

        Button:
            id: listen_button
            text: "Activar escucha de palabra clave"
            size_hint_y: 0.13
            on_release: root.start_auto_listening()

        Button:
            id: stop_tracking_button
            text: "Detener seguimiento activo"
            size_hint_y: 0.1
            background_color: 0.5, 0.1, 0.1, 1
            opacity: 0
            disabled: True
            on_release: root.stop_tracking()

        Button:
            text: "Configuracion"
            size_hint_y: 0.1
            on_release: root.manager.current = "settings"
"""
Builder.load_string(KV)


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._volume_trigger = VolumeTripleTrigger(on_trigger=self.trigger_manual_alert)
        self._shake_trigger = ShakeTrigger(on_trigger=self.trigger_manual_alert)
        self._auto_listen_started = False
        self._listening_active = False

    def on_pre_enter(self, *args):
        config = App.get_running_app().config_data
        self.ids.keyword_label.text = f"Palabra clave: {config.get('keyword', '')}"
        self._refresh_tracking_button()

        if config.get("volume_trigger_enabled", True):
            self._volume_trigger.enable()
        else:
            self._volume_trigger.disable()

        if config.get("shake_trigger_enabled", True):
            self._shake_trigger.enable()
        else:
            self._shake_trigger.disable()

        # La escucha automatica solo se activa sola la primera vez que se
        # abre la app en esta sesion. Si el usuario entra a Configuracion
        # (por ejemplo a cambiar la palabra clave) y regresa, no se
        # reactiva sola: hay que presionar el boton, para no seguir
        # escuchando la palabra clave vieja mientras se edita la nueva.
        if not self._auto_listen_started:
            self._auto_listen_started = True
            self.start_auto_listening()
        elif not self._listening_active:
            self.ids.status_label.text = "Presiona SOS o activa la escucha de palabra clave"

    def on_leave(self, *args):
        self._volume_trigger.disable()
        self._shake_trigger.disable()
        self.stop_auto_listening()

    def _refresh_tracking_button(self):
        active = service_control.is_tracking_active()
        self.ids.stop_tracking_button.opacity = 1 if active else 0
        self.ids.stop_tracking_button.disabled = not active

    def stop_tracking(self):
        service_control.stop_tracking_service()
        self._refresh_tracking_button()

    def call_emergency_number(self):
        config = App.get_running_app().config_data
        phone = config.get("emergency_phone", "")
        if not phone:
            self.ids.status_label.text = "No hay numero de llamada rapida configurado"
            return
        call_service.call_number(phone)

    def trigger_manual_alert(self):
        self.manager.current = "alert"

    # --- Escucha automatica de la palabra clave ---

    def start_auto_listening(self):
        if self._listening_active:
            return
        self._listening_active = True
        self.ids.listen_button.text = "Escuchando..."
        self.ids.status_label.text = "Escuchando tu palabra clave..."
        threading.Thread(target=self._auto_listen_worker, daemon=True).start()

    def stop_auto_listening(self):
        self._listening_active = False
        self.ids.listen_button.text = "Activar escucha de palabra clave"

    def _auto_listen_worker(self):
        config = App.get_running_app().config_data
        keyword = config.get("keyword", "")
        listen_seconds = config.get("listen_seconds", 8)

        while self._listening_active:
            text = listen_once(timeout=listen_seconds)
            if not self._listening_active:
                break
            if matches_keyword(text, keyword):
                Clock.schedule_once(lambda dt: self._on_keyword_matched(text))
                break

    def _on_keyword_matched(self, text):
        self._listening_active = False
        self.ids.status_label.text = f"Palabra clave detectada: '{text}'"
        self.trigger_manual_alert()
