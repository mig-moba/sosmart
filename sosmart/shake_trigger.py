"""Disparo de alerta al agitar el telefono (acelerometro).

A diferencia del boton de volumen, el acelerometro si es accesible de forma
confiable desde plyer en Android sin necesitar codigo nativo adicional, y
funciona igual mientras la app esta abierta. Es el metodo manos-libres mas
robusto de este prototipo (no depende de que Android decida entregar o no
un evento de tecla de hardware).

El "threshold" es un valor de partida; conviene ajustarlo probando en un
telefono real (se imprime cada valor de delta para facilitar la calibracion).
"""

import time

from kivy.clock import Clock

try:
    from plyer import accelerometer
except Exception:
    accelerometer = None


class ShakeTrigger:
    def __init__(self, on_trigger, threshold=25.0, min_interval=1.5, poll_interval=0.15):
        self.on_trigger = on_trigger
        self.threshold = threshold
        self.min_interval = min_interval
        self.poll_interval = poll_interval
        self._last_trigger = 0
        self._last_values = None
        self._event = None
        self._running = False

    def enable(self):
        if accelerometer is None or self._running:
            return
        try:
            accelerometer.enable()
        except Exception as exc:
            print(f"[SOSmart] Acelerometro no disponible: {exc}")
            return
        self._running = True
        self._event = Clock.schedule_interval(self._poll, self.poll_interval)

    def disable(self):
        if self._event:
            self._event.cancel()
            self._event = None
        if self._running and accelerometer is not None:
            try:
                accelerometer.disable()
            except Exception:
                pass
        self._running = False

    def _poll(self, dt):
        try:
            values = accelerometer.acceleration[:3]
        except Exception:
            return
        if values is None or None in values:
            return

        if self._last_values is not None:
            delta = sum(abs(a - b) for a, b in zip(values, self._last_values))
            now = time.time()
            if delta > self.threshold and (now - self._last_trigger) > self.min_interval:
                self._last_trigger = now
                self.on_trigger()

        self._last_values = values
