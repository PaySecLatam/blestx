import asyncio
import importlib
from tabulate import tabulate
from core import client

INFO = {
    "name": "GATT Explorer",
    "author": "Stux",
    "description": "Explora y enumera los servicios, características y descriptores GATT de un dispositivo BLE.",
    "options": {
        "run": "Usa la conexión global para enumerar los servicios, características y descriptores",
    }
}

OPTIONS = {
    "timeout": 10.0,
}


BASE_SUFFIX = "-0000-1000-8000-00805f9b34fb"

def is_sig_uuid(u: str) -> bool:
    u = u.lower()
    return u.startswith("0000") and u.endswith(BASE_SUFFIX)

def get_short_uuid(u: str) -> str:
    u = u.lower()
    if is_sig_uuid(u):
        return "0x" + u[4:8]
    return u[:8]

def resolve_uuid_name(u: str) -> str:
    try:
        uuids_mod = importlib.import_module("bleak.uuids")
    except Exception:
        return ""

    candidates = []
    for attr in (
        "uuid16_dict", "uuid128_dict",
        "UUID16_DICT", "UUID128_DICT",
        "uuid16", "uuid128"
    ):
        d = getattr(uuids_mod, attr, None)
        if isinstance(d, dict):
            candidates.append(d)

    if not candidates:
        return ""

    u_l = u.lower()
    for d in candidates:
        name = d.get(u_l)
        if name:
            return name
        if is_sig_uuid(u_l):
            short_hex = u_l[4:8]
            name = d.get("0x" + short_hex) or d.get(short_hex)
            if name:
                return name
            try:
                return d.get(int(short_hex, 16), "")
            except Exception:
                pass
    return ""

def format_properties(properties):
    prop_map = {
        "read": "READ",
        "write": "WRITE",
        "write-without-response": "WRITE_NO_RESP",
        "notify": "NOTIFY",
        "indicate": "INDICATE",
        "broadcast": "BROADCAST",
        "authenticated-signed-writes": "SIGNED_WRITES",
        "reliable-write": "RELIABLE_WRITE",
        "writable-auxiliaries": "WRITABLE_AUX",
    }
    return ", ".join(prop_map.get(p, p.upper()) for p in properties)


async def run(timeout=10.0):
    if client.GLOBAL_CLIENT is None or not client.GLOBAL_CLIENT.is_connected:
        print("[!] No hay un cliente global conectado. Conecta un dispositivo primero desde scan.")
        return

    ble_client = client.GLOBAL_CLIENT
    print(f"✅ Usando cliente global conectado a {getattr(ble_client, 'address', 'desconocido')}")

    try:
        await ble_client.get_services()
        services = list(ble_client.services)
        if not services:
            print("❌ No se encontraron servicios")
            return

        print(f"\n📋 {len(services)} servicios encontrados:\n")

        client.GATT_CACHE = {}

        # Servicios
        service_rows = []
        for svc in services:
            handle = getattr(svc, "handle", "?")
            uuid_full = svc.uuid
            uuid_short = get_short_uuid(uuid_full)
            name = resolve_uuid_name(uuid_full) or "Unknown Service"
            service_rows.append([f"0x{handle:04X}" if isinstance(handle, int) else handle,
                     uuid_short, name, uuid_full])

        print(tabulate(service_rows,
                       headers=["Handle", "UUID corto", "Nombre", "UUID completo"],
                       tablefmt="github"))

        
        for svc in services:
            if not svc.characteristics:
                continue

            svc_short = get_short_uuid(svc.uuid)
            svc_name = resolve_uuid_name(svc.uuid) or "Unknown Service"
            print(f"\n🔹 Características de {svc_name} ({svc_short}):\n")

            char_rows = []
            for ch in svc.characteristics:
                ch_handle = getattr(ch, "handle", "?")
                ch_uuid_full = ch.uuid
                ch_short = get_short_uuid(ch_uuid_full)
                ch_name = resolve_uuid_name(ch_uuid_full) or "Unknown Characteristic"
                props = format_properties(ch.properties)

                client.GATT_CACHE[ch_uuid_full.lower()] = ch
                client.GATT_CACHE[ch_short.lower()] = ch

                char_rows.append([f"0x{ch_handle:04X}" if isinstance(ch_handle, int) else ch_handle,
                ch_short, ch_name, props, ch_uuid_full])

            print(tabulate(char_rows,
                           headers=["Handle", "UUID corto", "Nombre", "Propiedades", "UUID completo"],
                           tablefmt="github"))

            for ch in svc.characteristics:
                if not ch.descriptors:
                    continue
                ch_title = resolve_uuid_name(ch.uuid) or get_short_uuid(ch.uuid)
                print(f"\n   📎 Descriptores de característica {ch_title} (Handle {getattr(ch, 'handle', '?')}):")
                desc_rows = []
                for desc in ch.descriptors:
                    d_handle = getattr(desc, "handle", "?")
                    d_uuid_full = desc.uuid
                    d_short = get_short_uuid(d_uuid_full)
                    d_name = resolve_uuid_name(d_uuid_full) or "Unknown Descriptor"
                    desc_rows.append([f"0x{d_handle:04X}" if isinstance(d_handle, int) else d_handle,
                  d_short, d_name, d_uuid_full])

                print(tabulate(desc_rows,
                               headers=["Handle", "UUID corto", "Nombre", "UUID completo"],
                               tablefmt="github"))

        print(f"\n💾 {len(client.GATT_CACHE)} características cacheadas en client.GATT_CACHE")

    except asyncio.TimeoutError:
        print("[!] Timeout: No se pudieron obtener los servicios")
    except Exception as e:
        print(f"[!] Error: {e}")


if __name__ == "__main__":
    asyncio.run(run(OPTIONS["timeout"]))
