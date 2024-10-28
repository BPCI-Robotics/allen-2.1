import math

TAU = 6.283185307179586

GEARS = (12, 24, 36, 48, 60, 72, 84)

BATTERY_CAPACITY = 50400 # J
MOTOR_SPEED = 376.9911 # rad/s
FIELD_LENGTH = 3.658 # m
LADDER_SIZE = 0.8509 # m

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
        if current_speed < 55:
            return sgn * 60
        else:
            return sgn * math.ceil(logistic(val))
    
    return 0

def limit(x: float) -> float:
    sign = 0

    if x == 0:
        return 0
    
    if x < 0:
        sign = -1
    else:
        sign = 1
    
    if sign*x >= 100:
        return sign*100
    else:
        return x

SI_UNITS = {
    # Mass: kg
    "g": 0.001,
    "lb": 0.4536,
    "kg": 1,

    # Time: s
    "s": 1,
    "sec": 1,
    "min": 60,
    "hr": 3600,

    # Distance: m
    "km": 1000,
     "m": 1,
    "dm": 0.1,
    "cm": 0.01,
    "mm": 0.001,

    "in": 0.0254,
    "ft": 0.3048,
    "yd": 0.9144,
    "mi": 1609.34,

    # Velocity: m/s
    "m/s": 1,
    "km/h": 1/3.6,
    "mph": 0.44704,

    # Acceleration: m/s^2
    "gees": 9.80665,
    "km/h/s": 1/3.6,

    # Force
    "gforce": 9.80665,
    "dyne": 1e-5,
    "lbf": 4.44822,

    # Torque: J/rad
    "ft-lbs": 1.3558,
    "J/rad": 1,
    "Nm": 1,
    "J/rev": TAU,

    # Energy: J
    "J": 1,

    # Power: W
    "W": 1,

    # Angular Velocity: rad/s
    "rpm": TAU/60,
    "rps": TAU,

    # Angle: rad
    "deg": TAU/360,
    "rad": 1,

    # Percentages
    "percent": 0.01,
    "decimal": 1
}

def convert(val, unit, to=None):
    if unit not in SI_UNITS:
        raise ValueError(f"{unit} is not valid or has not been implemented.")
    
    if to not in SI_UNITS:
        raise ValueError(f"{to} is not valid or has not been implemented.")
    
    result = val * SI_UNITS[unit]

    if to:
        return result / SI_UNITS[unit]
    else:
        return result