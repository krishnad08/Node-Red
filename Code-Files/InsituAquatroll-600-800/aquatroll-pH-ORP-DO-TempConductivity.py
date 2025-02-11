import struct
import json
import os
from pymodbus.client import ModbusSerialClient # type: ignore

usb_port_file = "usb_port.json"

# Function to load the USB port from the JSON file
def load_port_from_file():
    try:
        with open(usb_port_file, "r") as file:
            data = json.load(file)
            return data.get("usb_port")
    except FileNotFoundError:
        print(f"{usb_port_file} not found.")
        return None
    except Exception as e:
        print(f"Error loading USB port from file: {e}")
        return None

# Helper function to parse a set of 7 registers
def parse_register_data(registers):
    measured_value = struct.unpack('>f', struct.pack('>HH', registers[0], registers[1]))[0]
    data_quality_id = registers[2]
    units_id = registers[3]
    parameter_id = registers[4]
    sentinel_value = struct.unpack('>f', struct.pack('>HH', registers[5], registers[6]))[0]

    return {
        "Measured Value": measured_value,
        "Data Quality ID": data_quality_id,
        "Units ID": units_id,
        "Parameter ID": parameter_id,
        "Sentinel Value": sentinel_value
    }

# Helper function to convert JSON data into a byte array
def convert_to_byte_array(data, max_bytes=170):
    byte_arrays = []

    # Serialize Device ID and Serial Number as uint16 and uint32 respectively
    device_id = struct.pack('>H', data["Device ID"])  # 2 bytes
    serial_number = struct.pack('>I', data["Serial Number"])  # 4 bytes

    # Starting data for each array (Device ID + Serial Number)
    start_data = device_id + serial_number  # 6 bytes total
    current_array = bytearray(start_data)

    # Iterate through the remaining data
    for register, values in data.items():
        if register in ["Device ID", "Serial Number"]:
            continue  # Skip the already processed Device ID and Serial Number

        # Serialize the 7 registers data (each 2 bytes)
        measured_value = struct.pack('>f', values["Measured Value"])  # 4 bytes
        data_quality_id = struct.pack('>H', values["Data Quality ID"])  # 2 bytes
        units_id = struct.pack('>H', values["Units ID"])  # 2 bytes
        parameter_id = struct.pack('>H', values["Parameter ID"])  # 2 bytes
        sentinel_value = struct.pack('>f', values["Sentinel Value"])  # 4 bytes

        register_data = measured_value + data_quality_id + units_id + parameter_id + sentinel_value  # 14 bytes

        # Check if adding this register would exceed the max_bytes limit
        if len(current_array) + len(register_data) > max_bytes:
            # If it exceeds, finalize the current array and start a new one
            byte_arrays.append(current_array)
            current_array = bytearray(start_data)  # Start new array with Device ID and Serial Number

        current_array.extend(register_data)

    # Append any remaining data as the last array
    if current_array:
        byte_arrays.append(current_array)

    return byte_arrays

usb_port = load_port_from_file()
if not usb_port:
    print("USB port not available. Exiting.")
    exit()

# Configure the Modbus RTU client
client = ModbusSerialClient(
    port=usb_port,    # Serial port
    baudrate=19200,         # Baud rate
    bytesize=8,             # Data bits
    parity='E',             # Even parity
    stopbits=1,             # Stop bits
    timeout=1.1             # Timeout in seconds
)

# Modbus settings
start_registers = [9000, 5450, 5457, 5464, 5667, 5506, 5513, 5520, 5527, 5541, 5562, 5569, 5576, 5583, 5590]
register_count = 7
slave_id = 1
max_retries = 5  # Maximum retries per register
output_dir = "/home/ncdio/aquatroll600"  # Directory to save files
os.makedirs(output_dir, exist_ok=True)

# Initialize data structure
all_registers_data = {}

# Attempt to connect to Modbus RTU server
if client.connect():
    print("Connected to Modbus RTU server successfully.")

    try:
        # Read registers
        for start_register in start_registers:
            retry_count = 0
            success = False

            while retry_count < max_retries:
                try:
                    result = client.read_holding_registers(start_register, register_count, slave=slave_id)

                    if not result.isError():
                        print(f"Raw Register values for start register {start_register}: {result.registers}")

                        if start_register == 9000:
                            # Extract Device ID and Serial Number from register 9000
                            device_id = result.registers[0]  # First 16 bits
                            serial_number = struct.unpack('>I', struct.pack('>HH', result.registers[1], result.registers[2]))[0]  # Next 32 bits
                            all_registers_data["Device ID"] = device_id
                            all_registers_data["Serial Number"] = serial_number
                        else:
                            parsed_data = parse_register_data(result.registers)
                            all_registers_data[start_register] = parsed_data

                        success = True
                        break
                    else:
                        print(f"Error reading Modbus registers starting at {start_register}. Retrying...")
                except Exception as e:
                    print(f"Exception while reading Modbus registers starting at {start_register}: {e}")

                retry_count += 1

            if not success:
                print(f"Failed to read Modbus registers starting at {start_register} after {max_retries} retries.")
                all_registers_data[start_register] = {"Error": "Failed to read after retries"}

        # Convert JSON data to byte arrays
        byte_arrays = convert_to_byte_array(all_registers_data)

        # Save byte arrays to files
        for i, byte_array in enumerate(byte_arrays):
            identifier = struct.pack('B', i + 1)  # Identifier (0x01, 0x02, etc.)
            byte_array_with_id = identifier + byte_array
            file_path = os.path.join(output_dir, f"modbus_data_part_{i + 1}.bin")
            with open(file_path, "wb") as file:
                file.write(byte_array_with_id)
            print(f"Byte Array {i + 1} saved to {file_path} with identifier {i + 1}")

    except Exception as e:
        print(f"An error occurred: {e}")

    # Close the client connection
    client.close()
else:
    print("Failed to connect to Modbus RTU server.")