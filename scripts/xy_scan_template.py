import numpy as np
import time
import datetime as dt
import scipy.interpolate as spint
import argparse
'''
import ocs
from ocs import matched_client
#import gevent.monkey
#gevent.monkey.patch_all(aggressive=False, thread=False)
from ocs.ocs_widgets import TaskWidget, ProcessWidget
from twisted.python import log
from twisted.logger import formatEvent, FileLogObserver
'''

from xy_agent.xy_scan import XY_Scan

def before():
    """Function to call before the scan"""
    time.sleep(0.5)

def during():
    """Function to call at each position"""
    #out = scan.xy_stage.acq.status().session.get('data')
    out = scan.xy_stage.position
    print( f"Position: {out[0]}, {out[1]}")
    time.sleep(2)

def after():
    """Function to call at the end of the scan"""
    time.sleep(2)

scan = XY_Scan(with_ocs=False)

scan.setup_scan(total_distance_x = 10,
                total_distance_y = 10,
                N_pts_x = 3,
                N_pts_y = 3,
                x_vel = 1,
                y_vel = 1,
                scan_dir='x',
                step_raster=True
                )

scan.set_before_scan_function(before)
scan.set_during_scan_function(during)
scan.set_after_scan_function(after)

scan.execute()

