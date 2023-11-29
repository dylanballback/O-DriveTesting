import smbus
import time

bus = smbus.SMBus(2)  # 1 indicates /dev/i2c-1
address = 0x50# AS5048A I2C address

def read_angle():
    # Read the angle value from the sensor
    word_data = bus.read_word_data(address, 0xFE)
    # Reorder the bytes in the correct endianness
    msb = (word_data & 0xFF00) >> 8
    lsb = (word_data & 0x00FF)
    # Combine the MSB and LSB into a single 14-bit value
    angle = (msb << 6) | (lsb & 0x3F)
    return angle

while True:
    angle_raw = read_angle()
    # Convert the raw angle to degrees
    angle_degrees = (angle_raw / float(0x3FFF)) * 360.0
    print(f"Raw angle value: {angle_raw}, Angle in degrees: {angle_degrees:.2f}")
    time.sleep(0.1)  # Sleep for 100ms