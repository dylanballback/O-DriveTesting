import can
import struct
import threading
import time
import math
import board
import busio
import adafruit_lsm9ds1

node_id = 0

def initialize_imu():
    """
    Initializes the IMU sensor and returns it.
    """
    i2c = board.I2C()
    sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)
    sensor.accel_range = adafruit_lsm9ds1.ACCELRANGE_2G
    sensor.gyro_scale = adafruit_lsm9ds1.GYROSCALE_245DPS
    return sensor

def calibrate_imu(sensor, calibration_duration=15):
    """
    Calibrates the IMU sensor over the specified duration and returns the calibration data.
    """
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

    print("Calibration complete.")
    return calibration_data

sensor = initialize_imu()
calibration_data = calibrate_imu(sensor)

bus = can.interface.Bus("can0", bustype="socketcan")

# IMU Variables
previous_time = time.monotonic()
angle_pitch = 0.0
angle_roll = 0.0
alpha = 0.98

# Global flag to manage threads
running = True

# Set motor velocity to sin wave
def set_vel():
    t = 0
    while running:
        velocity = math.sin(t)
        bus.send(can.Message(
            arbitration_id=(node_id << 5 | 0x0d),
            data=struct.pack('<ff', float(velocity), 0.0),
            is_extended_id=False
        ))
        t += 0.1
        time.sleep(0.1)

# Print encoder feedback and IMU roll angle
def get_pos_vel_and_imu_roll():
    global previous_time  # Make sure we're using the global variable
    last_print_time = time.time()
    read_count = 0
    while running:
        current_time = time.monotonic()
        elapsed_time = current_time - previous_time
        
        # Get IMU data
        accel_x, accel_y, accel_z = sensor.acceleration
        gyro_x, gyro_y, gyro_z = sensor.gyro
        pitch_acc = math.atan2(accel_x, math.sqrt(accel_y * accel_y + accel_z * accel_z)) * (180 / math.pi)
        roll_acc = math.atan2(accel_y, accel_z) * (180 / math.pi)
        pitch_gyro = angle_pitch + gyro_x * elapsed_time
        roll_gyro = angle_roll + gyro_y * elapsed_time
        angle_pitch = alpha * pitch_gyro + (1 - alpha) * pitch_acc
        angle_roll = alpha * roll_gyro + (1 - alpha) * roll_acc
        
        # Check messages for motor data
        msg = bus.recv(timeout=0.01)
        if msg and msg.arbitration_id == (node_id << 5 | 0x09):
            pos, vel = struct.unpack('<ff', bytes(msg.data))
            print(f"Roll: {angle_roll:.2f} degrees, IMU Speed: {read_count/10:.2f} Hz, pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")

            read_count += 1
            if time.time() - last_print_time >= 10:
                last_print_time = time.time()
                read_count = 0

        previous_time = current_time

try:
    # Start the threads
    vel_thread = threading.Thread(target=set_vel)
    data_thread = threading.Thread(target=get_pos_vel_and_imu_roll)
    
    vel_thread.start()
    data_thread.start()

    # Join the threads (or handle in another manner if you prefer)
    vel_thread.join()
    data_thread.join()

except KeyboardInterrupt:
    running = False
    vel_thread.join()
    data_thread.join()
    
    # Close the CAN bus connection (if necessary)
    bus.shutdown()
