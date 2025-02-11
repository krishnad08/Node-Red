import time
import json
import os
from pymodbus.client import ModbusSerialClient # type: ignore
from pymodbus.exceptions import ModbusIOException # type: ignore

# -----------------------------------------------------------------------------
# Serial Configuration
# -----------------------------------------------------------------------------
SERIAL_PORT = None  # Port will be dynamically fetched from usb_modbus_port.json
BAUD_RATE   = 19200
PARITY      = 'E'
STOP_BITS   = 1
BYTE_SIZE   = 8
TIMEOUT     = 1
SLAVE_ID    = 1

# -----------------------------------------------------------------------------
# File Paths
# -----------------------------------------------------------------------------
OUTPUT_FOLDER = '/home/ncdio/weather'
OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, 'weather_data.json')
USB_MODBUS_PORT_FILE = os.path.join(os.path.dirname(__file__), 'usb_modbus_port.json')

# -----------------------------------------------------------------------------
# Input Register Labels & Chunks (Existing)
# -----------------------------------------------------------------------------
REGISTER_LABELS = {
    0x000A: "relative_humidity_instant",
    0x000B: "relative_humidity_min",
    0x000C: "relative_humidity_max",
    0x000D: "relative_humidity_avg",
    0x000E: "air_pressure_instant",
    0x000F: "air_pressure_min",
    0x0010: "air_pressure_max",
    0x0011: "air_pressure_avg",
    0x0012: "wind_direction_instant",
    0x0013: "wind_direction_min",
    0x0014: "wind_direction_max",
    0x0015: "wind_direction_avg",
    0x001A: "wind_quality_instant",
    0x001B: "global_radiation_instant",
    0x001C: "global_radiation_min",
    0x001D: "global_radiation_max",
    0x001E: "global_radiation_avg",
    0x0033: "air_temperature_instant",
    0x0034: "air_temperature_min",
    0x0035: "air_temperature_max",
    0x0036: "air_temperature_avg",
    0x0037: "dew_point_instant",
    0x0038: "dew_point_min",
    0x0039: "dew_point_max",
    0x003A: "dew_point_avg",
    0x003B: "wind_chill_instant",
    0x003D: "heater_temperature_instant",
    0x003E: "wind_speed_instant",
    0x003F: "wind_speed_min",
    0x0040: "wind_speed_max",
    0x0041: "wind_speed_avg",
    0x0043: "wind_speed_raw",
    0x0044: "precipitation_accumulation_absolute",
    0x0045: "precipitation_accumulation_differential",
    0x0046: "precipitation_intensity",
    0x0047: "absolute_humidity_instant",
    0x0048: "absolute_humidity_min",
    0x0049: "absolute_humidity_max",
    0x004A: "absolute_humidity_avg",
    0x004B: "mixing_ratio_instant",
    0x004C: "mixing_ratio_min",
    0x004D: "mixing_ratio_max",
    0x004E: "mixing_ratio_avg",
    0x004F: "absolute_air_pressure_instant",
    0x0050: "absolute_air_pressure_min",
    0x0051: "absolute_air_pressure_max",
    0x0052: "absolute_air_pressure_avg",
    0x0053: "wind_speed_kmh_instant",
    0x0054: "wind_speed_kmh_min",
    0x0055: "wind_speed_kmh_max",
    0x0056: "wind_speed_kmh_avg",
    0x0058: "wind_speed_knots_instant",
    0x0059: "wind_speed_knots_min",
    0x005A: "wind_speed_knots_max",
    0x005B: "wind_speed_knots_avg",
    0x005D: "wind_speed_kmh_raw",
    0x005E: "wind_speed_knots_raw",
    0x0062: "wet_bulb_temperature_c_instant",
    0x0063: "wet_bulb_temperature_f_instant",
    0x0064: "specific_enthalpy_instant",
    0x0065: "air_density_instant",
    0x006B: "external_temperature_c_instant",
    0x006C: "external_temperature_f_instant",
    0x006D: "wind_measurement_quality"
}

CHUNKS = [
    (0x000A, 0x0015),
    (0x001A, 0x001E),
    (0x0033, 0x0041),
    (0x0043, 0x0052),
    (0x0053, 0x006D)
]

# -----------------------------------------------------------------------------
# Scaling for Input Registers
# -----------------------------------------------------------------------------
SCALING_FACTORS_INPUT = {
    0x000A: 10,
    0x000B: 10,
    0x000C: 10,
    0x000D: 10,
    0x000E: 10,
    0x000F: 10,
    0x0010: 10,
    0x0011: 10,
    0x0012: 10,
    0x0013: 10,
    0x0014: 10,
    0x0015: 10,
    0x001A: 1,
    0x001B: 10,
    0x001C: 10,
    0x001D: 10,
    0x001E: 10,
    0x0033: 10,
    0x0034: 10,
    0x0035: 10,
    0x0036: 10,
    0x0037: 10,
    0x0038: 10,
    0x0039: 10,
    0x003A: 10,
    0x003B: 10,
    0x003D: 10,
    0x003E: 10,
    0x003F: 10,
    0x0040: 10,
    0x0041: 10,
    0x0043: 10,
    0x0044: 1000,
    0x0045: 10000,
    0x0046: 10000,
    0x0047: 10,
    0x0048: 10,
    0x0049: 10,
    0x004A: 10,
    0x004B: 10,
    0x004C: 10,
    0x004D: 10,
    0x004E: 10,
    0x004F: 10,
    0x0050: 10,
    0x0051: 10,
    0x0052: 10,
    0x0053: 10,
    0x0054: 10,
    0x0055: 10,
    0x0056: 10,
    0x0058: 10,
    0x0059: 10,
    0x005A: 10,
    0x005B: 10,
    0x005D: 10,
    0x005E: 10,
    0x0062: 10,
    0x0063: 10,
    0x0064: 10,
    0x0065: 1000,
    0x006B: 10,
    0x006C: 10,
    0x006D: 1
}

# -----------------------------------------------------------------------------
# Holding Registers & Scaling
# -----------------------------------------------------------------------------
HOLDING_REGISTER_NAMES = {
    0x0000: "altitude",
    0x0001: "wind_direction_deviation_angle",
    0x0002: "averaging_interval_t_rh_x_a_tdw",
    0x0003: "averaging_interval_air_pressure",
    0x0004: "averaging_interval_wind",
    0x0005: "averaging_interval_solar_radiation",
    0x0006: "heating_control",
    0x0007: "reset_rain_accumulation",
    0x0008: "reset_device",
    0x0009: "modbus_address",
    0x000A: "cli_mode"
}

SCALING_FACTORS_HOLDING = {
    0x0000: 1,
    0x0001: 10,
    0x0002: 1,
    0x0003: 1,
    0x0004: 1,
    0x0005: 1,
    0x0006: 1,
    0x0007: 1,
    0x0008: 1,
    0x0009: 1,
    0x000A: 1
}

# Example chunk for holding registers (adjust addresses to match your device)
# Reads 0x0000 -> 0x000A
HOLDING_CHUNK = (0x0000, 0x000A)

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def clear_buffer(client):
    """Attempt to clear the Modbus client's receive buffer."""
    try:
        client.socket.reset_input_buffer()
        print("Receive buffer cleared.")
    except AttributeError:
        pass  # Not all backends support this

def get_modbus_port():
    """Fetch the Modbus port from the usb_modbus_port.json file."""
    try:
        with open(USB_MODBUS_PORT_FILE, 'r') as port_file:
            port_data = json.load(port_file)
            return port_data.get("usb_port")  # or your matching key name
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading Modbus port file: {e}")
        return None

def read_input_chunk(client, start_addr, end_addr, slave, retries=3):
    """Read a chunk of **input** registers from start_addr to end_addr (inclusive)."""
    count = (end_addr - start_addr) + 1
    for attempt in range(retries):
        try:
            clear_buffer(client)
            response = client.read_input_registers(
                address=start_addr,
                count=count,
                slave=slave
            )
            if response and not response.isError():
                return response.registers
            else:
                print(f"[Attempt {attempt+1}] Error reading input 0x{start_addr:04X} to 0x{end_addr:04X}")
        except ModbusIOException as e:
            print(f"[Attempt {attempt+1}] ModbusIOException: {e}")
        time.sleep(2)
    return None

def read_holding_chunk(client, start_addr, end_addr, slave, retries=3):
    """Read a chunk of **holding** registers from start_addr to end_addr (inclusive)."""
    count = (end_addr - start_addr) + 1
    for attempt in range(retries):
        try:
            clear_buffer(client)
            response = client.read_holding_registers(
                address=start_addr,
                count=count,
                slave=slave
            )
            if response and not response.isError():
                return response.registers
            else:
                print(f"[Attempt {attempt+1}] Error reading holding 0x{start_addr:04X} to 0x{end_addr:04X}")
        except ModbusIOException as e:
            print(f"[Attempt {attempt+1}] ModbusIOException: {e}")
        time.sleep(2)
    return None

def process_holding_register_data(address, value):
    """Scale and label a single holding register."""
    scaling_factor = SCALING_FACTORS_HOLDING.get(address, 1)
    scaled_value = value / scaling_factor
    variable_name = HOLDING_REGISTER_NAMES.get(address, None)
    if variable_name:
        return {variable_name: scaled_value}
    else:
        # Not in dictionary
        return {f"holding_{hex(address)}": scaled_value}

# -----------------------------------------------------------------------------
# Main Logic
# -----------------------------------------------------------------------------
def main():
    global SERIAL_PORT
    SERIAL_PORT = get_modbus_port()
    if not SERIAL_PORT:
        print("No Modbus port found. Exiting.")
        return

    client = ModbusSerialClient(
        port=SERIAL_PORT,
        baudrate=BAUD_RATE,
        parity=PARITY,
        stopbits=STOP_BITS,
        bytesize=BYTE_SIZE,
        timeout=TIMEOUT
    )

    if not client.connect():
        print(f"Failed to connect to device on {SERIAL_PORT}")
        return

    print(f"Connected to device on {SERIAL_PORT}")

    try:
        # -------------------------------------------------------------------------------------
        # 1) Read & Scale Input Registers
        # -------------------------------------------------------------------------------------
        scaled_data = {}

        for (start_addr, end_addr) in CHUNKS:
            chunk_values = read_input_chunk(client, start_addr, end_addr, SLAVE_ID)
            if chunk_values is None:
                print(f"Failed to read input chunk 0x{start_addr:04X} to 0x{end_addr:04X}")
                continue

            for i, raw_val in enumerate(chunk_values):
                current_addr = start_addr + i
                if current_addr in REGISTER_LABELS:
                    label = REGISTER_LABELS[current_addr]
                    scaling_factor = SCALING_FACTORS_INPUT.get(current_addr, 1)
                    scaled_data[label] = raw_val / scaling_factor

        # -------------------------------------------------------------------------------------
        # 2) Read & Scale Holding Registers
        # -------------------------------------------------------------------------------------
        scaled_holding_data = {}

        # Example: reading from 0x0000 to 0x000A
        hold_start, hold_end = HOLDING_CHUNK
        holding_values = read_holding_chunk(client, hold_start, hold_end, SLAVE_ID)
        if holding_values is not None:
            for i, raw_val in enumerate(holding_values):
                addr = hold_start + i
                parsed = process_holding_register_data(addr, raw_val)  # parse & scale
                scaled_holding_data.update(parsed)
        else:
            print(f"Failed to read holding chunk 0x{hold_start:04X} to 0x{hold_end:04X}")

        # -------------------------------------------------------------------------------------
        # 3) Combine & Write Results
        # -------------------------------------------------------------------------------------
        # If you want a single JSON with both input & holding data,
        # you can nest them or just merge them at top level. Example:
        combined_data = {
            "input_registers": scaled_data,
            "holding_registers": scaled_holding_data
        }

        # Write JSON
        with open(OUTPUT_FILE, 'w') as json_file:
            json_file.seek(0)
            json_file.truncate()
            json.dump(combined_data, json_file, indent=4)

        print("Weather data updated with input & holding registers.")

    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        client.close()
        print("Modbus client disconnected.")


if __name__ == "__main__":
    main()