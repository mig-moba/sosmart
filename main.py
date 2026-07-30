from kivy.app import App
from kivy.uix.screenmanager import NoTransition, ScreenManager

from sosmart.config import load_config
from sosmart.permissions import request_android_permissions, show_over_lock_screen
from sosmart.screens.alert import AlertScreen
from sosmart.screens.home import HomeScreen
from sosmart.screens.settings import SettingsScreen


class SOSmartApp(App):
    def build(self):
        self.config_data = load_config()
        request_android_permissions()
        show_over_lock_screen()

        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(AlertScreen(name="alert"))
        sm.current = "home"
        return sm

    def on_pause(self):
        # Al salir de la app (boton de inicio, cambiar de app, etc.) se
        # detiene la escucha de la palabra clave; no debe seguir usando el
        # microfono en segundo plano. El seguimiento de ubicacion en vivo
        # (si esta activo) sigue corriendo aparte, en el servicio.
        home_screen = self.root.get_screen("home")
        home_screen.stop_auto_listening()
        return True

    def on_stop(self):
        home_screen = self.root.get_screen("home")
        home_screen.stop_auto_listening()


if __name__ == "__main__":
    SOSmartApp().run()
