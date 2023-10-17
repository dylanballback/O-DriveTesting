# imu_client.py
import board
import busio
import adafruit_lsm9ds1
import math
import time
from socketIO_client import SocketIO

def initialize_imu():
    i2c = board.I2C()  # uses board.SCL and board.SDA
    sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)

    # Optional: Set the sensor to your preferred settings
    sensor.accel_range = adafruit_lsm9ds1.ACCELRANGE_2G
    sensor.gyro_scale = adafruit_lsm9ds1.GYROSCALE_245DPS
    
    return sensor

def calibrate_imu(sensor):
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

    print("Calibration complete. Begin reading angles...")
    return calibration_data

def get_angles(sensor, calibration_data, previous_time):
    alpha = 0.98  # Complementary filter coefficient

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

    return angle_pitch, angle_roll, current_time

def read_and_send_imu_data():
    sensor = initialize_imu()
    calibration_data = calibrate_imu(sensor)

    global angle_pitch, angle_roll
    angle_pitch = 0.0
    angle_roll = 0.0
    previous_time = time.monotonic()

    while True:
        angle_pitch, angle_roll, previous_time = get_angles(sensor, calibration_data, previous_time)

        data = {
            'roll': angle_roll,
            'pitch': angle_pitch
        }
        socketIO.emit('imu_data', data)
        time.sleep(1)  # Adjust this to your preferred data transmission rate

if __name__ == '__main__':
    with SocketIO('localhost', 5000) as socketIO:  # Adjust the host and port as needed
        read_and_send_imu_data()