from vex import *
import math

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
#endregion

# Flags
AUTON_TESTING = False
NAME = "Allen"

DONUT_ELEVATOR_FORWARD_SPEED = 100
DONUT_ELEVATOR_REVERSE_SPEED = 80

NAME = NAME.upper()

if NAME == "ALLEN":
    REVERSED = True
    GEAR_CARTRIDGE = GearSetting.RATIO_18_1
    VEL_PERCENT = 100

    # Drivetrain settings (mm)
    WHEEL_DIAMETER = 101.6
    TRACK_WIDTH = 230
    WHEEL_BASE = 340
    GEAR_RATIO = 60 / 48

elif NAME == "BARRON":
    # TODO: Measure drivetrain parameters!

    REVERSED = True
    GEAR_CARTRIDGE = GearSetting.RATIO_18_1

    # Manual drive parameters
    VEL_PERCENT = 75

    # Drivetrain settings (mm)
    WHEEL_DIAMETER = 101.6
    TRACK_WIDTH = 381
    WHEEL_BASE = 381
    GEAR_RATIO = 60 / 48

else:
    raise NameError("No configuration specified for " + NAME + ".")

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

if NAME == "ALLEN":
    donut_elevator = Motor(Ports.PORT10, GEAR_CARTRIDGE, True)
    stake_piston = DigitalOut(brain.three_wire_port.a)

if NAME == "BARRON":
    claw_lift = Motor(Ports.PORT9, GearSetting.RATIO_18_1)
    claw_claw = Motor(Ports.PORT10, GearSetting.RATIO_36_1)


running = True

#endregion

#region Main routines

def stop_everything():
    global NAME, running
    drivetrain.set_stopping(BRAKE)
    left_group.set_stopping(BRAKE)
    right_group.set_stopping(BRAKE)

    if NAME == "ALLEN":
        donut_elevator.set_velocity(0, PERCENT)
        drivetrain.set_drive_velocity(0, PERCENT)
        left_group.set_velocity(0, PERCENT)
        right_group.set_velocity(0, PERCENT)
    
    if NAME == "BARRON":
        claw_lift.set_stopping(BRAKE)
        claw_claw.set_stopping(BRAKE)
        claw_lift.stop()
        claw_claw.stop()

    stake_piston.set(True)
    drivetrain.stop()

    running = False

donut_elevator_is_active = False
def toggle_donut_elevator():
    global donut_elevator_is_active

    donut_elevator_is_active = not donut_elevator_is_active

    donut_elevator.spin(FORWARD, DONUT_ELEVATOR_FORWARD_SPEED if donut_elevator_is_active else 0, PERCENT)


def init():
    global controller, left_group, right_group, stake_piston, donut_elevator, NAME
    
    RETRACT = True
    EXTEND = False

    left_group.set_stopping(COAST)
    right_group.set_stopping(COAST)

    # Init callback
    if NAME == "ALLEN":
        controller.buttonR2.pressed(stake_piston.set, (RETRACT,))
        controller.buttonR2.released(stake_piston.set, (EXTEND,))

        controller.buttonL1.pressed(donut_elevator.spin, (FORWARD, DONUT_ELEVATOR_FORWARD_SPEED, PERCENT))
        controller.buttonL1.released(donut_elevator.spin, (FORWARD, 0, PERCENT))
        controller.buttonL2.pressed(donut_elevator.spin, (REVERSE, DONUT_ELEVATOR_REVERSE_SPEED, PERCENT))
        controller.buttonL2.released(donut_elevator.spin, (FORWARD, 0, PERCENT))

        # Parthib requested that this be added.
        controller.buttonY.pressed(toggle_donut_elevator)

    if NAME == "BARRON":
        controller.buttonL1.pressed(claw_lift.spin, (FORWARD, 100, PERCENT))
        controller.buttonL1.released(claw_lift.spin, (FORWARD, 0, PERCENT))
        controller.buttonL2.pressed(claw_lift.spin, (REVERSE, 100, PERCENT))
        controller.buttonL2.pressed(claw_lift.spin, (FORWARD, 0, PERCENT))

        controller.buttonR1.pressed(claw_claw.spin, (FORWARD, 100, PERCENT))
        controller.buttonR1.released(claw_claw.spin, (0, PERCENT))
        controller.buttonR2.pressed(claw_claw.spin, (REVERSE, 100, PERCENT))
        controller.buttonR2.pressed(claw_claw.spin, (FORWARD, 0, PERCENT))
    
    controller.buttonX.pressed(stop_everything)


def auton():
    global drivetrain, stake_piston

    drivetrain.set_stopping(BRAKE)
    stake_piston.set(False)
    donut_elevator.set_velocity(80, PERCENT)
    donut_elevator.spin(FORWARD)
    drivetrain.drive_for(FORWARD, 250, INCHES)
    donut_elevator.set_velocity(0, PERCENT)

    stop_everything()
    # wait(5, SECONDS)
    
controller_clear_counter = 0

velocity = 0
accel_stick = 0
turn_stick = 0
target_velocity = 0
turning_velocity = 0

def loop():

    global velocity, accel_stick, turn_stick, target_velocity, turn_velocity
    global controller, left_group, right_group

    # Update state
    velocity = (left_group.velocity(PERCENT) + right_group.velocity(PERCENT)) / 2

    accel_stick = controller.axis3.position()
    turn_stick = controller.axis1.position()
        
    target_velocity = get_velocity(accel_stick, velocity)
    turn_velocity = get_velocity(turn_stick, 100)
    
    global controller_clear_counter
    controller_clear_counter += 1
    if (controller_clear_counter == 10):
        controller.screen.clear_screen()
        
    # Update controller screen

    left_velocity = limit(target_velocity + turn_velocity/2) * VEL_PERCENT / 100
    right_velocity = limit(target_velocity - turn_velocity/2) * VEL_PERCENT / 100

    left_group.spin(FORWARD, left_velocity, PERCENT)
    right_group.spin(FORWARD, right_velocity, PERCENT)
    

#endregion Main routines

if __name__ == "__main__":

    init()
    """
    if AUTON_TESTING:
        while running:
            auton()
    else:
        while running:
            loop()
    """

    comp = Competition(lambda: None, lambda: None)
    
    while comp.is_autonomous() and running:
        auton()
    
    while comp.is_driver_control() and running:
        loop()