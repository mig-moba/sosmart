from kivy.app import App
from kivy.uix.screenmanager import NoTransition, ScreenManager

from sosmart.config import load_config
from sosmart.screens.alert import AlertScreen
from sosmart.screens.home import HomeScreen
from sosmart.screens.settings import SettingsScreen


class SOSmartApp(App):
    def build(self):
        self.config_data = load_config()

        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(AlertScreen(name="alert"))
        sm.current = "home"
        return sm


if __name__ == "__main__":
    SOSmartApp().run()
