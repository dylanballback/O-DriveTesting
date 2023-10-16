
import can
import struct
import threading
import time
import math
import board
import busio
import adafruit_lsm9ds1

# CAN Setup
node_id = 0  # Default
bus = can.interface.Bus("can0", bustype="socketcan")
while not (bus.recv(timeout=0) is None): pass  # Flush CAN RX buffer
bus.send(can.Message(arbitration_id=(node_id << 5 | 0x07), data=struct.pack('<I', 8), is_extended_id=False))

# IMU Setup
i2c = board.I2C()
sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)

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
