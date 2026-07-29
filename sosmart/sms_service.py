"""Envio de SMS de emergencia.

En Android usa android.telephony.SmsManager (via pyjnius) para enviar el
mensaje automaticamente, sin abrir la app de mensajes ni requerir que la
victima confirme el envio. Requiere el permiso SEND_SMS concedido en tiempo
de ejecucion (ver buildozer.spec).

En cualquier otra plataforma (por ejemplo, pruebas en escritorio sin
Android) solo se registra en consola el mensaje que se habria enviado, para
poder probar el resto del flujo sin un dispositivo real.
"""


def send_sms(phone_number, message):
    try:
        from jnius import autoclass

        sms_manager_cls = autoclass("android.telephony.SmsManager")
        manager = sms_manager_cls.getDefault()
        manager.sendTextMessage(phone_number, None, message, None, None)
        return True
    except Exception as exc:
        print(f"[SOSmart] (sin Android) SMS simulado a {phone_number}: {message} ({exc})")
        return False


def send_to_contacts(contacts, message):
    results = []
    for contact in contacts:
        phone = contact.get("phone")
        if not phone:
            continue
        ok = send_sms(phone, message)
        results.append((contact.get("name", phone), ok))
    return results
