import smbus
import time

bus = smbus.SMBus(2)  # 1 indicates /dev/i2c-1
address = 0x54  # AS5048A I2C address


def read_angle_raw():
    msb = bus.read_byte_data(address, 0xFE)
    lsb = bus.read_byte_data(address, 0xFF)
    return msb, lsb

def convert_to_angle(msb, lsb):
    # Combine the two bytes to create a 14-bit angle value
    # Mask the MSB with 0x3F to get rid of the two most significant non-angle bits
    angle = ((msb & 0x3F) << 8) | lsb
    # Convert the raw sensor reading to degrees (optional)
    angle_in_degrees = (angle / 0x3FFF) * 360.0
    return angle_in_degrees

while True:
    msb, lsb = read_angle_raw()
    angle = convert_to_angle(msb, lsb)
    print(f"Raw MSB: {msb}, Raw LSB: {lsb}, Angle: {angle:.2f} degrees")
    time.sleep(0.1)  # Sleep for 100ms