import board
import busio
import adafruit_lsm9ds1
import math
import time

# Initialize the I2C bus
i2c = board.I2C()  # uses board.SCL and board.SDA

# Initialize the LSM9DS1 sensor
sensor = adafruit_lsm9ds1.LSM9DS1(i2c)

# Optional: Set the sensor to your preferred settings
sensor.accel_range = adafruit_lsm9ds1.ACCELRANGE_2G
sensor.gyro_scale = adafruit_lsm9ds1.GYROSCALE_245DPS

# Calibration period (in seconds)
calibration_duration = 5  # Adjust this as needed

print("Calibrating LSM9DS1. Please keep the sensor stable...")
calibration_data = {"gyro_total": [0, 0, 0], "sample_count": 0}

start_time = time.monotonic()
while time.monotonic() - start_time < calibration_duration:
    gyro_x, gyro_y, gyro_z = sensor.gyro
    calibration_data["gyro_total"][0] += gyro_x
    calibration_data["gyro_total"][1] += gyro_y
    calibration_data["gyro_total"][2] += gyro_z
    calibration_data["sample_count"] += 1

# Calculate the average gyro readings during calibration
calibration_data["gyro_total"][0] /= calibration_data["sample_count"]
calibration_data["gyro_total"][1] /= calibration_data["sample_count"]
calibration_data["gyro_total"][2] /= calibration_data["sample_count"]

print("Calibration complete. Begin reading angles...")

while True:
    # Read accelerometer and gyroscope data
    accel_x, accel_y, accel_z = sensor.acceleration
    gyro_x, gyro_y, gyro_z = sensor.gyro

    # Subtract the calibration offset from gyro readings
    gyro_x -= calibration_data["gyro_total"][0]
    gyro_y -= calibration_data["gyro_total"][1]
    gyro_z -= calibration_data["gyro_total"][2]

    # Calculate pitch, roll, and yaw
    pitch = -1 * (180 / 3.141592) * (math.atan2(accel_x, math.sqrt(accel_y * accel_y + accel_z * accel_z)))
    roll = (180 / 3.141592) * (math.atan2(accel_y, accel_z))
    yaw = (180 / 3.141592) * (math.atan2(accel_z, accel_x))

    print("Pitch: {:.2f} degrees".format(pitch))
    print("Roll: {:.2f} degrees".format(roll))
    print("Yaw: {:.2f} degrees".format(yaw))
