from vex import *
import threading, time

FREQUENCY = 60 # updates per second

class RoboData:
    def __init__(self, pos: tuple[float, float], rot: float, motors: Tuple[MotorGroup, MotorGroup], wheelbase_width: int):

        # Position is defined as metres from the point (0, 0) 
        # where positive and negative directions are arbitrary.
        # The field is symmetric and this doesn't matter.

        self.x, self.y = pos
        self.rot = rot
        self.left_group, self.right_group = motors

        self.x_vel = 0.0 # m/s
        self.y_vel = 0.0 # m/s
        
        # The velocity could not be in a different direction from the robot.
        self.vel = 0.0 # m/s

        # But the acceleration could.
        self.accel_val = 0.0 # m/s^2
        self.accel_dir = 0.0 # radians

        threading.Thread(target=self.telemetry_loop).start()
    
    def update_velocities(self):
        left = self.left_group.velocity(RPM)
        right = self.right_group.velocity(RPM)

        left /= 60
        right /= 60

    def telemetry_loop(self):
        start_time = time.perf_counter()

        # Code goes under here.

        self.x_vel = self.left_group.velocity(PERCENT)
        self.y_vel = self.right_group.velocity(PERCENT)

        self.x += self.x_vel / FREQUENCY
        self.y += self.y_vel / FREQUENCY
        
        self.vel = (self.x_vel + self.y_vel) / 2

        # Code goes above here.

        end_time = time.perf_counter()
        time_spent = end_time - start_time

        time.sleep(max(0, 1/FREQUENCY - time_spent))
