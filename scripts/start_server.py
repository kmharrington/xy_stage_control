from xy_wing.server import XY_Server

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

