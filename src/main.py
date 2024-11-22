from vex import *
import math


DRIVER = "Parthib".upper()

DONUT_ELEVATOR_FORWARD_SPEED = 100
DONUT_ELEVATOR_REVERSE_SPEED = 60

REVERSED = True
GEAR_CARTRIDGE = GearSetting.RATIO_18_1
VEL_PERCENT = 80

# Drivetrain settings (mm)
WHEEL_DIAMETER = 101.6
TRACK_WIDTH = 230
WHEEL_BASE = 340
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

#region Declare robot parts
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

drivetrain = DriveTrain(
    lm=left_group,
    rm=right_group,
    wheelTravel=WHEEL_DIAMETER * math.pi,
    trackWidth=TRACK_WIDTH,
    wheelBase=WHEEL_BASE,
    units=MM,
    externalGearRatio=GEAR_RATIO
)

donut_elevator = Motor(Ports.PORT10, GEAR_CARTRIDGE, True)
stake_piston = DigitalOut(brain.three_wire_port.a)

velocity = 0
accel_stick = 0
turn_stick = 0
target_velocity = 0
turning_velocity = 0

#endregion

#region Main routines

donut_elevator_is_active = False
def toggle_donut_elevator():
    global donut_elevator_is_active

    donut_elevator_is_active = not donut_elevator_is_active

    donut_elevator.spin(FORWARD, DONUT_ELEVATOR_FORWARD_SPEED if donut_elevator_is_active else 0, PERCENT)

def init():
    left_group.set_stopping(COAST)
    right_group.set_stopping(COAST)

    # Init callback
    controller.buttonR2.pressed(stake_piston.set, (True,))
    controller.buttonR2.released(stake_piston.set, (False,))

    controller.buttonL1.pressed(donut_elevator.spin, (FORWARD, DONUT_ELEVATOR_FORWARD_SPEED, PERCENT))
    controller.buttonL1.released(donut_elevator.spin, (FORWARD, 0, PERCENT))
    controller.buttonL2.pressed(donut_elevator.spin, (REVERSE, DONUT_ELEVATOR_REVERSE_SPEED, PERCENT))
    controller.buttonL2.released(donut_elevator.spin, (FORWARD, 0, PERCENT))

    if DRIVER == "PARTHIB":
        controller.buttonY.pressed(toggle_donut_elevator)

    

start_positions = ['top-left', 'top-right', 'bottom-left', 'bottom-right']

def auton():
    global drivetrain, stake_piston, claw_lift, start_positions

    """drivetrain.set_stopping(BRAKE)
    stake_piston.set(False)
    donut_elevator.set_velocity(80, PERCENT)
    donut_elevator.spin(FORWARD)
    drivetrain.drive_for(FORWARD, 250, INCHES)
    donut_elevator.set_velocity(0, PERCENT)
    
    vision_sensor1 = Vision(port=13)"""
    
    stake_piston.set(True)
    wait(0.5, SECONDS)
    drivetrain.drive_for(REVERSE, 32, INCHES, 65, PERCENT)
    stake_piston.set(False)
    drivetrain.drive_for(REVERSE, 1.5, INCHES, 40, PERCENT)
    wait(0.5, SECONDS)
    #this depends on which starting position the robot is on
    drivetrain.turn_for(RIGHT, 50, DEGREES)
    donut_elevator.spin(FORWARD, 100, PERCENT)

    wait(1, SECONDS)

    if donut_elevator.velocity(RPM) <= 2:
        donut_elevator.spin_for(REVERSE, 30, DEGREES, 100, PERCENT)

    wait(5, SECONDS)

    drivetrain.stop()
    donut_elevator.stop()
    # wait(5, SECONDS)
    
controller_clear_counter = 0

def loop():

    global velocity, accel_stick, turn_stick, target_velocity, turn_velocity
    global controller, left_group, right_group
    global sped_limit

    # Update state
    velocity = (left_group.velocity(PERCENT) + right_group.velocity(PERCENT)) / 2

    accel_stick = controller.axis3.position()
    turn_stick = controller.axis1.position()
    brain.screen.set_cursor(1, 1)
    brain.screen.print(accel_stick)
    brain.screen.set_cursor(2, 1)
    brain.screen.print(turn_stick)
        
    target_velocity = get_velocity(accel_stick, velocity)
    turn_velocity = get_velocity(turn_stick, 100)

    """# Rumble controller when full power being used
    if 51 <= abs(velocity) <= 64:
        controller.rumble("--")"""
    
    """global controller_clear_counter
    controller_clear_counter += 1
    if (controller_clear_counter == 10):
        controller.screen.clear_screen()"""
        
    # Update controller screen

    left_velocity = limit(target_velocity + turn_velocity/2) * (VEL_PERCENT / 100)
    right_velocity = limit(target_velocity - turn_velocity/2) * (VEL_PERCENT / 100)

    left_group.spin(FORWARD, left_velocity, PERCENT)
    right_group.spin(FORWARD, right_velocity, PERCENT)
    

#endregion Main routines

competition = Competition(loop, auton)