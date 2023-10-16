import board
import busio
import adafruit_lsm9ds1
import math
import time
import threading

# Declare previous_time, angle_pitch, and angle_roll as global variables
global previous_time
global angle_pitch
global angle_roll

# Initialize the I2C bus
i2c = board.I2C()
sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)

# Optional: Set the sensor to your preferred settings
sensor.accel_range = adafruit_lsm9ds1.ACCELRANGE_2G
sensor.gyro_scale = adafruit_lsm9ds1.GYROSCALE_245DPS

# Calibration period (in seconds)
calibration_duration = 15  
print("Calibrating LSM9DS1. Please keep the sensor stable...")
calibration_data = {"gyro_total": [0, 0, 0], "sample_count": 0}

start_time = time.monotonic()
while time.monotonic() - start_time < calibration_duration:
    gyro_x, gyro_y, gyro_z = sensor.gyro
    calibration_data["gyro_total"][0] += gyro_x
    calibration_data["gyro_total"][1] += gyro_y
    calibration_data["gyro_total"][2] += gyro_z
    calibration_data["sample_count"] += 1

calibration_data["gyro_total"][0] /= calibration_data["sample_count"]
calibration_data["gyro_total"][1] /= calibration_data["sample_count"]
calibration_data["gyro_total"][2] /= calibration_data["sample_count"]

# Complementary filter parameters
alpha = 0.98

print("Calibration complete. Begin reading angles...")

# Initialize angle variables and previous time
previous_time = time.monotonic()
angle_pitch = 0.0
angle_roll = 0.0

# Create a lock to ensure thread safety when printing
print_lock = threading.Lock()

def read_and_print_roll():
    global previous_time
    global angle_pitch
    global angle_roll

    read_count = 0
    rate_time = time.monotonic()

    while True:
        current_time = time.monotonic()
        elapsed_time = current_time - previous_time

        accel_x, accel_y, accel_z = sensor.acceleration
        gyro_x, gyro_y, gyro_z = sensor.gyro

        gyro_x -= calibration_data["gyro_total"][0]
        gyro_y -= calibration_data["gyro_total"][1]
        gyro_z -= calibration_data["gyro_total"][2]

        pitch_acc = math.atan2(accel_x, math.sqrt(accel_y * accel_y + accel_z * accel_z)) * (180 / math.pi)
        roll_acc = math.atan2(accel_y, accel_z) * (180 / math.pi)

        pitch_gyro = angle_pitch + gyro_x * elapsed_time
        roll_gyro = angle_roll + gyro_y * elapsed_time

        angle_pitch = alpha * pitch_gyro + (1 - alpha) * pitch_acc
        angle_roll = alpha * roll_gyro + (1 - alpha) * roll_acc

        read_count += 1
        if time.monotonic() - rate_time >= 10:
            rate = read_count / 10
            with print_lock:
                print("\rRoll: {:.2f} degrees, IMU read rate: {:.2f} Hz".format(angle_roll, rate), end="")
            read_count = 0
            rate_time = time.monotonic()

        previous_time = current_time
        time.sleep(0.01)

# Create a thread for reading and printing the roll angle
read_thread = threading.Thread(target=read_and_print_roll)
read_thread.start()
