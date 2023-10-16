import smbus
import time
import math

# LSM9DS1 I2C address
LSM9DS1_ADDRESS = 0x6b

# Register addresses for LSM9DS1
CTRL_REG1_G = 0x10
CTRL_REG6_XL = 0x20
CTRL_REG5_XL = 0x1F
CTRL_REG8 = 0x22

OUT_X_L_G = 0x18
OUT_X_L_XL = 0x28
OUT_X_H_XL = 0x29
OUT_Y_L_XL = 0x2A
OUT_Y_H_XL = 0x2B
OUT_Z_L_XL = 0x2C
OUT_Z_H_XL = 0x2D

# Initialize the I2C bus and LSM9DS1
bus = smbus.SMBus(1)

def read_word_2c(addr):
    high = bus.read_byte_data(LSM9DS1_ADDRESS, addr)
    low = bus.read_byte_data(LSM9DS1_ADDRESS, addr + 1)
    val = (high << 8) + low
    if val >= 0x8000:
        return -((65535 - val) + 1)
    else:
        return val

def read_gyro():
    x = read_word_2c(OUT_X_L_G)
    y = read_word_2c(OUT_Y_L_XL)
    z = read_word_2c(OUT_Z_L_XL)
    return x, y, z

def read_acceleration():
    x = read_word_2c(OUT_X_L_XL)
    y = read_word_2c(OUT_Y_L_XL)
    z = read_word_2c(OUT_Z_L_XL)
    return x, y, z

def calculate_pitch_roll(gyro_data, accel_data):
    gyro_scale = 245  # 245 degrees per second for the gyroscope
    accel_scale = 4  # 4 g for the accelerometer

    gx, gy, gz = gyro_data
    ax, ay, az = accel_data

    roll = math.atan2(ay, az)
    pitch = math.atan2(-ax, math.sqrt(ay ** 2 + az ** 2))

    return math.degrees(roll), math.degrees(pitch)

def main():
    bus.write_byte_data(LSM9DS1_ADDRESS, CTRL_REG1_G, 0x0F)  # Enable gyroscope
    bus.write_byte_data(LSM9DS1_ADDRESS, CTRL_REG6_XL, 0x0F)  # Enable accelerometer
    bus.write_byte_data(LSM9DS1_ADDRESS, CTRL_REG5_XL, 0x38)  # Accelerometer at 416Hz
    bus.write_byte_data(LSM9DS1_ADDRESS, CTRL_REG8, 0x04)  # Enable BDU

    while True:
        gyro_data = read_gyro()
        accel_data = read_acceleration()
        roll, pitch = calculate_pitch_roll(gyro_data, accel_data)
        print(f"Roll: {roll:.2f} degrees, Pitch: {pitch:.2f} degrees")
        time.sleep(0.1)

if __name__ == '__main__':
    main()
