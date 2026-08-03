# Documentación técnica de SOSmart

Este documento explica cómo está construida la app, cómo se empaqueta a
un APK instalable, y el proceso real (con errores incluidos) que llevó a
la versión actual. Sirve como referencia técnica complementaria al
reporte del proyecto.

## 1. Por qué Python para una app de Android

Python no es el lenguaje nativo de Android (eso sería Kotlin/Java), pero
se puede usar mediante **Kivy**, un framework de interfaz gráfica en
Python, combinado con **python-for-android** (p4a): una herramienta que
toma un proyecto de Kivy y lo compila, junto con un intérprete de Python
completo, dentro de un `.apk` instalable. **Buildozer** es la capa que
automatiza todo ese proceso (descargar el Android SDK/NDK, invocar a
p4a, empaquetar el resultado) a partir de un solo archivo de
configuración: [`buildozer.spec`](buildozer.spec).

Para hablar con las APIs nativas de Android (GPS, SMS, permisos, la
cámara del sistema, servicios en segundo plano, etc.) se usa
**pyjnius**, un puente que permite llamar clases e interfaces de Java
directamente desde Python.

## 2. Arquitectura de la app

```
main.py                      Punto de entrada (Kivy App + ScreenManager)
sosmart/
  config.py                  Configuracion persistente (JSON)
  permissions.py             Permisos en tiempo de ejecucion + pantalla bloqueada
  keyword_detector.py        Reconocimiento de voz (plyer.stt en Android)
  location_service.py        GPS: una lectura o seguimiento continuo (pyjnius)
  sms_service.py             Envio de SMS automatico (pyjnius)
  call_service.py            Llamada directa (pyjnius)
  audio_recorder.py          Grabacion de audio de evidencia (plyer)
  alert_service.py           Arma y envia la alerta inicial
  service_control.py         Arranca/detiene el servicio de seguimiento
  shake_trigger.py           Disparo por sacudida (acelerometro, plyer)
  volume_trigger.py          Disparo por volumen (experimental)
  screens/
    home.py                  Pantalla principal
    settings.py               Configuracion
    alert.py                  Cuenta regresiva + envio + seguimiento
service/
  tracking_service.py        Servicio Android en primer plano (proceso aparte)
```

**Patrón usado en todo el proyecto:** cada módulo que toca una API de
Android hace el `import` de `jnius`/`plyer` dentro de un `try/except`, de
forma que el mismo código corra (sin esas funciones) en escritorio para
poder probar la interfaz sin un teléfono real.

### 2.1 Flujo de una alerta

1. Se activa por: botón SOS, palabra clave reconocida, sacudida, o
   triple pulsación de volumen.
2. `AlertScreen` muestra una cuenta regresiva cancelable
   (`countdown_seconds` en la configuración).
3. Si no se cancela: se pide una lectura de GPS con tiempo límite
   (`location_service.get_location_once`), se arma el mensaje
   (`alert_service.build_message`) y se manda por SMS a todos los
   contactos (`sms_service.send_to_contacts`), además de iniciar la
   grabación de audio.
4. Si hay contactos, se arranca el **servicio de seguimiento en
   primer plano** (`service_control.start_tracking_service`), que sigue
   mandando SMS con la ubicación actualizada cada cierto intervalo,
   incluso si el usuario cambia de app o bloquea la pantalla.
5. El usuario puede detener el seguimiento desde la pantalla de alerta o
   desde la principal.

### 2.2 Por qué el seguimiento es un servicio de Android aparte

Un hilo de Python normal dentro de la app (`threading.Thread`) solo vive
mientras la propia Activity está activa. En cuanto Android decide
descargar el proceso en segundo plano (por batería o memoria), ese hilo
muere. Un **foreground service** (declarado en `buildozer.spec` vía
`services = Tracking:service/tracking_service.py`) corre en su **propio
proceso del sistema operativo**, con una notificación persistente, y
Android lo trata con mucha más tolerancia. Por eso
[`service/tracking_service.py`](service/tracking_service.py) no comparte
memoria con la app principal: carga su propia configuración desde disco
y se comunica con la app solo mediante un archivo de bandera
(`tracking_active.flag`) para saber si sigue corriendo.

## 3. Empaquetado: de código Python a APK

No es posible compilar para Android en Windows de forma nativa (Buildozer
requiere Linux). La solución fue automatizar todo con **GitHub Actions**:
cada vez que se sube un cambio a la rama `main`, un workflow
([`.github/workflows/build-apk.yml`](.github/workflows/build-apk.yml))
hace lo siguiente en un servidor Linux temporal, gratis, en la nube:

1. Instala Java, Python y las dependencias de sistema de Buildozer.
2. Instala `buildozer` y `python-for-android` con **versiones fijas**
   (ver sección 4.3 — esto no fue arbitrario).
3. Corre `buildozer -v android debug`, que descarga el Android
   SDK/NDK (solo la primera vez, luego queda en caché) y compila.
4. Sube el `.apk` resultante como "artifact" descargable desde la
   pestaña *Actions* del repositorio.

## 4. Bitácora de depuración (los problemas reales que se resolvieron)

Documentar esto tiene valor porque cada uno fue un error real en
producción, no hipotético, y la forma de diagnosticarlos (leer el log
completo del build, o conectar el teléfono por USB y leer su log en vivo
con `adb logcat`) es una habilidad de depuración transferible a
cualquier proyecto de software.

### 4.1 El build fallaba sin razón aparente

**Síntoma:** Buildozer avanzaba 20+ minutos compilando y fallaba al
final sin un error claro.
**Causa real:** `python-for-android` sin versión fijada tomaba Python
3.14 (recién salido) como versión objetivo, y un paso interno
(`pip install -U pip`) se actualizaba a una versión de `pip` con
archivos internos inconsistentes entre sí (`ImportError`).
**Solución:** fijar `python3==3.11.9` y `hostpython3==3.11.9` (deben
coincidir entre sí) en `buildozer.spec`, y limitar la versión de `pip`
que se puede instalar en todo el job con la variable de entorno
`PIP_CONSTRAINT` apuntando a [`constraints.txt`](constraints.txt).

### 4.2 El GPS nunca devolvía ubicación

**Síntoma:** ninguna alerta llegaba con ubicación real, sin ningún error
visible.
**Diagnóstico:** conectando el teléfono por USB y leyendo el log en vivo
con `adb logcat`, apareció un error repetido:
`NotImplementedError: onLocationChanged ... List ... is not implemented`.
**Causa real:** en Android 13+, el sistema puede invocar la sobrecarga
por lote `LocationListener.onLocationChanged(List<Location>)` en vez de
la versión individual, y la librería `plyer` solo implementa esta
última — un bug real de esa librería, no del código propio.
**Solución:** [`location_service.py`](sosmart/location_service.py)
reemplaza `plyer.gps` por un listener propio hecho con `pyjnius` que
implementa **ambas** sobrecargas.

### 4.3 El reconocimiento de voz nunca funcionaba

**Causa real:** la llamada a la API de `plyer.stt` estaba mal (`start()`
no acepta un parámetro `callback`, esa API no existe); el error se
atrapaba en silencio. Además, el idioma por defecto de `plyer.stt` es
inglés, y su lista de idiomas "soportados" ni siquiera incluye español.
**Solución:** se reescribió [`keyword_detector.py`](sosmart/keyword_detector.py)
para usar el patrón real de esa librería (`start()` sin argumentos,
resultados leídos después de `stt.results`), y se asigna el idioma
directamente al atributo interno para saltarse esa validación
incompleta de la librería.

### 4.4 Nada llegaba (SMS, GPS, micrófono) aun con el código bien

**Causa real:** en Android, declarar un permiso en el manifiesto
(`buildozer.spec` → `android.permissions`) no es suficiente desde
Android 6; hay que **pedirlo en tiempo de ejecución** y que el usuario
lo acepte en un diálogo. Nunca se estaba haciendo esa segunda parte.
**Solución:** [`permissions.py`](sosmart/permissions.py) pide los
permisos al arrancar la app, usando el módulo `android.permissions` que
python-for-android incluye automáticamente.

### 4.5 El micrófono se quedaba grabando para siempre

**Causa real:** se llamaba a `audio_recorder.start_recording()` al
activarse una alerta, pero nunca se llamaba a `stop_recording()`.
**Solución:** límite de 60 segundos vía `Clock.schedule_once`, más un
`on_leave` en `AlertScreen` que detiene la grabación como red de
seguridad si el usuario sale de esa pantalla.

### 4.6 Abrir la app con el teléfono bloqueado

Se intentó (ver `permissions.show_over_lock_screen`, usando
`FLAG_SHOW_WHEN_LOCKED` / `setShowWhenLocked`) que la app se mostrara
sobre la pantalla de bloqueo al abrirse desde el atajo de tecla lateral
de Samsung. El código corre y se configura correctamente (confirmado por
log), pero Android exige la autenticación del usuario antes de iniciar
cualquier app de terceros por ese medio — solo la Cámara tiene esa
excepción del sistema operativo. **No se encontró una forma legítima de
evitarlo**; queda documentado como objetivo no logrado en el reporte.

## 5. Cómo se depuró en un dispositivo real

Casi todos los bugs de la sección 4 se encontraron con el mismo método:

1. Conectar el teléfono por USB con la Depuración USB activada
   (Opciones de desarrollador).
2. Usar `adb.exe logcat` (herramienta oficial de Google, parte de
   *Android Platform Tools*) para ver en vivo todo lo que la app imprime
   y cualquier excepción de Android, filtrado para no ahogarse en ruido:
   ```bash
   adb logcat -v brief python:V AndroidRuntime:E *:S
   ```
3. Reproducir la falla en el teléfono mientras se observa el log.
4. Cuando el error ocurría dentro de un build de GitHub Actions (no en
   el teléfono), se descargaba el archivo de log completo del run
   (ícono de engranaje → "Download log archive") para buscar la línea
   real del error, ya que la vista web trunca logs muy largos.

Por eso casi todos los módulos de `sosmart/` tienen impresiones con el
prefijo `[SOSmart]` — son puntos de diagnóstico pensados para aparecer
en ese log y facilitar encontrar la causa real de un fallo, en vez de
adivinar.
