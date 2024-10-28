from vex import *

class RoboData:
    def __init__(self, pos: Tuple[float, float], rot: float, motors: Tuple[MotorGroup, MotorGroup]):
        self.x, self.y = pos
        self.rot = rot
        self.left_group, self.right_group = motors

        self.x_vel = 0.0
        self.y_vel = 0.0
        
        # The velocity could not be in a different direction from the robot.
        self.vel = 0.0

