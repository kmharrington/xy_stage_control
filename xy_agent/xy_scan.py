import numpy as np
import time
import datetime as dt
import scipy.interpolate as spint
import argparse

try:
    import ocs
    from ocs import matched_client
    from ocs.ocs_widgets import TaskWidget, ProcessWidget
    from twisted.python import log
    from twisted.logger import formatEvent, FileLogObserver
except ImportError:
    import xy_agent.xy_connect as connect
    WITH_OCS = False
else:
    WITH_OCS = True

if WITH_OCS:
    try:
        import xy_agent.xy_connect as connect
    except ImportError:
        pass

class XY_Scan:
    """Class for defining scan patterns with the XY Stages. There are several
        types of scans currently implemented.

        the setup_scan option has N_pts in each direction and stops at 
        each point to run a function. You can chose to primarily scan in 
        the x or y direction (aka, which on is on the outside of the for loop).
        If step_raster is true, the scan will raster back and forth instead
        of reseting to the other side.

        the setup_raster_yscan option has N_pts in the y direction and 
        continuously scans in the x direction.
        
      """
    def __init__(self, with_ocs=WITH_OCS ):
        """Connects to the Agent
        """
        self.ocs = with_ocs
        if self.ocs:
            self.xy_stage = matched_client.MatchedClient('XYWing', args=[])
        else:
            self.xy_stage = connect.XY_Stage.latrt_xy_stage()

        self.before_function = None
        self.during_function = None
        self.after_function = None
        self.is_setup = False
        self.step_raster = False
        self.is_raster_setup = False

    def setup_scan(self, total_distance_x, total_distance_y,
                    N_pts_x, N_pts_y, x_vel=0.5, y_vel=0.5, 
                    scan_dir='x', step_raster=False, x_vel_reset=None, 
                    y_vel_reset=None):
        """ Accepts the scan parameters can calculates the necessary moves
    
        Arguments
        -----------
        total_distance_x : float in cm
            scan will be from -total_disance_x/2 to + total_distance_x/2
        total_distance_y : float in cm
            scan will be from -total_disance_y/2 to + total_distance_y/2
        N_pts_x : int (must be odd)
        N_pts_y : int (must be odd)
        x_vel : float (speed to step in cm / s)
        y_vel : float (speed to step in cm / s)
        scan_dir : str ('x' or 'y') axis to move the most often in the scan
        step_raster : bool (choose if we want to raster or totally reset)
        x_vel_reset : float (speed for larger moves in cm/s)
        y_vel_reset : float (speed for larger moves in cm/s)
        """
        assert (scan_dir == 'x' or scan_dir == 'y')
        self.scan_dir = scan_dir
        self.N_pts_x = N_pts_x
        self.N_pts_y = N_pts_y
        self.x_vel = x_vel
        self.y_vel = y_vel
        if x_vel_reset is None:
            self.x_vel_reset = x_vel
        else:
            self.x_vel_reset = x_vel_reset
        
        if y_vel_reset is None:
            self.y_vel_reset = y_vel
        else:
            self.y_vel_reset = y_vel_reset
        

        if self.N_pts_x > 1:
            self.x_step = total_distance_x/(self.N_pts_x-1) #cm
        else:
            self.x_step = 0

        if self.N_pts_y > 1:
            self.y_step = total_distance_y/(self.N_pts_y-1) #cm
        else:
            self.y_step = 0

        self.total_x_move = self.x_step*(self.N_pts_x-1)
        self.total_y_move = self.y_step*(self.N_pts_y-1)

        self.step_raster = step_raster
        
        print('Total Motions: {}, {}'.format(self.total_x_move, self.total_y_move))
        print('Assuming I am starting in the middle')
        if self.step_raster:
            print('I plan to raster the scan')

        if np.mod(self.N_pts_x, 2) == 0 or np.mod(self.N_pts_y, 2)== 0:
            raise ValueError("I only know how to deal with an odd number of data point")
        self.is_setup = True

    def move_x(self, dist, vel):
        if self.ocs:
            self.xy_stage.move_x_cm.start(distance=dist, velocity=vel)
            self.xy_stage.move_x_cm.wait()
        else:
            self.xy_stage.move_x_cm(dist, vel)
            self.xy_stage.wait()

    def move_y(self, dist, vel):
        if self.ocs:
            self.xy_stage.move_y_cm.start(distance=dist, velocity=vel)
            self.xy_stage.move_y_cm.wait()
        else:
            self.xy_stage.move_y_cm(dist, vel)
            self.xy_stage.wait()

    def set_before_scan_function(self, function):
        """Function will run once at the begining of the scan
        """
        self.before_function = function
    def set_during_scan_function(self, function):
        """Function that will run at each position
        """
        self.during_function = function

    def set_after_scan_function(self, function):
        """Function to run after the scan is over
        """
        self.after_function = function

    def execute(self, test_scan = False):
        if self.scan_dir == 'x':
            self.execute_xscan(test_scan)
        elif self.scan_dir == 'y':
            self.execute_yscan(test_scan)
        else:
            raise ValueError("How did scan_dir get set incorrectly?")
    
    def execute_xscan(self, test_scan = False):
        """Execute Planned Scan
        
        Arguments
        ----------
        test_scan : bool
            If true, does not call functions and instead just sleeps for a
            second at each point.
        """
        if not self.is_setup:
            raise ValueError("Scan needs to be setup with setup_scan")
        if self.before_function is None:
            raise ValueError("Need a defined before function, use \
                            set_before_scan_function")        
        if self.during_function is None:
            raise ValueError("Need a defined during function, use \
                            set_during_scan_function")        
        if self.after_function is None:
            raise ValueError("Need a defined before function, use \
                            set_after_scan_function")        

        print('Moving to start position')
        if self.total_x_move > 0:
            self.move_x( -(self.N_pts_x-1)*self.x_step/2, self.x_vel_reset )
        if self.total_y_move > 0:
            self.move_y( -(self.N_pts_y-1)*self.y_step/2, self.y_vel_reset )

        if not test_scan:
            self.before_function()
        else:
            time.sleep(1)

        direction = 1
        for y in range(self.N_pts_y):
            if y > 0:
                self.move_y( self.y_step, self.y_vel)

            for x in range(self.N_pts_x):
                if x > 0:
                    self.move_x(self.x_step*direction, self.x_vel)

                ## call function as each position
                if not test_scan:
                    self.during_function()
                else:
                    time.sleep(1)

            if y < self.N_pts_y-1:
                if self.step_raster:
                    direction *= -1
                else:
                    self.move_x( -self.x_step*(self.N_pts_x-1), self.x_vel_reset)

        ## Reset to start position
        if self.total_x_move > 0:
            self.move_x( -(self.N_pts_x-1)*self.x_step/2, self.x_vel_reset )
        if self.total_y_move > 0:
            self.move_y( -(self.N_pts_y-1)*self.y_step/2, self.y_vel_reset )

        if not test_scan:
            self.after_function()
        else:
            time.sleep(1)
    
    def execute_yscan(self, test_scan = False):
        """Execute Planned Scan
        
        Arguments
        ----------
        test_scan : bool
            If true, does not call functions and instead just sleeps for a
            second at each point.
        """
        if not self.is_setup:
            raise ValueError("Scan needs to be setup with setup_scan")
        if self.before_function is None:
            raise ValueError("Need a defined before function, use \
                            set_before_scan_function")        
        if self.during_function is None:
            raise ValueError("Need a defined during function, use \
                            set_during_scan_function")        
        if self.after_function is None:
            raise ValueError("Need a defined before function, use \
                            set_after_scan_function")        

        print('Moving to start position')
        if self.total_x_move > 0:
            self.move_x( -(self.N_pts_x-1)*self.x_step/2, self.x_vel_reset )
        if self.total_y_move > 0:
            self.move_y( -(self.N_pts_y-1)*self.y_step/2, self.y_vel_reset )

        if not test_scan:
            self.before_function()
        else:
            time.sleep(1)
        
        direction = 1
        for x in range(self.N_pts_x):
            if x > 0:
                self.move_x(self.x_step, self.x_vel)
            for y in range(self.N_pts_y):
                if y > 0:
                    self.move_y( self.y_step*direction, self.y_vel)


                ## call function as each position
                if not test_scan:
                    self.during_function()
                else:
                    time.sleep(1)

            if x < self.N_pts_x-1:
                if self.step_raster:
                    direction *= -1
                else:
                    self.move_y( -self.y_step*(self.N_pts_y-1), self.y_vel_reset)

        ## Reset to start position
        if self.total_x_move > 0:
            self.move_x( -(self.N_pts_x-1)*self.x_step/2, self.x_vel_reset )
        if self.total_y_move > 0:
            self.move_y( -(self.N_pts_y-1)*self.y_step/2, self.y_vel_reset )

        if not test_scan:
            self.after_function()
        else:
            time.sleep(1)

    def setup_raster_yscan(self, total_distance_x, total_distance_y,
                    N_pts_x, x_vel=0.5, y_vel=0.1, 
                    x_vel_reset=None, 
                    y_vel_reset=None):
        """ Accepts the scan parameters for a raster scan
    
        Arguments
        -----------
        total_distance_x : float in cm
            scan will be from -total_disance_x/2 to + total_distance_x/2
        total_distance_y : float in cm
            scan will be from -total_disance_y/2 to + total_distance_y/2
        N_pts_x : int (must be odd)
        x_vel : float (speed to step in cm / s)
        y_vel : float (speed to step in cm / s)
        x_vel_reset : float (speed for larger moves in cm/s)
        y_vel_reset : float (speed for larger moves in cm/s)
        """
        
        self.N_pts_x = N_pts_x
        self.x_vel = x_vel
        self.y_vel = y_vel
        if x_vel_reset is None:
            self.x_vel_reset = x_vel
        else:
            self.x_vel_reset = x_vel_reset
        
        if y_vel_reset is None:
            self.y_vel_reset = y_vel
        else:
            self.y_vel_reset = y_vel_reset
            
        if self.N_pts_x > 1:
            self.x_step = total_distance_x/(self.N_pts_x-1) #cm
        else:
            self.x_step = 0
        
        self.total_x_move = self.x_step*(self.N_pts_x-1)
        self.total_y_move = total_distance_y

        print('Total Motions: {}, {}'.format(self.total_x_move, self.total_y_move))
        print('Assuming I am starting in the middle')
        self.is_raster_setup = True
    
    def execute_raster_yscan(self, test_scan=False):        
        if not self.is_raster_setup:
            raise ValueError("Scan needs to be setup with setup_raster_yscan")
        if self.before_function is None:
            raise ValueError("Need a defined before function, use \
                            set_before_scan_function")              
        if self.after_function is None:
            raise ValueError("Need a defined before function, use \
                            set_after_scan_function")   
        
        if self.total_x_move > 0:
            self.move_x( -(self.N_pts_x-1)*self.x_step/2, self.x_vel_reset )
        if self.total_y_move > 0:
            self.move_y( -self.total_y_move/2, self.y_vel_reset )
            
        if not test_scan:
            self.before_function()
        else:
            time.sleep(1)
        
        direction = 1
        for x in range(self.N_pts_x):
            if x > 0:
                self.move_x(self.x_step, self.x_vel)
            
            self.move_y( direction*self.total_y_move, self.y_vel)
            direction *= -1
        if not test_scan:
            self.after_function()
        else:
            time.sleep(1)
