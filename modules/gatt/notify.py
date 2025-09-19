import asyncio
from core import client

INFO = {
    "name": "GATT Notify",
    "author": "Stux",
    "description": "Se suscribe a notificaciones o indicaciones de una característica GATT para recibir datos en tiempo real.",
    "options": {
        "run": "Usa la conexión global para intecturas con la característica establecida",
        "uuid_characteristic": "UUID de la característica para suscribirse",
        #"handle": "Handle opcional de la característica", no implementada aun
        "max_messages": " máximo de mensajes para recibir notificaciones (default=10)"
    }
}

OPTIONS = {
    "uuid_characteristic": "",
    "max_messages": 10,
}

stop_notifications = False
received_messages = 0

async def run(uuid_characteristic=None, max_messages=None):
    global stop_notifications, received_messages

    if client.GLOBAL_CLIENT is None or not client.GLOBAL_CLIENT.is_connected:
        print("[!] No hay un cliente global conectado.")
        return

    ble_client = client.GLOBAL_CLIENT
    stop_notifications = False
    received_messages = 0

    uuid_characteristic = uuid_characteristic or OPTIONS.get("uuid_characteristic", "")
    max_messages = max_messages or OPTIONS.get("max_messages", 10)

    if not uuid_characteristic:
        print("[!] Debes especificar el UUID de la característica")
        return

    
    if not hasattr(ble_client, "services") or not ble_client.services:
        await ble_client.get_services()

    
    characteristic_obj = None
    service_obj = None
    for s in ble_client.services:
        for c in s.characteristics:
            if c.uuid.lower() == uuid_characteristic.lower() and ("notify" in c.properties or "indicate" in c.properties):
                characteristic_obj = c
                service_obj = s
                break
        if characteristic_obj:
            break

    if not characteristic_obj:
        print(f"[!] No se encontró característica notify/indicate para UUID {uuid_characteristic}")
        return

    print(f"✅ Característica encontrada: {characteristic_obj.uuid}")
    print(f"   Servicio: {service_obj.uuid}")
    print(f"   Propiedades: {', '.join(characteristic_obj.properties)}")

    
    def notification_handler(sender, data):
        global received_messages, stop_notifications
        received_messages += 1
        print(f"\n📨 Notificación #{received_messages}")
        print(f"   Handle: {getattr(sender,'handle',sender)}")
        print(f"   Datos (hex): {data.hex()}")
        print(f"   Longitud: {len(data)} bytes")
        try:
            text = data.decode("utf-8", errors="ignore").strip()
            if text:
                print(f"   Texto: '{text}'")
        except:
            pass
        if received_messages >= max_messages:
            stop_notifications = True

    
    await ble_client.start_notify(characteristic_obj, notification_handler)
    print("🎯 Esperando notificaciones... (Ctrl+C para salir al CLI)")

    try:
        while not stop_notifications:
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        
        print("\n⏹️ Interrupción manual: volviendo al CLI...")
    finally:
        await ble_client.stop_notify(characteristic_obj)
        print("✅ Notificaciones detenidas")
        print(f"\n📊 Mensajes recibidos: {received_messages}")
