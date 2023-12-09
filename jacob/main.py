import time
from ODriveCAN import ODriveCAN


# Initialize ODriveCAN for 1st Motor 
odrive1 = ODriveCAN(0)
odrive1.initCanBus()

# Initialize ODriveCAN for 2nd Motor 
#odrive2 = ODriveCAN(1)
#odrive2.initCanBus()

def set_motors_vel(target_vel):
    odrive1.set_velocity(target_vel)
    motor2_target_vel = 0.5 * target_vel
    odrive2.set_velocity(motor2_target_vel)
    print(f"Set Motor 1 to {target_vel} turn/s, Motor 2 to {motor2_target_vel} turns/s")

try:
    while True:
        odrive.set_velocity(3)
        pos, vel = odrive.get_encoder_estimate_rtr()
        print(f"ODrive 1 velocity = {vel} turn/s")
except KeyboardInterrupt:
    odrive.set_velocity(0)
    print("Program interrupted by user. Exiting.")