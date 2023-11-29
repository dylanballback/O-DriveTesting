import smbus
import time

bus = smbus.SMBus(2)  # 1 indicates /dev/i2c-1
address = 0x50  # AS5048A I2C address

def read_angle():
    # Read two bytes of data from the registers 0xFE and 0xFF
    msb = bus.read_byte_data(address, 0xFE)
    lsb = bus.read_byte_data(address, 0xFF)
    
    # Combine the two bytes to create a 14-bit angle value
    # Mask the MSB with 0x3F to get rid of the two most significant non-angle bits
    angle = ((msb & 0x3F) << 8) | lsb
    # Convert the raw sensor reading to degrees (optional)
    angle_in_degrees = (angle / 0x3FFF) * 360.0
    return angle_in_degrees

while True:
    angle = read_angle()
    print("Angle: {:.2f} degrees".format(angle))
    time.sleep(0.1)  # Sleep for 100ms