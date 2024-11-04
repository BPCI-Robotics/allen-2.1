AUTON_TESTING = True

#region Set up code
from vex import *

from math_tools import *
from telemetry import *

brain = Brain()
controller = Controller(PRIMARY)

left_group = MotorGroup(
                Motor(Ports.PORT1, GearSetting.RATIO_18_1, False),
                Motor(Ports.PORT2, GearSetting.RATIO_18_1, False)
            )

right_group = MotorGroup(
                Motor(Ports.PORT3, GearSetting.RATIO_18_1, True), 
                Motor(Ports.PORT4, GearSetting.RATIO_18_1, True)
            )

donut_elevator = Motor(Ports.PORT10, GearSetting.RATIO_18_1, False)
stake_piston = DigitalOut(brain.three_wire_port.a)
# chain_button = Bumper(brain.three_wire_port.b)
drivetrain = DriveTrain(
    lm=left_group,
    rm=right_group,
    wheelTravel=4 * math.pi,
    trackWidth=300,
    wheelBase=300,
    units=INCHES,
    externalGearRatio=1
)

velocity = 0
accel_stick = 0
turn_stick = 0
target_velocity = 0
turning_velocity = 0

#endregion

def init():
    global controller, left_group, right_group, stake_piston, donut_elevator

    left_group.set_stopping(COAST)
    right_group.set_stopping(COAST)

    # Init callback
    controller.buttonR2.pressed(stake_piston.set, (True,))
    controller.buttonR2.released(stake_piston.set, (False,))

    controller.buttonA.pressed(donut_elevator.spin, (FORWARD, 50, PERCENT))
    controller.buttonA.released(donut_elevator.spin, (FORWARD, 0, PERCENT))
    controller.buttonB.pressed(donut_elevator.spin, (REVERSE, 50, PERCENT))
    controller.buttonB.released(donut_elevator.spin, (FORWARD, 0, PERCENT))


def auton():
    global drivetrain

    drivetrain.drive_for(FORWARD, 1000, MM, 63, PERCENT, True)
    drivetrain.turn_for(LEFT, 90, DEGREES, 63, PERCENT, True)
    

def loop():
    global velocity, accel_stick, turn_stick, target_velocity, turn_velocity
    global controller, left_group, right_group

    # Update state
    velocity = (left_group.velocity(PERCENT) + right_group.velocity(PERCENT)) / 2
    accel_stick = controller.axis2.position()
    turn_stick = controller.axis4.position()
    target_velocity = get_velocity(accel_stick, velocity)
    turn_velocity = get_velocity(turn_stick, 100)

    # Rumble controller when full power being used
    if 51 <= abs(accel_stick) <= 64:
        controller.rumble("--")
    
    # Update controller screen
    controller.screen.clear_screen()
    controller.screen.set_cursor(1, 1)
    controller.screen.print("Turning", turn_velocity)

    left_group.spin(FORWARD, limit(target_velocity + turn_velocity), PERCENT)
    right_group.spin(FORWARD, limit(target_velocity - turn_velocity), PERCENT)


if __name__ == "__main__":
    init()
    if AUTON_TESTING:
        while True:
            loop()
    else:
        while True:
            auton()