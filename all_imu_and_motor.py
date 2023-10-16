import board
import busio
import adafruit_lsm9ds1
import math
import time
import threading
import can
import struct

# Declare previous_time, angle_pitch, and angle_roll as global variables
global previous_time
global angle_pitch
global angle_roll

# Initialize the I2C bus
i2c = board.I2C()  
sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)

sensor.accel_range = adafruit_lsm9ds1.ACCELRANGE_2G
sensor.gyro_scale = adafruit_lsm9ds1.GYROSCALE_245DPS

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
for i in range(3):
    calibration_data["gyro_total"][i] /= calibration_data["sample_count"]

alpha = 0.98

print("Calibration complete. Begin reading angles...")

angle_pitch = 0.0
angle_roll = 0.0
previous_time = time.monotonic()
print_lock = threading.Lock()

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
        previous_time = current_time
        msg = bus.recv(timeout=1)
        if msg and msg.arbitration_id == (node_id << 5 | 0x09):
            pos, vel = struct.unpack('<ff', bytes(msg.data))
            with print_lock:
                print(f"Roll: {angle_roll:.2f} degrees, pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")

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

roll_thread = threading.Thread(target=read_and_print_roll)
vel_thread = threading.Thread(target=set_vel)

roll_thread.start()
vel_thread.start()
