import board
import busio
import adafruit_lsm9ds1
import math
import time
import threading
import can
import struct

# LSM9DS1 IMU Initialization
i2c = board.I2C()
sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)
sensor.accel_range = adafruit_lsm9ds1.ACCELRANGE_2G
sensor.gyro_scale = adafruit_lsm9ds1.GYROSCALE_245DPS
previous_time = time.monotonic()
angle_pitch = 0.0
angle_roll = 0.0

# CAN Bus Initialization
node_id = 0
bus = can.interface.Bus("can0", bustype="socketcan")
while not (bus.recv(timeout=0) is None): pass
bus.send(can.Message(arbitration_id=(node_id << 5 | 0x07), data=struct.pack('<I', 8), is_extended_id=False))
for msg in bus:
    if msg.arbitration_id == (node_id << 5 | 0x01):
        _, state, _, _ = struct.unpack('<IBBB', bytes(msg.data[:7]))
        if state == 8:
            break

imu_read_count = 0
imu_rate_time = time.monotonic()
imu_read_rate = 0.0
shared_data = {
    "roll": 0.0,
    "imu_rate": 0.0,
    "pos": 0.0,
    "vel": 0.0
}

def read_and_print_roll():
    global previous_time, angle_pitch, angle_roll, imu_read_count, imu_rate_time

    while True:
        # IMU data reading and processing
        current_time = time.monotonic()
        elapsed_time = current_time - previous_time
        accel_x, accel_y, accel_z = sensor.acceleration
        gyro_x, gyro_y, gyro_z = sensor.gyro
        pitch_acc = math.atan2(accel_x, math.sqrt(accel_y * accel_y + accel_z * accel_z)) * (180 / math.pi)
        roll_acc = math.atan2(accel_y, accel_z) * (180 / math.pi)
        pitch_gyro = angle_pitch + gyro_x * elapsed_time
        roll_gyro = angle_roll + gyro_y * elapsed_time
        angle_pitch = pitch_gyro + roll_acc
        angle_roll = roll_gyro + roll_acc
        previous_time = current_time

        imu_read_count += 1
        elapsed = time.monotonic() - imu_rate_time
        if elapsed >= 10.0:
            imu_read_rate = imu_read_count / elapsed
            imu_read_count = 0
            imu_rate_time = time.monotonic()

        shared_data["roll"] = angle_roll
        shared_data["imu_rate"] = imu_read_rate

def set_vel(velocity):
    while True:
        # Motor command sending code
        bus.send(can.Message(
            arbitration_id=(node_id << 5 | 0x0d),
            data=struct.pack('<ff', float(velocity), 0.0),
            is_extended_id=False
        ))
        time.sleep(0.1)

def get_pos_vel():
    while True:
        # Motor data receiving code
        for msg in bus:
            if msg.arbitration_id == (node_id << 5 | 0x09):
                pos, vel = struct.unpack('<ff', bytes(msg.data))
                shared_data["pos"] = pos
                shared_data["vel"] = vel

def printer_thread():
    while True:
        print(f"Roll Angle: {shared_data['roll']:.2f}°, IMU Rate: {shared_data['imu_rate']:.2f}Hz, Motor Pos: {shared_data['pos']:.3f} [turns], Vel: {shared_data['vel']:.3f} [turns/s]")
        time.sleep(0.1)

# Create threads
imu_thread = threading.Thread(target=read_and_print_roll)
vel_thread = threading.Thread(target=set_vel, args=(10,))
pos_thread = threading.Thread(target=get_pos_vel)
print_thread = threading.Thread(target=printer_thread)

# Start threads
imu_thread.start()
vel_thread.start()
pos_thread.start()
print_thread.start()
