from vex import *
import math


DRIVER = "Parthib".upper()
VEL_PERCENT = 80

#region Control math functions
def logistic(x: float) -> float:
    # See https://www.desmos.com/calculator/ckpeuxjv0c

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
    if 51 <= val <= 75:
        return sgn * (val + 10)

    if 76 <= val <= 100:
        # Improve acceleration when flooring accelerator
        if abs(current_speed) < 55:
            return sgn * 60
        else:
            return sgn * math.ceil(logistic(val))
    
    return 0

def limit(x: float) -> float:
    return max(min(x, 100), -100)
#endregion Control math functions


#region Declare robot parts
brain = Brain()
controller = Controller(PRIMARY)

left_group = MotorGroup(
                Motor(Ports.PORT1, GearSetting.RATIO_18_1, True),
                Motor(Ports.PORT2, GearSetting.RATIO_18_1, True)
            )

right_group = MotorGroup(
                Motor(Ports.PORT3, GearSetting.RATIO_18_1, False), 
                Motor(Ports.PORT4, GearSetting.RATIO_18_1, False)
            )

drivetrain = DriveTrain(
    lm = left_group,
    rm = right_group,
    wheelTravel = 101.6 * math.pi,
    trackWidth = 230,
    wheelBase = 340,
    units = MM,
    externalGearRatio = 48 / 36
)

donut_elevator = Motor(Ports.PORT10, GearSetting.RATIO_18_1, True)
stake_piston = DigitalOut(brain.three_wire_port.a)
#endregion


#region Helper routines
donut_elevator_is_active = False
def toggle_donut_elevator():
    global donut_elevator_is_active

    donut_elevator_is_active = not donut_elevator_is_active

    donut_elevator.spin(FORWARD, 100 * donut_elevator_is_active)


def grab_stake():
    stake_piston.set(False)


def release_stake():
    stake_piston.set(True)
#endregion


#region Main routines
def init():
    left_group.set_stopping(COAST)
    right_group.set_stopping(COAST)

    # Init callback
    controller.buttonR2.pressed(release_stake)
    controller.buttonR2.released(grab_stake)

    controller.buttonL1.pressed(donut_elevator.spin, (FORWARD, 60, PERCENT))
    controller.buttonL1.released(donut_elevator.spin, (FORWARD, 0, PERCENT))
    controller.buttonL2.pressed(donut_elevator.spin, (REVERSE, 60, PERCENT))
    controller.buttonL2.released(donut_elevator.spin, (FORWARD, 0, PERCENT))

    if DRIVER == "PARTHIB":
        controller.buttonY.pressed(toggle_donut_elevator)

def auton():
    release_stake()

    # Wait for the piston to finish retracting.
    wait(0.3, SECONDS)

    drivetrain.drive_for(REVERSE, 32, INCHES, 65, PERCENT)
    grab_stake()
    drivetrain.drive_for(REVERSE, 1.5, INCHES, 40, PERCENT)

    wait(0.5, SECONDS)

    # TODO: Adjust the code based on the starting position of the robot.
    drivetrain.turn_for(RIGHT, 50, DEGREES)
    donut_elevator.spin(FORWARD, 100, PERCENT)

    wait(1, SECONDS)

    # Unstuck the donut elevator if it is stuck.
    if donut_elevator.velocity(PERCENT) <= 2.0:
        donut_elevator.spin_for(REVERSE, 30, DEGREES, 100, PERCENT)

    wait(5, SECONDS)

    # This is redundant but it's better to be sure.
    drivetrain.stop()
    donut_elevator.stop()


def loop():
    while True:
        velocity = (left_group.velocity(PERCENT) + right_group.velocity(PERCENT)) / 2

        accel_stick = controller.axis3.position()
        turn_stick = controller.axis1.position()

        target_velocity = get_velocity(accel_stick, velocity)
        turn_velocity = get_velocity(turn_stick, 100)

        left_velocity = limit(target_velocity + turn_velocity/2) * (VEL_PERCENT / 100)
        right_velocity = limit(target_velocity - turn_velocity/2) * (VEL_PERCENT / 100)

        left_group.spin(FORWARD, left_velocity, PERCENT)
        right_group.spin(FORWARD, right_velocity, PERCENT)
#endregion Main routines

competition = Competition(loop, auton)