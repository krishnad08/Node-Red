import json
import os
from pymodbus.client import ModbusSerialClient # type: ignore
from pymodbus.exceptions import ModbusIOException # type: ignore

import time

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
USB_MODBUS_PORT_FILE = os.path.join(os.path.dirname(__file__), 'usb_modbus_port.json')

# Serial Modbus settings
BAUD_RATE   = 19200
PARITY      = 'E'  # 'N', 'E', or 'O'
STOP_BITS   = 1
BYTE_SIZE   = 8
TIMEOUT     = 1

SLAVE_ID          = 1        # Adjust if your device uses a different slave ID
RESET_REGISTER    = 0x0007   # Holding register for precipitation reset
RESET_VALUE       = 0x3247   # Value that triggers precipitation counter reset

def get_modbus_port():
    """
    Fetch the Modbus port from the usb_modbus_port.json file.
    Example file:
      {
        "usb_port": "/dev/ttyUSB0"
      }
    """
    try:
        with open(USB_MODBUS_PORT_FILE, 'r') as port_file:
            port_data = json.load(port_file)
            return port_data.get("usb_port")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading Modbus port file: {e}")
        return None

def main():
    port = get_modbus_port()
    if not port:
        print("No Modbus port found. Exiting.")
        return

    # Initialize the Modbus serial client
    client = ModbusSerialClient(
        port=port,
        baudrate=BAUD_RATE,
        parity=PARITY,
        stopbits=STOP_BITS,
        bytesize=BYTE_SIZE,
        timeout=TIMEOUT
    )

    # Attempt to connect
    if not client.connect():
        print(f"Failed to connect on {port}")
        return

    print(f"Connected to device on {port}")

    try:
        # Write the reset value to holding register 0x0007
        print(f"Writing 0x{RESET_VALUE:04X} to holding register 0x{RESET_REGISTER:04X} ...")
        response = client.write_register(
            address=RESET_REGISTER,
            value=RESET_VALUE,
            slave=SLAVE_ID
        )

        # Check for errors or confirm success
        if response.isError():
            print("Error during write operation:", response)
        else:
            print("Precipitation counter reset command sent successfully.")

    except ModbusIOException as err:
        print(f"Modbus IOException: {err}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        client.close()
        print("Modbus client disconnected.")

if __name__ == "__main__":
    main()