from bleak import BleakClient
from typing import Optional, Dict
from tabulate import tabulate

GLOBAL_CLIENT: Optional[BleakClient] = None
GATT_CACHE: Dict[str, object] = {}

BASE_SUFFIX = "-0000-1000-8000-00805f9b34fb"

def is_sig_uuid(u: str) -> bool:
    """Detecta si es un UUID estándar SIG de 16-bit"""
    u = u.lower()
    return u.startswith("0000") and u.endswith(BASE_SUFFIX)

def get_short_uuid(u: str) -> str:
    """Devuelve UUID corto 0xXXXX si es SIG, sino primeros 8 chars"""
    u = u.lower()
    if is_sig_uuid(u):
        return "0x" + u[4:8]
    return u[:8]

def status():
    """Muestra el estado del cliente global"""
    if GLOBAL_CLIENT and GLOBAL_CLIENT.is_connected:
        print(f"🔹 Global client {GLOBAL_CLIENT.address}")
    else:
        print("🔹 Not client connect")

def cache_characteristic(ch):
    """
    Guarda una característica en el cache global por UUID completo y corto
    """
    if not ch or not hasattr(ch, "uuid"):
        return

    uuid_full = ch.uuid.lower()
    uuid_short = get_short_uuid(uuid_full).lower()

    GATT_CACHE[uuid_full] = ch
    GATT_CACHE[uuid_short] = ch

def get_characteristic(uuid: str):
    """
    Recupera una característica del cache por UUID corto o completo
    """
    if not uuid:
        return None
    return GATT_CACHE.get(uuid.lower())

def clear_cache():
    """Limpia el cache de características"""
    GATT_CACHE.clear()

def show_cached_chars():
    """
    Muestra todas las características cacheadas en formato tabla
    """
    if not GATT_CACHE:
        print("📭 No hay características cacheadas todavía.")
        return

    rows = []
    seen = set()
    for ch in GATT_CACHE.values():
        uuid_full = ch.uuid.lower()
        if uuid_full in seen:
            continue
        seen.add(uuid_full)

        handle = getattr(ch, "handle", "?")
        uuid_short = get_short_uuid(uuid_full)
        props = getattr(ch, "properties", [])
        props_fmt = ", ".join(props).upper() if props else "-"
        rows.append([f"0x{handle:04x}" if isinstance(handle, int) else handle,
                     uuid_short, props_fmt, uuid_full])

    print(tabulate(rows,
                   headers=["Handle", "UUID corto", "Propiedades", "UUID completo"],
                   tablefmt="github"))
    print(f"\n💾 Total: {len(rows)} características cacheadas")
