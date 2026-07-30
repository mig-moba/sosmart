from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from ..config import save_config

KV = """
<SettingsScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: 24
        spacing: 12

        Label:
            text: "Configuracion"
            font_size: "26sp"
            bold: True
            size_hint_y: 0.1

        Label:
            text: "Palabra clave de emergencia"
            size_hint_y: 0.06
        TextInput:
            id: keyword_input
            multiline: False
            size_hint_y: 0.08

        BoxLayout:
            size_hint_y: 0.08
            spacing: 8
            CheckBox:
                id: shake_checkbox
                size_hint_x: 0.15
            Label:
                text: "Activar al agitar el telefono (recomendado)"

        BoxLayout:
            size_hint_y: 0.08
            spacing: 8
            CheckBox:
                id: volume_checkbox
                size_hint_x: 0.15
            Label:
                text: "Activar con triple pulsacion del boton de volumen (experimental)"

        Label:
            text: "Numero de llamada rapida"
            size_hint_y: 0.06
        TextInput:
            id: emergency_phone_input
            hint_text: "Ej. +524421234567"
            multiline: False
            size_hint_y: 0.08

        Label:
            text: "Contactos de emergencia"
            size_hint_y: 0.06

        BoxLayout:
            size_hint_y: 0.1
            spacing: 8
            TextInput:
                id: contact_name
                hint_text: "Nombre"
                multiline: False
            TextInput:
                id: contact_phone
                hint_text: "Telefono"
                multiline: False
            Button:
                text: "Agregar"
                size_hint_x: 0.35
                on_release: root.add_contact()

        ScrollView:
            size_hint_y: 0.3
            BoxLayout:
                id: contacts_list
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height

        BoxLayout:
            size_hint_y: 0.12
            spacing: 12
            Button:
                text: "Guardar"
                on_release: root.save_and_back()
            Button:
                text: "Cancelar"
                on_release: root.manager.current = "home"
"""
Builder.load_string(KV)


class SettingsScreen(Screen):
    def on_pre_enter(self, *args):
        config = App.get_running_app().config_data
        self.ids.keyword_input.text = config.get("keyword", "")
        self.ids.shake_checkbox.active = config.get("shake_trigger_enabled", True)
        self.ids.volume_checkbox.active = config.get("volume_trigger_enabled", True)
        self.ids.emergency_phone_input.text = config.get("emergency_phone", "")
        self._refresh_contacts()

    def _refresh_contacts(self):
        config = App.get_running_app().config_data
        container = self.ids.contacts_list
        container.clear_widgets()
        for index, contact in enumerate(config.get("contacts", [])):
            row = BoxLayout(size_hint_y=None, height=40, spacing=8)
            row.add_widget(Label(text=f"{contact.get('name', '')} - {contact.get('phone', '')}"))
            remove_btn = Button(text="Quitar", size_hint_x=0.3)
            remove_btn.bind(on_release=lambda instance, i=index: self._remove_contact(i))
            row.add_widget(remove_btn)
            container.add_widget(row)

    def _remove_contact(self, index):
        config = App.get_running_app().config_data
        contacts = config.get("contacts", [])
        if 0 <= index < len(contacts):
            contacts.pop(index)
        self._refresh_contacts()

    def add_contact(self):
        config = App.get_running_app().config_data
        name = self.ids.contact_name.text.strip()
        phone = self.ids.contact_phone.text.strip()
        if not phone:
            return
        config.setdefault("contacts", []).append({"name": name or phone, "phone": phone})
        self.ids.contact_name.text = ""
        self.ids.contact_phone.text = ""
        self._refresh_contacts()

    def save_and_back(self):
        config = App.get_running_app().config_data
        config["keyword"] = self.ids.keyword_input.text.strip() or config.get("keyword", "")
        config["shake_trigger_enabled"] = self.ids.shake_checkbox.active
        config["volume_trigger_enabled"] = self.ids.volume_checkbox.active
        config["emergency_phone"] = self.ids.emergency_phone_input.text.strip()
        save_config(config)
        self.manager.current = "home"
