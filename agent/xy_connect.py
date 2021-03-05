import socket
import json
import time

class XY_Stage:
    def __init__(self, ip_address, port, timeout=10):
        self.ip_address = ip_address
        self.port = port


        self.comm = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.comm.connect((HOST, PORT))
        self.comm.settimeout(timeout)

    def send(self, message):
        self.comm.sendall(bytes(json.dumps(message), 'utf-8'))
        try:
            data = self.comm.recv(1025)
            resp = json.loads(data)
            if 'error' in resp:
                raise Exception(resp['error'])
            return resp['resp']
        except socket.timeout:
            return None
        
    def build_text(self, func, prop=False, kwargs={}):
        if prop:
            resp = self.send({'property':func})
        else:
            resp = self.send({'function':func, 'kwargs':kwargs})
        return resp

    def init_stages(self):
        self.build_text('init', {})

    @property
    def limits(self):
        return xy_stage.build_text( 'limits', prop=True )
        
    def stop(self):
        self.build_text('stop', kwargs={})

    def move_x_cm( self, distance, velocity=None):
        self.build_text('move_x_cm', kwargs={'distance':distance, 
                                             'velocity':velocity})

    def move_y_cm( self, distance, velocity=None):
        self.build_text('move_y_cm', kwargs={'distance':distance, 
                                             'velocity':velocity})

class XY_Agent:
    def __init__(self):
        pass    

HOST = '192.168.10.15'
PORT = 3010

xy_stage = XY_Stage(HOST, PORT)
#xy_stage.send('Hello')
xy_stage.init_stages()
print( xy_stage.limits )
xy_stage.move_y_cm( -10, 0.5)
time.sleep(3)
xy_stage.stop()
