import os
import socket

import time

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as int_con:
    int_con.bind(("127.0.0.1", 8888))
    int_con.listen(1)

    client,addr = int_con.accept()

    #breakpoint()

    with client:
        data = client.recv(1024)
        while data != b'':
            print(data)
            if data == b'reboot':
                print('System Reboot')
                try:
                    os.system('systemctl reboot')
                except Exception as e:
                    print("Exception", e)
                data = client.recv(1024)
            elif data:
                try:
                    os.system('service docker restart')
                    os.system('systemctl daemon-reload')
                except Exception as e:
                    print("Exception", e)
                data = client.recv(1024)