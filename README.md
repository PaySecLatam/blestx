# BLE Framework

Este repositorio contiene un framework de interacción con dispositivos **BLE**, diseñado específicamente para **el CTF mPOS** en los retos de La Meche de los payments.

El objetivo del framework es facilitar la exploración, lectura, escritura y pruebas de seguridad en entornos controlados de laboratorio.

## Funcionalidades principales

- Escanear dispositivos BLE cercanos.
- Explorar servicios, características y descriptores GATT.
- Leer y escribir características GATT.
- Suscribirse a notificaciones de características.

## Módulos incluidos

| Módulo                   | Descripción |
|---------------------------|-------------|
| **GATT Characteristics Discover**        | Descubre características de un dispositivo BLE. |
| **GATT Read**             | Lee el valor de características específicas. |
| **GATT Write**            | Escribe datos en características seleccionadas. |
| **GATT Notify**           | Recibe notificaciones o indicaciones en tiempo real. |
| **Ble Scan**    | Identifica dispositivos ble cercanos |

## Uso del framework

1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Ejecutar el shell principal:
   ```bash
   python blestx.py
   ```

2. Listar módulos disponibles:
   ```bash
   modules
   ```

3. Cargar un módulo:
   ```bash
   load discover.ble_scan
   ```

4. Ver información del módulo:
   ```bash
   info
   ```

5. Ver opciones del módulo:
   ```bash
   options
   ```

6. Ejecutar el módulo:
   ```bash
   run
   ```

## Testeado con:

- Python 3.8.10
- Windows 11
- bleak>=0.22.0
- pyreadline3