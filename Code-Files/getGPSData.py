import os
import time
import json

def read_nmea_sentence(input_file, timeout=30):
    start_time = time.time()
    gpgsv_received = False
    gpgga_received = False
    gpgsv_sentence = None
    gpgga_sentence = None
    sentence = bytearray()
    #print("Started capturing GPS sentences")
    while True:
        if time.time() - start_time > timeout:
            return None

        byte = input_file.read(1)
        if byte == b'\r':  # Carriage return encountered
            sentence_str = sentence.decode("utf-8").strip()
            if sentence_str.startswith('$GPGSV'):
                gpgsv_received = True
                gpgsv_sentence = sentence_str
                #print(gpgsv_sentence)
            elif sentence_str.startswith('$GPGGA'):
                gpgga_received = True
                gpgga_sentence = sentence_str
                #print(gpgga_sentence)
            sentence = bytearray()
            if gpgsv_received and gpgga_received:
                #print(gpgsv_sentence)
                #print(gpgga_sentence)
                return gpgsv_sentence, gpgga_sentence
        else:
            sentence.extend(byte)

def extract_gpgga_data(sentence):
    if sentence.startswith('$GPGGA'):
        data = sentence.split(',')
        time_str = data[1][:6]  # Extract only the time part (HHMMSS)
        latitude = float(data[2][:2]) + float(data[2][2:]) / 60.0
        if data[3].upper() == 'S':
            latitude *= -1
        longitude = float(data[4][:3]) + float(data[4][3:]) / 60.0
        if data[5].upper() == 'W':
            longitude *= -1
        satellites_used = int(data[7])
        satellites_in_view = int(data[6])
        return {'time': time_str, 'latitude': latitude, 'longitude': longitude, 'satellites_used': satellites_used, 'satellites_in_view': satellites_in_view}
    else:
        return None

def extract_gpgsv_data(sentence):
    if sentence.startswith('$GPGSV'):
        data = sentence.split(',')
        satellites = int(data[3])
        #print(satellites)
        return satellites
    else:
        return None

def main():
    output_json_path = '/home/ncdio/gpsData/gps.json'

    if not os.path.exists(output_json_path):
        open(output_json_path, 'w').close()

    with open('/dev/ttyGPS', 'rb') as input_file:
        # Open the output file
        gpgsv_sentence, gpgga_sentence = read_nmea_sentence(input_file)
        if gpgsv_sentence is None or gpgga_sentence is None:
            print("Error: Timeout occurred or incomplete data.")
            return
        gpgga_data = extract_gpgga_data(gpgga_sentence)
        gpgsv_data = extract_gpgsv_data(gpgsv_sentence)

        if gpgga_data and gpgsv_data:
            data = {
                'time': gpgga_data['time'],
                'latitude': gpgga_data['latitude'],
                'longitude': gpgga_data['longitude'],
                'satellites_used': gpgga_data['satellites_used'],
                'satellites_in_view': gpgga_data['satellites_in_view'],
                'satellites_in_view_gpgsv': gpgsv_data,
                'gpgga_sentence': gpgga_sentence
            }
            with open(output_json_path, 'w') as output_json_file:
                json.dump(data, output_json_file, indent=4)
if __name__ == "__main__":
    main()