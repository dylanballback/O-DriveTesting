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

def read_magnetometer():
    x = read_word_2c(0x28)
    y = read_word_2c(0x2A)
    z = read_word_2c(0x2C)
    return x, y, z

def calculate_yaw_pitch_roll(gyro_data, accel_data, mag_data, accel_offset, mag_offset):
    gyro_scale = 245  # 245 degrees per second for the gyroscope
    accel_scale = 4  # 4 g for the accelerometer
    mag_scale = 4  # 4 gauss for the magnetometer

    gx, gy, gz = [(x * gyro_scale / 32768.0) for x in gyro_data]
    ax, ay, az = [(x * accel_scale / 32768.0) - offset for x, offset in zip(accel_data, accel_offset)]
    mx, my, mz = [(x * mag_scale / 32768.0) - offset for x, offset in zip(mag_data, mag_offset)]

    roll = math.atan2(ay, az)
    pitch = math.atan2(-ax, math.sqrt(ay ** 2 + az ** 2))

    # Yaw calculation using magnetometer data
    yaw = math.atan2(
        (mx * math.cos(roll) + my * math.sin(roll)),
        (mx * math.cos(pitch) * math.sin(roll) + my * math.cos(pitch) * math.cos(roll) - mz * math.sin(pitch))
    )

    # Convert to degrees
    roll = math.degrees(roll)
    pitch = math.degrees(pitch)
    yaw = math.degrees(yaw)

    return roll, pitch, yaw

def calibrate_sensors():
    print("Calibrating sensors. Keep the IMU still...")
    accel_offset = [0, 0, 0]
    mag_offset = [0, 0, 0]

    # Gather data for calibration
    for _ in range(1000):
        accel_data = read_acceleration()
        mag_data = read_magnetometer()
        accel_offset = [a + x for a, x in zip(accel_data, accel_offset)]
        mag_offset = [m + x for m, x in zip(mag_data, mag_offset)]
        time.sleep(0.01)

    accel_offset = [x / 1000 for x in accel_offset]
    mag_offset = [x / 1000 for x in mag_offset]
    
    return accel_offset, mag_offset

def main():
    bus.write_byte_data(LSM9DS1_ADDRESS, CTRL_REG1_G, 0x0F)  # Enable gyroscope
    bus.write_byte_data(LSM9DS1_ADDRESS, CTRL_REG6_XL, 0x0F)  # Enable accelerometer
    bus.write_byte_data(LSM9DS1_ADDRESS, CTRL_REG5_XL, 0x38)  # Accelerometer at 416Hz
    bus.write_byte_data(LSM9DS1_ADDRESS, CTRL_REG8, 0x04)  # Enable BDU

    accel_offset, mag_offset = calibrate_sensors()
    print("Calibration complete.")

    while True:
        gyro_data = read_gyro()
        accel_data = read_acceleration()
        mag_data = read_magnetometer()
        roll, pitch, yaw = calculate_yaw_pitch_roll(gyro_data, accel_data, mag_data, accel_offset, mag_offset)
        print(f"Roll: {roll:.2f} degrees, Pitch: {pitch:.2f} degrees, Yaw: {yaw:.2f} degrees")
        time.sleep(0.1)

if __name__ == '__main__':
    main()
