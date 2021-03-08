from . import Axis, CombinedAxis

import time
from threading import Thread


class XY_Stage(object):
    
    def __init__(self, xpin_list, ypin_list, xsteps_per_cm, ysteps_per_cm=None):
        '''
        Args:
            xpin_list: the pins needed for the X-axis
            ypin_list: the pins needed for the Y-axis
            xsteps_per_cm: steps needed to move the x stages 1 cm
                used for y axis as well if only one is defined
        '''
        self.x_axis = CombinedAxis('X', xpin_list, xsteps_per_cm)

        if ysteps_per_cm is None:
            ysteps_per_cm = xsteps_per_cm
        self.y_axis = Axis('Y', ypin_list, ysteps_per_cm)
        self.mv_thrd = None
        
    @property
    def position(self):
        return (self.x_axis.position, self.y_axis.position)

    @property
    def moving(self):
        return self.x_axis.keep_moving or self.y_axis.keep_moving

    @property
    def limits(self):
        return self.x_axis.limits, self.y_axis.limits

    @property
    def homed(self):
        return self.x_axis.homed and self.y_axis.homed

    def home(self, max_dist=150):
        '''
        Home both axes. Should probably add some failure checking
        '''

        self.x_axis.home(max_dist)
        self.y_axis.home(max_dist)

    def move_x_cm(self, distance, velocity=None):
        '''
        Args:
            distance -- number of cm to move
                     -- negative numbers go toward home
            velocity, how quickly to move, in cm/s
                     -- (Speed really, always positive) 
        '''
        if self.moving:
            raise ValueError("Cannot start new move before previous move is finished")

        if distance > 0:
            dir = False
        else:
            dir = True

        self.mv_thrd = Thread(target=self.x_axis.move_cm, 
                args=(dir, abs(distance), abs(velocity)) )
        self.mv_thrd.start()

    def move_y_cm(self, distance, velocity=None):
        '''
        Args:
            distance -- number of cm to move
                     -- negative numbers go toward home
            velocity, how quickly to move, in cm/s
                    -- (Speed really, always positive)
        '''
        if self.moving:
            raise Exception("Cannot start new move before previous move is finished")
        
        if distance > 0:
            dir = False
        else:
            dir = True
        
        self.mv_thrd = Thread(target=self.y_axis.move_cm, 
                args=(dir, abs(distance), abs(velocity)) )
        self.mv_thrd.start()

    def move_to_cm(self, new_position, velocity=None, require_home=True):
        assert len(new_position) == 2
        if velocity is None:
            velocity = None, None
        else:
            assert len(velocity) == 2
        self.x_axis.move_to_cm( new_position[0], velocity[0], require_home)
        self.y_axis.move_to_cm( new_position[1], velocity[1], require_home)

    def stop(self):
        self.x_axis.stop()
        self.y_axis.stop()
        
    def cleanup():
        self.x_axis.cleanup()

if __name__ == '__main__':
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

    xy_stage = XY_Stage(xpins, ypins, STEP_PER_CM)
    print(xy_stage.limits)

    x = Thread(target=xy_stage.move_y_cm, args=(-6,.5))
    x.start()
    time.sleep(0.01)
    while xy_stage.moving:
        time.sleep(0.5)
        print(xy_stage.position)
    x.join()
    
    x = Thread(target=xy_stage.move_y_cm, args=(7,.5))
    x.start()
    time.sleep(0.01)
    while xy_stage.moving:
        time.sleep(0.5)
        print(xy_stage.position)
    x.join()
    
    #xy_stage.move_x_cm( 10 )
    #time.sleep(2)
    #xy_stage.move_y_cm( 20 )
    #time.sleep(1)
    #xy_stage.move_x_cm( -5)
    
    xy_stage.cleanup()
