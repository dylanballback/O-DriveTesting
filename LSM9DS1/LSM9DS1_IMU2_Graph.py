import board
import busio
import adafruit_lsm9ds1
import math
import time
import matplotlib.pyplot as plt
import numpy as np

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

# Complementary filter parameters
alpha = 0.98  # Complementary filter coefficient

print("Calibration complete. Begin reading angles...")

# Initialize angle variables
angle_roll = 0.0

previous_time = time.monotonic()

# Initialize lists for storing roll values for plotting
max_data_points = 100  # Maximum number of data points to display
roll_values = [0] * max_data_points
time_values = np.linspace(0, 10, max_data_points)

plt.ion()  # Turn on interactive mode for live plotting

while True:
    current_time = time.monotonic()
    elapsed_time = current_time - previous_time

    # Read accelerometer and gyroscope data
    gyro_x, gyro_y, gyro_z = sensor.gyro

    # Subtract the calibration offset from gyro readings
    gyro_x -= calibration_data["gyro_total"][0]

    # Calculate roll from gyroscope
    roll_gyro = angle_roll + gyro_y * elapsed_time

    # Apply the complementary filter
    angle_roll = alpha * roll_gyro + (1 - alpha) * angle_roll

    # Append roll values for plotting
    roll_values.append(angle_roll)
    roll_values = roll_values[1:]  # Remove the oldest value

    # Clear the terminal and plot the roll values
    plt.clf()
    plt.plot(time_values, roll_values)
    plt.xlabel("Time")
    plt.ylabel("Roll Angle (degrees)")
    plt.pause(0.01)  # Update the plot

    previous_time = current_time
