import board
import busio
import adafruit_lsm9ds1
import math
import time
import socketio

sio = socketio.Client()

def initialize_imu():
    """Initialize IMU settings."""
    i2c = board.I2C()
    sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)
    sensor.accel_range = adafruit_lsm9ds1.ACCELRANGE_2G
    sensor.gyro_scale = adafruit_lsm9ds1.GYROSCALE_245DPS
    return sensor

def calibrate_imu(sensor):
    """Calibrate IMU gyro readings."""
    calibration_duration = 5
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

    print("Calibration complete.")
    return calibration_data

# Define global variables
previous_time = time.monotonic()
angle_pitch = 0.0
angle_roll = 0.0

def get_imu_angles(sensor, calibration_data):
    global previous_time, angle_pitch, angle_roll  # Indicate that we're using the global variables
    """Read IMU angles and return them."""
    alpha = 0.98

    current_time = time.monotonic()
    elapsed_time = current_time - previous_time
    accel_x, accel_y, accel_z = sensor.acceleration
    gyro_x, gyro_y, gyro_z = sensor.gyro

    for i in range(3):
        gyro_x -= calibration_data["gyro_total"][i]
        gyro_y -= calibration_data["gyro_total"][i]
        gyro_z -= calibration_data["gyro_total"][i]

    pitch_acc = math.degrees(math.atan2(accel_x, math.sqrt(accel_y * accel_y + accel_z * accel_z)))
    roll_acc = math.degrees(math.atan2(accel_y, accel_z))

    pitch_gyro = angle_pitch + (gyro_x * elapsed_time)
    roll_gyro = angle_roll + (gyro_y * elapsed_time)

    angle_pitch = alpha * pitch_gyro + (1 - alpha) * pitch_acc
    angle_roll = alpha * roll_gyro + (1 - alpha) * roll_acc

    previous_time = current_time  # Update the global variable at the end

    return angle_pitch, angle_roll


#----------------------Websocket Functions START-----------------------------------------------------------------

def connect_to_websocket(server_ip, server_port):
    """Connect to WebSocket server."""
    sio.connect(f'http://{server_ip}:{server_port}')
    print("Successfully connected to the WebSocket server.")



def send_data_via_websocket(data):
    """Send IMU data through the WebSocket."""
    try:
        sio.emit('imu_data', data)
        #print(f"Sent data: {data}")  # Debugging print
    except Exception as e:
        print(f"Failed to send data through WebSocket. Error: {e}")

#----------------------Websocket Functions END-----------------------------------------------------------------


def main():
    """Main execution function."""
    imu_sensor = initialize_imu()
    imu_calibration_data = calibrate_imu(imu_sensor)
    connect_to_websocket('192.168.1.2', 5025)
    
    while True:
        pitch, roll = get_imu_angles(imu_sensor, imu_calibration_data)
        print(f"Pitch: {pitch:.2f} degrees, Roll: {roll:.2f} degrees")
        data = {'pitch': pitch, 'roll': roll}
        send_data_via_websocket(data)
    
    sio.wait()


if __name__ == "__main__":
    main()



"""


def initialize_imu():
    # Initialize the I2C bus
    i2c = board.I2C()
    sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)

    # Optional: Set sensor settings
    sensor.accel_range = adafruit_lsm9ds1.ACCELRANGE_2G
    sensor.gyro_scale = adafruit_lsm9ds1.GYROSCALE_245DPS

    return sensor

def calibrate_imu(sensor):
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

    print("Calibration complete.")
    return calibration_data

def get_imu_angles(sensor, calibration_data):
    alpha = 0.98
    angle_pitch = angle_roll = 0.0
    previous_time = time.monotonic()

    while True:
        current_time = time.monotonic()
        elapsed_time = current_time - previous_time
        accel_x, accel_y, accel_z = sensor.acceleration
        gyro_x, gyro_y, gyro_z = sensor.gyro

        for i in range(3):
            gyro_x -= calibration_data["gyro_total"][i]
            gyro_y -= calibration_data["gyro_total"][i]
            gyro_z -= calibration_data["gyro_total"][i]

        pitch_acc = math.atan2(accel_x, math.sqrt(accel_y * accel_y + accel_z * accel_z)) * (180 / math.pi)
        roll_acc = math.atan2(accel_y, accel_z) * (180 / math.pi)

        pitch_gyro = angle_pitch + gyro_x * elapsed_time
        roll_gyro = angle_roll + gyro_y * elapsed_time

        angle_pitch = alpha * pitch_gyro + (1 - alpha) * pitch_acc
        angle_roll = alpha * roll_gyro + (1 - alpha) * roll_acc

        print(f"Pitch: {angle_pitch:.2f} degrees, Roll: {angle_roll:.2f} degrees")
        previous_time = current_time
        time.sleep(1)

if __name__ == "__main__":
    imu_sensor = initialize_imu()
    imu_calibration_data = calibrate_imu(imu_sensor)
    get_imu_angles(imu_sensor, imu_calibration_data)




"""