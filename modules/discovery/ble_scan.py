from bleak import BleakScanner, BleakClient
import asyncio
import time
from core import client
from core import vendors

INFO = {
    "name": "Bluetooth Scanner",
    "author": "Stux",
    "description": "Escanea dispositivos BLE cercanos para enumerar su señal, mac y crear una conexión global con el dispositivo.",
    "options": {
        "timeout": "Tiempo de escaneo en segundos (default=10)",
        "filter": "Filtro opcional por nombre/dispositivo"
    }
}


OPTIONS = {
    "timeout": 10.0,
    "scan_interval": 2.0,
    "max_retries": 3
}

async def run(timeout=10.0, scan_interval=2.0, max_retries=3):
    """Escanea dispositivos BLE y permite conexión a un cliente global"""
    client.status()
    print(f"🔍 Buscando dispositivos BLE durante {timeout} segundos...\n")
    try:
        vendors.load()
    except Exception as e:
        print(f"[!] No se pudo cargar vendors: {e}")

    all_devices = {}
    start_time = time.time()

    for attempt in range(max_retries):
        print(f"Intento de escaneo {attempt + 1}/{max_retries}...")
        try:
            devices = await BleakScanner.discover(
                timeout=scan_interval,
                return_adv=True,
                scanning_mode="active"
            )
            for device, adv in devices.values():
                if device.address not in all_devices:
                    all_devices[device.address] = (device, adv)
            if time.time() - start_time >= timeout:
                break
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"[!] Error en intento {attempt + 1}: {e}")
            continue

    if not all_devices:
        print("[!] No se encontraron dispositivos")
        return

    table_data = []
    for addr, (device, adv) in all_devices.items():
        rssi = adv.rssi
        name = device.name or "unknown"
        addr_type = getattr(device, "address_type", "unknown")
        vendor = vendors.find(addr) or "unknown"
        table_data.append({
            "RSSI": rssi,
            "Addr": addr,
            "Vendor": vendor,
            "Name": name,
            "AddrType": addr_type
        })

    table_data.sort(key=lambda x: x["RSSI"], reverse=True)

    headers = ["No", "RSSI", "Addr", "Vendor", "Name", "AddrType"]
    col_widths = {header: len(header) for header in headers}
    for i, row in enumerate(table_data, start=1):
        row["No"] = str(i)
        for header in headers:
            col_widths[header] = max(col_widths[header], len(str(row.get(header, ""))))

    separator = "+" + "+".join("-"*(col_widths[h]+2) for h in headers) + "+"
    print(separator)
    print("|" + "|".join(f" {h.ljust(col_widths[h])} " for h in headers) + "|")
    print(separator)
    for row in table_data:
        print("|" + "|".join(f" {str(row.get(h,'')).ljust(col_widths[h])} " for h in headers) + "|")
    print(separator)
    print(f"\nEncontrados {len(table_data)} dispositivos en {time.time() - start_time:.1f} segundos.")

    choice = input("\nSelecciona un dispositivo para conectar (número, enter para omitir): ")
    if choice.strip().isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(table_data):
            mac_to_connect = table_data[idx]["Addr"]
            print(f"\n🔗 Conectando a {mac_to_connect}...")
            try:
                client.GLOBAL_CLIENT = BleakClient(mac_to_connect, timeout=OPTIONS["timeout"])
                await client.GLOBAL_CLIENT.connect()
                if client.GLOBAL_CLIENT.is_connected:
                    print(f"✅ Conectado y guardado en cliente global: {mac_to_connect}")
                else:
                    print("[!] No se pudo conectar al dispositivo")
                    client.GLOBAL_CLIENT = None
            except Exception as e:
                print(f"[!] Error conectando: {e}")
                client.GLOBAL_CLIENT = None
        else:
            print("[!] Selección inválida")
    else:
        print("⏹️ Omitido, no se conecta ningún dispositivo")

if __name__ == "__main__":
    asyncio.run(run(OPTIONS["timeout"]))
