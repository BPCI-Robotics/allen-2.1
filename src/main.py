from vex import *
import math

# Flags
AUTON_TESTING = False

REVERSED = True
GEAR_CARTRIDGE = GearSetting.RATIO_18_1

DONUT_ELEVATOR_FORWARD_SPEED = 80
DONUT_ELEVATOR_REVERSE_SPEED = 40

# Drivetrain settings (mm)
WHEEL_DIAMETER = 4
TRACK_WIDTH = 300
WHEEL_BASE = 300
GEAR_RATIO = 48 / 36

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

#region Set up code
brain = Brain()
controller = Controller(PRIMARY)

left_group = MotorGroup(
                Motor(Ports.PORT1, GEAR_CARTRIDGE, REVERSED),
                Motor(Ports.PORT2, GEAR_CARTRIDGE, REVERSED)
            )

right_group = MotorGroup(
                Motor(Ports.PORT3, GEAR_CARTRIDGE, not REVERSED), 
                Motor(Ports.PORT4, GEAR_CARTRIDGE, not REVERSED)
            )

donut_elevator = Motor(Ports.PORT10, GEAR_CARTRIDGE, False)
stake_piston = DigitalOut(brain.three_wire_port.a)
# chain_button = Bumper(brain.three_wire_port.b)
drivetrain = DriveTrain(
    lm=left_group,
    rm=right_group,
    wheelTravel=WHEEL_DIAMETER * math.pi,
    trackWidth=TRACK_WIDTH,
    wheelBase=WHEEL_BASE,
    units=INCHES,
    externalGearRatio=GEAR_RATIO
)

velocity = 0
accel_stick = 0
turn_stick = 0
target_velocity = 0
turning_velocity = 0

#endregion

#region Main routines
def init():
    global controller, left_group, right_group, stake_piston, donut_elevator

    left_group.set_stopping(COAST)
    right_group.set_stopping(COAST)

    # Init callback
    controller.buttonR2.pressed(stake_piston.set, (True,))
    controller.buttonR2.released(stake_piston.set, (False,))

    controller.buttonA.pressed(donut_elevator.spin, (FORWARD, DONUT_ELEVATOR_FORWARD_SPEED, PERCENT))
    controller.buttonA.released(donut_elevator.spin, (FORWARD, 0, PERCENT))
    controller.buttonB.pressed(donut_elevator.spin, (REVERSE, DONUT_ELEVATOR_REVERSE_SPEED, PERCENT))
    controller.buttonB.released(donut_elevator.spin, (FORWARD, 0, PERCENT))


def auton():
    global drivetrain

    drivetrain.drive_for(FORWARD, 1000, MM, 63, PERCENT, True)
    drivetrain.turn_for(LEFT, 90, DEGREES, 63, PERCENT, True)
    
controller_clear_counter = 0

def loop():

    global velocity, accel_stick, turn_stick, target_velocity, turn_velocity
    global controller, left_group, right_group

    # Update state
    velocity = (left_group.velocity(PERCENT) + right_group.velocity(PERCENT)) / 2
    accel_stick = controller.axis2.position()
    turn_stick = controller.axis1.position()
    target_velocity = get_velocity(accel_stick, velocity)
    turn_velocity = get_velocity(turn_stick, 100)

    # Rumble controller when full power being used
    if 51 <= abs(velocity) <= 64:
        controller.rumble("--")
    
    global controller_clear_counter
    controller_clear_counter += 1
    if (controller_clear_counter == 10):
        controller.screen.clear_screen()
        
    # Update controller screen

    controller.screen.set_cursor(1, 1)
    controller.screen.print("Turning", turn_velocity)

    left_velocity = limit(target_velocity + turn_velocity/1.5) / 2
    right_velocity = limit(target_velocity - turn_velocity/1.5) / 2

    left_group.spin(FORWARD, left_velocity, PERCENT)
    right_group.spin(FORWARD, right_velocity, PERCENT)

    controller.screen.set_cursor(2, 1)
    controller.screen.print("Left_vel", left_velocity)
    controller.screen.set_cursor(3, 1)
    controller.screen.print("Righ_vel", right_velocity)
#endregion Main routines

if __name__ == "__main__":
    init()
    if AUTON_TESTING:
        while True:
            auton()
    else:
        while True:
            loop()