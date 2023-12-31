import board
import busio
import adafruit_lsm9ds1
import math
import time

#Code with filter

# Initialize the I2C bus
i2c = board.I2C()  # uses board.SCL and board.SDA

sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)

# Optional: Set the sensor to your preferred settings
sensor.accel_range = adafruit_lsm9ds1.ACCELRANGE_2G
sensor.gyro_scale = adafruit_lsm9ds1.GYROSCALE_245DPS

# Calibration period (in seconds)
calibration_duration = 15  # Adjust this as needed

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

# Complementary filter parameters
alpha = 0.98  # Complementary filter coefficient

print("Calibration complete. Begin reading angles...")

# Initialize angle variables
angle_pitch = 0.0
angle_roll = 0.0

previous_time = time.monotonic()

while True:
    current_time = time.monotonic()
    elapsed_time = current_time - previous_time

    # Read accelerometer and gyroscope data
    accel_x, accel_y, accel_z = sensor.acceleration
    gyro_x, gyro_y, gyro_z = sensor.gyro

    # Subtract the calibration offset from gyro readings
    gyro_x -= calibration_data["gyro_total"][0]
    gyro_y -= calibration_data["gyro_total"][1]
    gyro_z -= calibration_data["gyro_total"][2]

    # Calculate pitch and roll from accelerometer
    pitch_acc = math.atan2(accel_x, math.sqrt(accel_y * accel_y + accel_z * accel_z)) * (180 / math.pi)
    roll_acc = math.atan2(accel_y, accel_z) * (180 / math.pi)

    # Calculate pitch and roll from gyroscope
    pitch_gyro = angle_pitch + gyro_x * elapsed_time
    roll_gyro = angle_roll + gyro_y * elapsed_time

    # Apply the complementary filter
    angle_pitch = alpha * pitch_gyro + (1 - alpha) * pitch_acc
    angle_roll = alpha * roll_gyro + (1 - alpha) * roll_acc

    #print("Pitch: {:.2f} degrees, Roll: {:.2f} degrees".format(angle_pitch, angle_roll))
    print(" Roll: {:.2f} degrees".format(angle_roll))

    previous_time = current_time



#This code works well but has no filter
"""
# Initialize the I2C bus
i2c = board.I2C()  # uses board.SCL and board.SDA

sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)

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

    print("Pitch: {:.2f} degrees, Roll: {:.2f} degrees, Yaw: {:.2f} degrees".format(pitch, roll, yaw))

"""