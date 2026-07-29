# SOSmart (prototipo)

Aplicacion movil de alerta de emergencia. Activa una alerta (ubicacion GPS +
SMS automatico a contactos de confianza + grabacion de audio) mediante:

1. Boton SOS manual en pantalla.
2. Palabra clave configurable, detectada al pulsar "Escuchar palabra clave"
   (ventana corta de escucha, no microfono siempre activo).
3. Agitar el telefono (acelerometro) - metodo manos-libres recomendado.
4. Triple pulsacion del boton de volumen (experimental, ver limitacion abajo).

Los metodos 3 y 4 se activan/desactivan por separado desde Configuracion.

## Estructura

```
main.py                    Punto de entrada (Kivy App + ScreenManager)
sosmart/
  config.py                Carga/guarda config.json (palabra clave, contactos, ajustes)
  keyword_detector.py      Reconocimiento de voz y comparacion con la palabra clave
  shake_trigger.py         Deteccion de sacudida (acelerometro) - recomendado
  volume_trigger.py        Deteccion de triple pulsacion de volumen - experimental
  location_service.py      Lectura de GPS (plyer)
  sms_service.py           Envio automatico de SMS (SmsManager via pyjnius)
  audio_recorder.py        Grabacion de audio de evidencia
  alert_service.py         Orquesta: ubicacion + SMS al disparar una alerta
  screens/
    home.py                Pantalla principal (SOS, escuchar palabra clave)
    settings.py            Configurar palabra clave y contactos
    alert.py                Cuenta regresiva antes de enviar (con boton Cancelar)
```

## Probar en escritorio (desarrollo de UI)

```bash
pip install -r requirements.txt
python main.py
```

En escritorio no hay GPS, SMS real ni microfono Android: esas funciones
imprimen en consola lo que habrian hecho, para poder probar el flujo de
pantallas sin un telefono.

## Generar el APK (Android)

Buildozer solo corre en Linux. En Windows, usar WSL:

```bash
pip install buildozer
buildozer -v android debug
```

El primer build descarga el Android SDK/NDK y tarda bastante. El APK queda
en `bin/`.

## Limitaciones conocidas (importantes para la demo)

- **Agitar el telefono**: es el metodo manos-libres mas confiable de este
  prototipo, ya que el acelerometro (via plyer) si es accesible desde Python
  puro sin restricciones especiales de Android. El umbral de sensibilidad
  (`threshold` en `shake_trigger.py`) es un valor de partida y conviene
  calibrarlo en un dispositivo real (se imprime cada delta para facilitar el
  ajuste).
- **Triple pulsacion de volumen**: Android restringe, desde la version 7, la
  entrega de eventos de volumen a apps que no tienen el foco (pantalla
  bloqueada o app cerrada). `volume_trigger.py` funciona mientras SOSmart
  esta abierta; los codigos de tecla reales pueden variar por dispositivo y
  deben verificarse con `adb logcat` (el modulo imprime cada tecla detectada).
  Capturar el boton de forma global (pantalla bloqueada) requeriria un
  Accessibility Service nativo de Android, fuera del alcance de este
  prototipo en Python puro. Por eso queda como metodo secundario junto con
  la sacudida, en vez de reemplazar por completo un metodo por el otro.
- **Reconocimiento de voz**: no hay escucha continua en segundo plano; el
  usuario debe abrir la app y tocar "Escuchar palabra clave" (o usarla justo
  despues de un disparo por volumen/SOS).
- **SMS automatico**: requiere que el usuario otorgue el permiso `SEND_SMS`
  en el telefono la primera vez que se instala la app.
