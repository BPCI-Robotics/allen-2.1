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

        self.left_position = 0.0
        self.right_position = 0.0

        self.angle = 0.0

        self.wheelbase = wheelbase_width

        threading.Thread(target=self.telemetry_loop).start()

    def telemetry_loop(self):
        start_time = time.perf_counter()

        # Get the new positions of the motors (say, 400 degrees)
        left_position_new = self.left_group.position(DEGREES)
        right_position_new = self.right_group.position(DEGREES)

        # Get the change in motor position (say it went from 380 to 400 degrees, so 20 degrees)
        delta_left_position = left_position_new - self.left_position
        delta_right_position = right_position_new - self.right_position

        # Get the change in distance for each side of the robot (for 20 degrees on 4" that is 1.77 cm)
        delta_left_distance = convert(delta_left_position, "deg", "rad") * WHEEL_RADIUS
        delta_right_distance = convert(delta_right_position, "deg", "rad") * WHEEL_RADIUS

        # The average of the two is how far it went forward in total (as a vector)
        delta_forward_distance = (delta_left_distance + delta_right_distance) / 2
        
        # The difference between the two over the width of the wheelbase is how much it turned.
        delta_angle = (delta_right_distance - delta_left_distance) / self.wheelbase

        # Update data
        self.angle += delta_angle
        self.x += delta_forward_distance * math.cos(self.angle)
        self.y += delta_forward_distance * math.sin(self.angle)

        end_time = time.perf_counter()
        time_spent = end_time - start_time

        time.sleep(max(0, 1/FREQUENCY - time_spent))
