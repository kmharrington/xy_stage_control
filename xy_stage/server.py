#!/user/bin/env python3

from . import XY_Stage
import socket
import json


class XY_Server(object):
    def __init__(self, host, port, xpin_list, ypin_list, steps_per_cm):
        
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((HOST, PORT))
        self.server.listen(1)
        
        self.xpins = xpin_list
        self.ypins = ypin_list
        self.steps_per_cm = steps_per_cm
        self.stages = None

    def work(self):
        while True:
            try:
                conn, addr = self.server.accept()
                with conn:
                    print('Connected by ', addr)
                    while True:
                        msg = conn.recv(1024)
                        if not msg:
                            break
                        resp = self.process(msg.decode('utf-8'))
                        conn.sendall(bytes(resp, 'utf-8'))
            except:
                self.server.close()
                raise

    def process(self, msg):
        msg = json.loads(msg)
        print(msg)
        try:
            if 'property' in msg:
                resp = {'resp': getattr(self.stages, msg['property'])}
            elif 'function' in msg:
                if msg['function'] == 'init':
                    resp = {'resp':self.init_stages()}
                else:
                    f = getattr(self.stages, msg['function'])
                    resp = {'resp': f(**msg['kwargs'])}
            if resp is None:
                resp = {'resp': None }
        except Exception as err:
            resp = {'error': err.args[0]}     
        print(resp)
        return json.dumps(resp)

    def init_stages(self):
        if self.stages is not None:
            return 'Stages already Initialized'
        self.stages = XY_Stage(self.xpins, self.ypins, self.steps_per_cm)
        return 'Stages Initialized'
        
if __name__ == '__main__':
    HOST = '192.168.10.15'
    PORT = 3010
    
    STEP_PER_CM = 1574.80316

    xpins = {
        'ena':2,
        'pul':4,
        'dir':3,
        'eot_ccw':[17,23],
        'eot_cw':[27,24],
    }
    ypins = {
        'ena':16,
        'pul':21,
        'dir':20,
        'eot_ccw':19,
        'eot_cw':26,
    }

    server = XY_Server(HOST, PORT, xpins, ypins, STEP_PER_CM)
    server.work()
