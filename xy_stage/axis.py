import RPi.GPIO as GPIO
import time
import os

class Axis:
    """
    Base Class for one of the XY gantry axes

    All move commands are written to be called in threads
    
    self.position and/or self.step position can safely be queried
        while the axis is moving. 
    """
    def __init__(self, name, pin_list, steps_per_cm, logfile=None):
        self.name = name
        self.ena = pin_list['ena']
        self.pul = pin_list['pul']
        self.dir = pin_list['dir']

        self.eot_ccw = pin_list['eot_ccw']
        self.eot_cw = pin_list['eot_cw']

        self.setup_pins()
        
        self.hold_enable = False
        self.keep_moving = False
        self.step_position = 0
        self.logfile = logfile
        if self.logfile is not None and os.path.exists(self.logfile):
            with open(self.logfile, "r") as pos_file:
                self.step_position = int(pos_file.read())
        
        self.steps_per_cm = steps_per_cm
        self.max_vel = 1.27 ## cm / s
        self.homed = False

    @property
    def position(self):
        return self.step_position / self.steps_per_cm

    @position.setter
    def position(self, value):
        if self.keep_moving:
            raise ValueError("Cannot update position while moving")
        self.step_position = value*self.steps_per_cm

    @property
    def limits(self):
        '''
        Returns: (home limit, far side limit)
        '''
        self.set_limits()
        return self.lim_cw, self.lim_ccw
        
    def setup_pins(self):
        GPIO.setmode(GPIO.BCM)

        for pin in [self.ena, self.pul, self.dir]:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)
        for pin in [self.eot_ccw, self.eot_cw]:
            GPIO.setup(pin, GPIO.IN)

    def set_limits(self):
        ### pins go low when they are engaged
        self.lim_ccw =  GPIO.input(self.eot_ccw) == GPIO.LOW 
        self.lim_cw =  GPIO.input(self.eot_cw) == GPIO.LOW 
        return self.lim_ccw or self.lim_cw

    def home(self, max_dist=150, reset_pos=True):
        """Move axis at 1 cm/s toward the home limit.
        
        Arguments
        ----------
        max_dist : float
            the maximum number of cm to move for homing
        reset_pos : bool
            if true, axis position is reset to zero
        """    
        while not self.lim_cw:
            self.move_cm(True, max_dist, velocity=1)
        if reset_pos:
            self.step_position = 0
        self.homed = True

    def move_cm(self, dir, distance, velocity=None):
        '''
        Axis Moves the commanded number of cm. Converts to steps 
            and calls the move_step function

        Args:
            dir -- True goes toward home (the motors)
            distance -- number of cm to move
            velocity -- how quickly to move
        '''
        steps = distance*self.steps_per_cm
        if velocity is None:
            velocity = self.max_vel

        if velocity > self.max_vel:
            print('Requested Velocity too high, setting to {} cm/s'.format(self.max_vel))
            velocity = self.max_vel

        wait = 1.0/(2*velocity*self.steps_per_cm)
        success, steps = self.move_step(dir, steps, wait)
        return success, steps/self.steps_per_cm

    def move_to_cm(self, new_position, velocity=None, require_home=True):
        '''
        Move Axis to the requested position. 
        
        Args:
            new_position -- the position you want to move to
            velocity -- how fast to move (cm/s)
            require_home -- if true, requires the axis position to be calibrated
                defaults to true to prevent mistakes
        '''
        if not self.homed:
            if require_home:
                print('ERROR -- Axis Position Not Calibrated')
                return False
            print('WARNING -- Axis Position Not calibrated')
        distance = new_position - self.position         
        if distance < 0:
            return self.move_cm( True, abs(distance), velocity)
        
        return self.move_cm(False, abs(distance), velocity)

    def enable(self):
        self.hold_enable = True
        GPIO.output(self.ena, GPIO.LOW)

    def disable(self):
        self.hold_enable = False
        GPIO.output(self.ena, GPIO.HIGH)

    def move_step(self, dir, steps=100, wait=0.005):
        ## direction = False is toward the CCW limit
        ## direction = True is toward the CW limit
        steps = int(round(steps))
        self.keep_moving = True
        
        if dir:
            increment = -1
        else:
            increment = 1
        if not self.hold_enable:
            GPIO.output( self.ena, GPIO.LOW)
        GPIO.output(self.dir, dir)
        
        time.sleep(0.25)

        while steps > 0 and self.keep_moving:
       
            if self.set_limits():
                if (not dir) and self.lim_ccw:
                    #print('Hit CCW limti with {} steps left'.format(steps))
                    self.keep_moving = False
                    break
                elif dir and self.lim_cw:
                    ### true goes to home
                    self.keep_moving = False
                    break
                #print('LIMIT!')
                #print('CCW: ', self.lim_ccw, 'CW:', self.lim_cw)
            
            GPIO.output(self.pul, GPIO.HIGH)
            time.sleep(wait)
            GPIO.output(self.pul, GPIO.LOW)
            time.sleep(wait)
            self.step_position += increment
            steps -= 1
            if self.logfile is not None:
                with open(self.logfile, "w") as pos_file:
                    pos_file.write(self.step_position)

        if not self.hold_enable:
            GPIO.output(self.ena, GPIO.HIGH)
        if not self.keep_moving:
            #print('I think I hit a limit with {} steps left'.format(steps))
            return False, steps

        self.keep_moving = False
        return True, steps
    
    def stop(self):
        self.keep_moving = False
    
    def cleanup(self):
        GPIO.cleanup()


class CombinedAxis(Axis):
    """
    Two axes where the control outputs are electrically connected

    This assumes there's two limit switches per axes so there's two
    limits on each side.
    """
    def setup_pins(self):
        GPIO.setmode(GPIO.BCM)

        for pin in [self.ena, self.pul, self.dir]:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)
        for pins in [self.eot_ccw, self.eot_cw]:
            for pin in pins:
                GPIO.setup(pin, GPIO.IN)

    def set_limits(self):
        ### pins go low when they are engaged
        self.lim_ccw = (GPIO.input(self.eot_ccw[0]) == GPIO.LOW) or (GPIO.input(self.eot_ccw[1]) == GPIO.LOW)  
        self.lim_cw =  (GPIO.input(self.eot_cw[0]) == GPIO.LOW) or (GPIO.input(self.eot_cw[1]) == GPIO.LOW)  
        return self.lim_ccw or self.lim_cw

if __name__ == '__main__':
    from threading import Thread

    STEP_PER_CM = 1574.80316
    
    ### used when only one axis is plugged in to Xa
    x_axis = Axis('X', 
            pin_list={
            'ena':2, 'pul':4, 'dir':3,
            'eot_ccw':17, 'eot_cw':27}, 
             steps_per_cm = STEP_PER_CM)
    '''
    #### BCM PIN NUMBERS
    x_axis = CombinedAxis('X', 
            pin_list={
            'ena':2, 'pul':4, 'dir':3,
            'eot_ccw':[17,23], 'eot_cw':[27,24]}, 
             steps_per_cm = STEP_PER_CM)
    
    y_axis = Axis('Y', 
            pin_list={
            'ena':16, 'pul':21, 'dir':20,
            'eot_ccw':19, 'eot_cw':26},
            steps_per_cm = STEP_PER_CM)
    '''
    #x = Thread(target=x_axis.move_to_cm, args=(10, 1, False))
    x = Thread(target=x_axis.home, args=() )
    print('starting')
    x.start()
    time.sleep(0.01)
    while x_axis.keep_moving:
        time.sleep(1)
        print(x_axis.position)
        if x_axis.position > 4:
            x_axis.position=0
    x.join()
    print('all done')
    x_axis.stop()
    #x_axis.move_step(False, 5000, 0.0001)
    
    #time.sleep(0.1)
    
    #test.move(True,2000, 0.0001)
    
    #test.print_limits(nread=40, wait=0.25) 
    #time.sleep(30)

        
