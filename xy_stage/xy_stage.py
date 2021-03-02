from axis import Axis, CombinedAxis

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
        
    @property
    def position(self):
        return (self.x_axis.position, self.y_axis.position)

    @property
    def moving(self):
        return self.x_axis.keep_moving or self.y_axis.keep_moving

    @property
    def limits(self):
        return self.x_axis.limits, self.y_axis.limits

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
            velocity, how quickly to move
        '''
        if distance > 0:
            dir = False
        else:
            dir = True
        self.x_axis.move_cm(dir, abs(distance), velocity)

    def move_y_cm(self, distance, velocity=None):
        '''
        Args:
            distance -- number of cm to move
                     -- negative numbers go toward home
            velocity, how quickly to move
        '''
        if distance > 0:
            dir = False
        else:
            dir = True
        self.y_axis.move_cm(dir, abs(distance), velocity)

    def move_to_cm(self, new_position, velocity=None, require_home=True):
        assert len(new_position) == 2
        if velocity is None:
            velocity = None, None
        else:
            assert len(velocity) == 2
        self.x_axis.move_to_cm( new_position[0], velocity[0], require_home)
        self.y_axis.move_to_cm( new_position[1], velocity[1], require_home)

    def stop(self):
        ## probably doesn't need to be run twice. 
        ## the x-axis can break the y-axis...
        self.x_axis.stop()
        self.y_axis.stop()

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

    xy_stage.move_x_cm( 10 )
    time.sleep(2)
    xy_stage.move_y_cm( 20 )
    time.sleep(1)
    xy_stage.move_x_cm( -5)
    xy_stage.stop()
