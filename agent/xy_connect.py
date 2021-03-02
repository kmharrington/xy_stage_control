import socket



class XY_Stage:
    def __init__(self, ip_address, port, timeout=10):
        self.ip_address = ip_address
        self.port = port


        self.comm = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.comm.connect((HOST, PORT))
        self.comm.settimeout(timeout)

    def send(self, message):
        self.comm.sendall(bytes(message, 'utf-8'))
        data = self.comm.recv(1024)
        print('Received ', data)

    def init_stages(self):
        self.send('init')


class XY_Agent:
    def __init__(self):
        pass    

HOST = '192.168.10.15'
PORT = 3010

xy_stage = XY_Stage(HOST, PORT)
xy_stage.send('Hello')
xy_stage.init_stages()

