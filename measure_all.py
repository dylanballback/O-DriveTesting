import board
import busio
import adafruit_lsm9ds1
import math
import time
import threading
import can
import struct

# IMU initialization
i2c = board.I2C()
sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)
sensor.accel_range = adafruit_lsm9ds1.ACCELRANGE_2G
sensor.gyro_scale = adafruit_lsm9ds1.GYROSCALE_245DPS

# CAN initialization
node_id = 0
bus = can.interface.Bus("can0", bustype="socketcan")
while not (bus.recv(timeout=0) is None): pass
bus.send(can.Message(arbitration_id=(node_id << 5 | 0x07), data=struct.pack('<I', 8), is_extended_id=False))
for msg in bus:
    if msg.arbitration_id == (node_id << 5 | 0x01):
        error, state, result, traj_done = struct.unpack('<IBBB', bytes(msg.data[:7]))
        if state == 8:
            break

# Global variables
previous_time = time.monotonic()
angle_pitch = 0.0
angle_roll = 0.0
imu_rate_time = time.monotonic()
imu_read_count = 0
imu_read_rate = 0
running = True

# IMU Calibration
print("Calibrating LSM9DS1. Please keep the sensor stable...")
calibration_duration = 15
calibration_data = {"gyro_total": [0, 0, 0], "sample_count": 0}
start_time = time.monotonic()
while time.monotonic() - start_time < calibration_duration:
    gyro_x, gyro_y, gyro_z = sensor.gyro
    calibration_data["gyro_total"][0] += gyro_x
    calibration_data["gyro_total"][1] += gyro_y
    calibration_data["gyro_total"][2] += gyro_z
    calibration_data["sample_count"] += 1
for i in range(3):
    calibration_data["gyro_total"][i] /= calibration_data["sample_count"]

print("Calibration complete. Begin reading angles...")

def read_and_print_roll():
    global previous_time, angle_pitch, angle_roll, imu_read_count, imu_rate_time, imu_read_rate
    alpha = 0.98
    while running:
        current_time = time.monotonic()
        elapsed_time = current_time - previous_time

        accel_x, accel_y, accel_z = sensor.acceleration
        gyro_x, gyro_y, gyro_z = sensor.gyro

        # Subtract the calibration offset from gyro readings
        gyro_x -= calibration_data["gyro_total"][0]
        gyro_y -= calibration_data["gyro_total"][1]
        gyro_z -= calibration_data["gyro_total"][2]

        # Calculate pitch and roll from accelerometer
        pitch_acc = math.atan2(accel_x, math.sqrt(accel_y * accel_y + accel_z * accel_z)) * (180 / math.pi)
        roll_acc = math.atan2(accel_y, accel_z) * (180 / math.pi)

        pitch_gyro = angle_pitch + gyro_x * elapsed_time
        roll_gyro = angle_roll + gyro_y * elapsed_time

        angle_pitch = alpha * pitch_gyro + (1 - alpha) * pitch_acc
        angle_roll = alpha * roll_gyro + (1 - alpha) * roll_acc

        previous_time = current_time

        imu_read_count += 1

        # Update the read rate every 10 seconds
        if current_time - imu_rate_time >= 10:
            imu_read_rate = imu_read_count / 10
            imu_read_count = 0
            imu_rate_time = current_time

def set_vel(velocity):
    while running:
        bus.send(can.Message(arbitration_id=(node_id << 5 | 0x0d), data=struct.pack('<ff', float(velocity), 0.0), is_extended_id=False))
        time.sleep(0.1)

def get_pos_vel():
    global angle_roll, imu_read_rate
    while running:
        for msg in bus:
            if msg.arbitration_id == (node_id << 5 | 0x09):
                pos, vel = struct.unpack('<ff', bytes(msg.data))
                print(f"Roll: {angle_roll:.2f} degrees, IMU Rate: {imu_read_rate:.2f} Hz, pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")

# Threads
imu_thread = threading.Thread(target=read_and_print_roll)
vel_thread = threading.Thread(target=set_vel, args=(10,))
pos_thread = threading.Thread(target=get_pos_vel)

imu_thread.start()
vel_thread.start()
pos_thread.start()

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    running = False
    bus.shutdown()
    print("\nProgram terminated gracefully.")
