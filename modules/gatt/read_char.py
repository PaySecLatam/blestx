import asyncio
from core import client  

INFO = {
    "name": "GATT Reader",
    "author": "Stux",
    "description": "Permite leer el valor de una característica GATT usando su UUID o leer todas las características read.",
    "options": {
        "run": "Usa la conexión global para interactuar con la característica establecida y leer todas las que tengan esta propiedad",
        "uuid_characteristic": "UUID corto o completo de la característica a leer"
    }
}

OPTIONS = {
    "uuid_characteristic": "",  
}

async def run(uuid_characteristic=None):
    """
    Lee características GATT usando el cliente global y el cache.
    """
    if client.GLOBAL_CLIENT is None or not client.GLOBAL_CLIENT.is_connected:
        print("[!] No hay un cliente global conectado. Conecta un dispositivo primero desde scan.")
        return

    ble_client = client.GLOBAL_CLIENT
    uuid_characteristic = uuid_characteristic or OPTIONS.get("uuid_characteristic", "")

    try:
        
        if not hasattr(ble_client, 'services') or not ble_client.services:
            await ble_client.get_services()

        
        for s in ble_client.services:
            for c in s.characteristics:
                client.cache_characteristic(c)

        
        if not uuid_characteristic:
            print("📋 Leyendo todas las características con propiedad READ...\n")
            for uuid, ch in client.GATT_CACHE.items():
                
                if len(uuid) > 8 and "read" in getattr(ch, "properties", []):
                    await read_characteristic(ble_client, ch)
            return

        
        characteristic_obj = client.get_characteristic(uuid_characteristic)
        if not characteristic_obj or "read" not in getattr(characteristic_obj, "properties", []):
            print(f"[!] No se encontró ninguna característica read para el UUID {uuid_characteristic}")
            print("📋 Características disponibles (read):")
            for ch in client.GATT_CACHE.values():
                if "read" in getattr(ch, "properties", []):
                    print(f"   UUID: {ch.uuid}, Handle: {getattr(ch, 'handle', '?')}")
            return

        
        await read_characteristic(ble_client, characteristic_obj)

    except Exception as e:
        print(f"[!] Error durante la lectura: {e}")


async def read_characteristic(ble_client, ch):
    """Lee y muestra información de una característica"""
    handle = getattr(ch, "handle", "?")
    print(f"✅ Característica: UUID {ch.uuid}, Handle {handle}, Propiedades: {', '.join(ch.properties)}")
    try:
        data = await ble_client.read_gatt_char(ch)
        print(f"📨 Datos (hex): {data.hex()}")
        print(f"   Longitud: {len(data)} bytes")
        try:
            text = data.decode('utf-8', errors='ignore').strip()
            if text:
                print(f"   Texto: '{text}'")
        except:
            pass
        print("")
    except Exception as e:
        print(f"[!] Error leyendo {ch.uuid}: {e}")
