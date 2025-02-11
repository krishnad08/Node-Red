import subprocess
import re
import json

# File to store the USB port information
usb_port_file = "usb_port.json"

# Function to get the last FTDI port from dmesg
def get_ftdi_port():
    try:
        # Get the dmesg output and filter for FTDI messages
        dmesg_output = subprocess.check_output(['dmesg'], text=True).splitlines()
        ftdi_lines = [line for line in dmesg_output if "FTDI USB Serial Device converter now attached to" in line]

        if ftdi_lines:
            # Get the last FTDI occurrence
            last_ftdi_line = ftdi_lines[-1]
            match = re.search(r"attached to (\w+)", last_ftdi_line)
            if match:
                return f"/dev/{match.group(1)}"
        return None
    except Exception as e:
        print(f"Error retrieving FTDI port: {e}")
        return None

# Function to save the port to a JSON file
def save_port_to_file(port):
    try:
        data = {"usb_port": port}
        with open(usb_port_file, "w") as file:
            json.dump(data, file)
        print(f"Saved USB port to {usb_port_file}: {port}")
    except Exception as e:
        print(f"Error saving USB port to file: {e}")

# Main function to detect and save the correct FTDI USB port
def main():
    # Always detect the USB port dynamically
    usb_port = get_ftdi_port()
    if usb_port:
        save_port_to_file(usb_port)
    else:
        print("FTDI device not found. Please check the connection.")

if __name__ == "__main__":
    main()