#region Set up code
from vex import *
import math

brain = Brain(),
controller_1 = Controller(PRIMARY),

left_motor_a = Motor(Ports.PORT1, GearSetting.RATIO_36_1, True),
left_motor_b = Motor(Ports.PORT2, GearSetting.RATIO_36_1, True),
left_drive_smart = MotorGroup(left_motor_a, left_motor_b)

right_motor_a = Motor(Ports.PORT3, GearSetting.RATIO_36_1, False),
right_motor_b = Motor(Ports.PORT4, GearSetting.RATIO_36_1, False),
right_drive_smart = MotorGroup(right_motor_a, right_motor_b)

donut_elevator = Motor(Ports.PORT10, GearSetting.RATIO_18_1, False)
stake_piston = DigitalOut(brain.three_wire_port.a)
    
velocity = 0
accel_stick = 0
turn_stick = 0
target_velocity = 0
turning_velocity = 0
stake_piston_extended = False
donut_elevator_moving = False
#endregion

#region Math functions (logistic, get_velocity, limit)
def logistic(x: float) -> float:
    # See https://www.desmos.com/calculator/4hrf2l0lzf

    # max value of output
    M = 100

    # The slope I guess
    k = 0.15

    # adjustment (put center at 50)
    a = 50

    return M / (1 + math.exp(-k*(x - a)))

def get_velocity(val: float, current_speed=100.0) -> float:

    sgn = 1

    if val < 0:
        val = abs(val)
        sgn = -1

    # Controller value is within 0 < val <= 100

    if 0 < val <= 50:
        return sgn * math.ceil(logistic(val))

    # Create range where speed snaps to magic number 63
    # 63% speed is max power consumption.
    if 51 <= val <= 64:
        return sgn * (val + 10)

    if 65 <= val <= 100:
        # Improve acceleration when flooring accelerator
        if current_speed < 55:
            return sgn * 60
        else:
            return sgn * math.ceil(logistic(val))
    
    return 0

def limit(x):
    if x == 0:
        return 0
    
    sign = 0

    if x < 0:
        sign = -1
    else:
        sign = 1
    
    if sign*x >= 100:
        return sign*100
    else:
        return x
#endregion

def toggle_stake_piston():
    global stake_piston_extended, stake_piston

    stake_piston_extended = not stake_piston_extended
    stake_piston.set(stake_piston_extended)

def toggle_donut_elevator():
    global donut_elevator_moving, donut_elevator

    donut_elevator_moving = not donut_elevator_moving
    donut_elevator.spin(FORWARD, 100 * donut_elevator_moving, PERCENT)


def update(S, D):

    # Update s
    velocity = (left_drive_smart.velocity(PERCENT) + right_drive_smart.velocity(PERCENT)) / 2
    accel_stick = controller_1.axis2.position()
    turn_stick = controller_1.axis4.position()
    target_velocity = get_velocity(accel_stick, velocity)
    turn_velocity = get_velocity(turn_stick, 100) * 0.5

    # Rumble controller when full power being used
    if 51 <= abs(accel_stick) <= 64:
        controller_1.rumble("--")
    
    # Update controller screen
    controller_1.screen.clear_screen()
    controller_1.screen.set_cursor(1, 1)
    controller_1.screen.print("Turning", turn_velocity)

    left_drive_smart.spin(FORWARD, target_velocity + turn_velocity, VelocityUnits.PERCENT)
    right_drive_smart.spin(FORWARD, target_velocity - turn_velocity, VelocityUnits.PERCENT)

def main():


    # Init callback
    controller_1.buttonR2.pressed(toggle_stake_piston)
    controller_1.buttonR1.pressed(toggle_stake_piston)