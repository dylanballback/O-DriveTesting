import time
from ODriveCAN import ODriveCAN


# Initialize ODriveCAN for 1st Motor 
odrive1 = ODriveCAN(0)
odrive1.initCanBus()

# Initialize ODriveCAN for 2nd Motor 
odrive2 = ODriveCAN(1)
odrive2.initCanBus()

def get_motor2_velocity()

try:
    while True:
        odrive.set_velocity(3)
        pos, vel = odrive.get_encoder_estimate_rtr()
        print(f"ODrive 1 velocity = {vel} turn/s")
except KeyboardInterrupt:
    odrive.set_velocity(0)
    print("Program interrupted by user. Exiting.")