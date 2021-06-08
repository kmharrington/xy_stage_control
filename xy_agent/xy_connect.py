import socket
import json
import time

class XY_Stage:
    def __init__(self, ip_address, port, timeout=10):
        self.ip_address = ip_address
        self.port = port


        self.comm = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.comm.connect((ip_address, port))
        self.comm.settimeout(timeout)

    def send(self, message):
        try:
            msg = bytes(json.dumps(message), 'utf-8')
        except:
            msg = json.dumps(message)
        self.comm.sendall(msg)
        try:
            data = self.comm.recv(1025)
            resp = json.loads(data)
            if 'error' in resp:
                raise Exception(resp['error'])
            return resp['resp']
        except socket.timeout:
            return None

    def close(self):
        self.comm.close()

    def wait_for_response(self):
        while True:
            try:
                data = self.comm.recv(1025)
                resp = json.loads(data)
                if 'error' in resp:
                    raise Exception(resp['error'])
                return resp['resp']
            except socket.timeout:
                #print('still waiting')
                continue

    def build_text(self, func, prop=False, kwargs={}):
        if prop:
            resp = self.send({'property':func})
        else:
            resp = self.send({'function':func, 'kwargs':kwargs})
        return resp

    def init_stages(self):
        self.build_text('init', kwargs={})

    @property
    def limits(self):
        return self.build_text( 'limits', prop=True )

    @property
    def position(self):
        return self.build_text( 'get_position', prop=False)
    
    @position.setter
    def position(self, value):
        if len(value) != 2:
            raise ValueError("Must supply position for x and y")
        return self.build_text( 'set_position', 
                                kwargs={'value': value})
    
    def wait(self):
        resp = self.build_text( 'wait', kwargs={})    
        if resp is None:
            resp = self.wait_for_response()
        return resp
    
    @property
    def moving(self):
        return self.build_text('moving', prop=True)
   
    def is_enabled(self):    
        return self.build_text('is_enabled', kwargs={})
    
    def enable(self):
        self.build_text('enable', kwargs={})
 
    def disable(self):
        self.build_text('disable', kwargs={})
    
    def stop(self):
        self.build_text('stop', kwargs={})

    def move_x_cm( self, distance, velocity=None):
        self.build_text('move_x_cm', kwargs={'distance':distance, 
                                             'velocity':velocity})

    def move_y_cm( self, distance, velocity=None):
        self.build_text('move_y_cm', kwargs={'distance':distance, 
                                             'velocity':velocity})
    @classmethod
    def latrt_xy_stage(cls):
        HOST = '192.168.10.15'
        PORT = 3010

        xy_stage = cls(HOST, PORT)
        xy_stage.init_stages()
        return xy_stage        


#class XY_Agent:
#    def __init__(self):
#        pass    
'''
if __name__ == '__main__':
    #xy_stage.send('Hello')

    #print( xy_stage.limits )
    #xy_stage.move_y_cm( -10, 0.5)
    #time.sleep(3)
    #xy_stage.stop()
'''
