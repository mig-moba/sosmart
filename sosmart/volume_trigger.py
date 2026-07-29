"""Disparo de alerta por triple pulsacion del boton de volumen.

IMPORTANTE - limitacion real de Android:
Desde Android 7, el sistema no garantiza que una app reciba los eventos de
los botones de volumen si no tiene el foco (pantalla bloqueada, app en
segundo plano o cerrada). Esto es una restriccion de seguridad deliberada
de la plataforma, no una limitacion de Python. Este disparador funciona de
forma confiable solo mientras SOSmart esta abierta en primer plano.

Para capturar el boton globalmente (pantalla bloqueada / app cerrada) se
necesitaria un Accessibility Service nativo de Android, fuera del alcance
de este prototipo en Python puro. Queda documentado como trabajo futuro.

Como los codigos de tecla que Kivy recibe para botones de hardware varian
segun el dispositivo y la version de Android, este modulo imprime cada
pulsacion detectada en consola (visible con `adb logcat` o `buildozer
android logcat`) para poder ajustar VOLUME_KEYCODES con los valores reales
observados en un dispositivo físico.
"""

import time

from kivy.core.window import Window

# Valores de partida (Android KEYCODE_VOLUME_UP=24, KEYCODE_VOLUME_DOWN=25).
# Ajustar tras probar en un dispositivo real: revisar los logs impresos por
# _on_keyboard para ver que valor de "key" llega realmente.
VOLUME_KEYCODES = {24, 25}


class VolumeTripleTrigger:
    def __init__(self, on_trigger, max_gap=1.2, presses_needed=3):
        self.on_trigger = on_trigger
        self.max_gap = max_gap
        self.presses_needed = presses_needed
        self._timestamps = []
        self._bound = False

    def enable(self):
        if not self._bound:
            Window.bind(on_keyboard=self._on_keyboard)
            self._bound = True

    def disable(self):
        if self._bound:
            Window.unbind(on_keyboard=self._on_keyboard)
            self._bound = False

    def _on_keyboard(self, window, key, *args):
        print(f"[SOSmart] Tecla detectada: key={key} args={args}")

        if key not in VOLUME_KEYCODES:
            return False

        now = time.time()
        self._timestamps = [t for t in self._timestamps if now - t <= self.max_gap]
        self._timestamps.append(now)

        if len(self._timestamps) >= self.presses_needed:
            self._timestamps.clear()
            self.on_trigger()

        return True
