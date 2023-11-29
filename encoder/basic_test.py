import smbus
import time

bus = smbus.SMBus(1)  # 1 indicates /dev/i2c-1
address = 0x40 #AS5048B I2C address

def read_angle():
    # Read two bytes of data from the registers 0xFE and 0xFF
    msb = bus.read_byte_data(address, 0xFE)
    lsb = bus.read_byte_data(address, 0xFF)
    
    # Combine the two bytes to create a 14-bit angle value
    angle = ((msb & 0x3F) << 8) | lsb
    return angle

while True:
    angle = read_angle()
    print("Angle: ", angle)
    time.sleep(1)