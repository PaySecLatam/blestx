import asyncio
from core import client

INFO = {
    "name": "GATT Writer",
    "author": "Stux",
    "description": "Permite enviar datos arbitrarios a una característica GATT específica del dispositivo.",
    "options": {
        "run": "Usa la conexión global para interactuar con la característica establecida",
        "uuid_characteristic": "UUID de la característica a escribir (full o short ej: 0x2a37)",
        "handle": "Handle en formato decimal o hexadecimal (ej: 63 o 0x3f)",
        "mode": "Permite enviar la información al descriptor en ascii o hexadecimal",
        "message": "Datos a enviar en formato hex o string"
    }
}

OPTIONS = {
    "uuid_characteristic": "",  
    "handle": "",               
    "mode": "ascii",            
    "message": ""              
}

def _looks_like_hex(s: str) -> bool:
    try:
        s_clean = s.replace(" ", "")
        if len(s_clean) == 0 or len(s_clean) % 2 != 0:
            return False
        bytes.fromhex(s_clean)
        return True
    except ValueError:
        return False

def _parse_handle(h):
    if not h:
        return None
    try:
        return int(h, 16) if isinstance(h, str) and h.lower().startswith("0x") else int(h)
    except Exception:
        return None

def _short_uuid(uuid: str) -> str:
    u = uuid.lower()
    base = "-0000-1000-8000-00805f9b34fb"
    if u.startswith("0000") and u.endswith(base):
        return "0x" + u[4:8]
    return u

async def run(uuid_characteristic=None, handle=None, mode=None, message=None):
    if client.GLOBAL_CLIENT is None or not client.GLOBAL_CLIENT.is_connected:
        print("[!] No hay un cliente global conectado. Conecta un dispositivo primero desde scan.")
        return

    ble_client = client.GLOBAL_CLIENT

    uuid_characteristic = uuid_characteristic or OPTIONS.get("uuid_characteristic", "")
    handle = handle or OPTIONS.get("handle", "")
    mode = (mode or OPTIONS.get("mode", "ascii")).lower()
    message = message or OPTIONS.get("message", "")

    if not uuid_characteristic and not handle:
        print("[!] Debes especificar el UUID de la característica o el handle")
        return

    if not message:
        print("[!] Debes asignar un mensaje usando 'set message <valor>'")
        return

    if mode not in ("ascii", "hex"):
        print("[!] Modo inválido. Usa 'set mode ascii' o 'set mode hex'")
        return

    if mode == "hex" and not _looks_like_hex(message):
        print("[!] Advertencia: el mensaje no parece HEX válido, revisa tu entrada.")

    try:
        if not hasattr(ble_client, 'services') or not ble_client.services:
            await ble_client.get_services()

        service_obj, characteristic_obj = None, None
        target_handle = _parse_handle(handle)

        # Búsqueda por handle
        if target_handle:
            for s in ble_client.services:
                for c in s.characteristics:
                    if getattr(c, "handle", None) == target_handle:
                        service_obj, characteristic_obj = s, c
                        break
                if characteristic_obj:
                    break
            if not characteristic_obj:
                print(f"[!] No se encontró ninguna característica con handle {handle}")
                return
        else:
            uuid_characteristic = uuid_characteristic.lower()
            matches = []
            for s in ble_client.services:
                for c in s.characteristics:
                    if (c.uuid.lower() == uuid_characteristic or _short_uuid(c.uuid) == uuid_characteristic):
                        matches.append((s, c))
            if not matches:
                print(f"[!] No se encontró ninguna característica con UUID {uuid_characteristic}")
                return
            if len(matches) > 1:
                print(f"[!] Múltiples características con UUID {uuid_characteristic}:")
                for i, (s, c) in enumerate(matches):
                    props = ", ".join(c.properties)
                    print(f"[{i}] Handle: {c.handle}, Servicio: {s.uuid}, Propiedades: {props}")
                while True:
                    choice = input("Selecciona el índice o escribe el handle exacto: ").strip()
                    try:
                        idx = int(choice)
                        if 0 <= idx < len(matches):
                            service_obj, characteristic_obj = matches[idx]
                            break
                    except ValueError:
                        try:
                            handle_wanted = int(choice, 0)
                            for s, c in matches:
                                if getattr(c, "handle", None) == handle_wanted:
                                    service_obj, characteristic_obj = s, c
                                    choice = None
                                    break
                            if choice is None:
                                break
                        except ValueError:
                            pass
                    print("Selección inválida. Ingresa un índice de la lista o un handle numérico.")
            else:
                service_obj, characteristic_obj = matches[0]

        # Ajuste automático de write con o sin respuesta
        if "write" in characteristic_obj.properties:
            response = True
        elif "write-without-response" in characteristic_obj.properties:
            response = False
        else:
            print(f"[!] La característica seleccionada no soporta escritura")
            print(f"   Propiedades: {', '.join(characteristic_obj.properties)}")
            return

        print(f"✅ Característica seleccionada:")
        print(f"   Servicio: {service_obj.uuid}")
        print(f"   UUID: {characteristic_obj.uuid} ({_short_uuid(characteristic_obj.uuid)})")
        print(f"   Handle: {characteristic_obj.handle}")
        print(f"   Propiedades: {', '.join(characteristic_obj.properties)}")
        print(f"   Modo efectivo: {mode.upper()}")
        print(f"   Write {'con respuesta' if response else 'sin respuesta'}")
        print(f"   Mensaje a enviar: '{message}'")

        data = message.encode('utf-8') if mode == "ascii" else bytes.fromhex(message.replace(" ", ""))
        await ble_client.write_gatt_char(characteristic_obj, data, response=response)

        print(f"\n✅ Escrito '{message}' ({mode.upper()}) en handle {characteristic_obj.handle} ({'con respuesta' if response else 'sin respuesta'})")

    except Exception as e:
        print(f"[!] Error durante la escritura: {e}")
