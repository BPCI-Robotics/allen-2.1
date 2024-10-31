from vex import *
import threading, time, math
from math_tools import *

FREQUENCY = 60 # updates per second

class RoboData:
    def __init__(self, pos: tuple[float, float], rot: float, motors: tuple[MotorGroup, MotorGroup], wheelbase_width: int):

        # Position is defined as metres from the point (0, 0) 
        # where positive and negative directions are arbitrary.
        # The field is symmetric and this doesn't matter.

        self.x, self.y = pos
        self.rot = rot
        self.left_group, self.right_group = motors

        self.left_angle = 0.0
        self.right_angle = 0.0

        self.wheelbase = wheelbase_width

        threading.Thread(target=self.telemetry_loop).start()

    def telemetry_loop(self):
        start_time = time.perf_counter()

        left_angle_new = self.left_group.position(DEGREES)
        right_angle_new = self.right_group.position(DEGREES)

        delta_left_angle = left_angle_new - self.left_angle
        delta_right_angle = right_angle_new - self.right_angle

        delta_left_distance = convert(delta_left_angle, "deg", "rad") * WHEEL_RADIUS
        delta_right_distance = convert(delta_right_angle, "deg", "rad") * WHEEL_RADIUS

        delta_forward_distance = (delta_left_distance + delta_right_distance) / 2
        
        delta_angle = (delta_right_distance - delta_left_distance) / self.wheelbase

        

        end_time = time.perf_counter()
        time_spent = end_time - start_time

        time.sleep(max(0, 1/FREQUENCY - time_spent))
