import time
from ODriveCAN import ODriveCAN


# Initialize ODriveCAN and database
odrive = ODriveCAN(0)
odrive.initCanBus()


try:
    odrive.set_velocity(3)
except KeyboardInterrupt:
    odrive.set_velocity(0)
    print("Program interrupted by user. Exiting.")