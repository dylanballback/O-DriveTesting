import smbus
import time

bus = smbus.SMBus(2)  # 1 indicates /dev/i2c-1
address = 0x40# AS5048A I2C address

def read_angle():
    # Read the angle value from the sensor
    data = bus.read_i2c_block_data(address, 0xFE, 2)
    # Combine the MSB and LSB into a single 14-bit value
    angle = (data[0] << 6) | (data[1] & 0x3F)
    return angle

while True:
    angle_raw = read_angle()
    # Convert the raw angle to degrees
    angle_degrees = (angle_raw / float(0x3FFF)) * 360.0
    print(f"Raw angle value: {angle_raw}, Angle in degrees: {angle_degrees:.2f}")
    time.sleep(0.1)  # Sleep for 100ms