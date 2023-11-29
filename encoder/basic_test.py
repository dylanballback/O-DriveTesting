import smbus
import time

bus = smbus.SMBus(2)  # 1 indicates /dev/i2c-1
address = 0x50# AS5048A I2C address

def read_register(reg):
    return bus.read_byte_data(address, reg)

def read_angle():
    data = bus.read_i2c_block_data(address, 0xFE, 2)
    return (data[0] << 6) | (data[1] & 0x3F)

def diagnose_sensor():
    agc = read_register(0xFA)  # Automatic Gain Control register
    diag = read_register(0xFB)  # Diagnostics register
    print(f"AGC: {agc}, DIAG: {diag}")

while True:
    angle_raw = read_angle()
    angle_degrees = (angle_raw / float(0x3FFF)) * 360.0
    print(f"Raw angle value: {angle_raw}, Angle in degrees: {angle_degrees:.2f}")
    diagnose_sensor()
    time.sleep(0.1)