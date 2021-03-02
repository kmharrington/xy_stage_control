from xy_stage import XY_stage

import socket

HOST = '192.168.10.15'
PORT = 3010

xy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
xy_server.bin((HOST, PORT))
xy_server.listen()

conn, addr = s.accept()
with conn:
    print('Connected by ', addr)
    while True:
        data = conn.recv(1024)
        if not data:
            break
        conn.sendall(data)
