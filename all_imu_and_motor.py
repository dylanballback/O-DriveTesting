import board
import busio
import adafruit_lsm9ds1
import math
import time
import threading
import can
import struct

# LSM9DS1 Initialization
i2c = board.I2C()
sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)

sensor.accel_range = adafruit_lsm9ds1.ACCELRANGE_2G
sensor.gyro_scale = adafruit_lsm9ds1.GYROSCALE_245DPS

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

alpha = 0.98
print("Calibration complete. Begin reading angles...")

previous_time = time.monotonic()
angle_pitch = 0.0
angle_roll = 0.0
print_lock = threading.Lock()

def read_and_print_roll():
    global previous_time
    global angle_pitch
    global angle_roll
    while True:
        current_time = time.monotonic()
        elapsed_time = current_time - previous_time
        accel_x, accel_y, accel_z = sensor.acceleration
        gyro_x, gyro_y, gyro_z = sensor.gyro
        for i in range(3):
            calibration_data["gyro_total"][i] -= calibration_data["gyro_total"][i]

        pitch_acc = math.atan2(accel_x, math.sqrt(accel_y * accel_y + accel_z * accel_z)) * (180 / math.pi)
        roll_acc = math.atan2(accel_y, accel_z) * (180 / math.pi)
        pitch_gyro = angle_pitch + gyro_x * elapsed_time
        roll_gyro = angle_roll + gyro_y * elapsed_time

        angle_pitch = alpha * pitch_gyro + (1 - alpha) * pitch_acc
        angle_roll = alpha * roll_gyro + (1 - alpha) * roll_acc

        with print_lock:
            print("Roll: {:.2f} degrees".format(angle_roll))

        previous_time = current_time

roll_thread = threading.Thread(target=read_and_print_roll)
roll_thread.start()

# CAN Initialization for ODrive
node_id = 0
bus = can.interface.Bus("can0", bustype="socketcan")

while not (bus.recv(timeout=0) is None): pass

bus.send(can.Message(
    arbitration_id=(node_id << 5 | 0x07),
    data=struct.pack('<I', 8),
    is_extended_id=False
))

for msg in bus:
    if msg.arbitration_id == (node_id << 5 | 0x01):
        error, state, result, traj_done = struct.unpack('<IBBB', bytes(msg.data[:7]))
        if state == 8:
            break

def set_vel():
    while True:
        for vel_set in range(11):
            bus.send(can.Message(
                arbitration_id=(node_id << 5 | 0x0d),
                data=struct.pack('<ff', float(vel_set), 0.0),
                is_extended_id=False
            ))
            time.sleep(0.25)
        for vel_set in range(10, -1, -1):
            bus.send(can.Message(
                arbitration_id=(node_id << 5 | 0x0d),
                data=struct.pack('<ff', float(vel_set), 0.0),
                is_extended_id=False
            ))
            time.sleep(0.25)

def get_pos_vel():
    while True:
        for msg in bus:
            if msg.arbitration_id == (node_id << 5 | 0x09):
                pos, vel = struct.unpack('<ff', bytes(msg.data))
                print(f"pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")

vel_thread = threading.Thread(target=set_vel)
pos_thread = threading.Thread(target=get_pos_vel)

vel_thread.start()
pos_thread.start()
