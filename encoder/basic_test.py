import smbus
import time

bus = smbus.SMBus(1)  # 1 indicates /dev/i2c-1
address = 0x40  # AS5048A I2C address

def read_angle():
    data = bus.read_i2c_block_data(address, 0xFF, 2)
    angle = (data[0] << 8) | data[1]
    angle = angle & 0x3FFF  # 14-bit angle
    return angle

while True:
    angle = read_angle()
    print("Angle: ", angle)
    time.sleep(1)
