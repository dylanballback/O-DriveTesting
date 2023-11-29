import smbus2
import time

"""
11/29/23 This is very basic code to read the angle data of a AS5048B with
I2C and a Raspberry Pi. I am using 3.3v 
"""

# AS5048B I2C address
AS5048B_ADDRESS = 0x40

# Registers for the AS5048B angle value
AS5048B_REG_ANGLE_HIGH = 0xFE  # Register for bits 13 to 6 of the angle
AS5048B_REG_ANGLE_LOW = 0xFF   # Register for bits 5 to 0 of the angle


def read_angle(bus, address):
    """
    Read the angle data from the encoder.
    """
    # Read the high byte (contains bits 13 to 6)
    angle_high = bus.read_byte_data(address, AS5048B_REG_ANGLE_HIGH)
    # Read the low byte (contains bits 5 to 0)
    angle_low = bus.read_byte_data(address, AS5048B_REG_ANGLE_LOW)

    # Combine the two bytes into a 14-bit value
    angle = ((angle_high & 0x7F) << 6) | (angle_low & 0x3F)

    # The value is 14-bit, so we normalize it to a 360 degree scale
    return angle * 360 / 16384.0




# Define the angle stability threshold and duration
STABILITY_THRESHOLD = 0.5  # Adjust as needed
STABILITY_DURATION = 10  # 5 seconds (adjust as needed)

def perform_calibration(bus, address):
    """
    Perform calibration by moving the encoder from the upright position to the left stopper
    and then back to the upright position to the right stopper.
    Record the raw encoder angles during this process.
    """
    calibration_data = []

    def is_stable(values):
        # Check if the last values in the list are stable (within the threshold) for the specified duration
        if len(values) < STABILITY_DURATION:
            return False
        return all(abs(values[-1] - value) < STABILITY_THRESHOLD for value in values[-STABILITY_DURATION:])

    print("Move the encoder to the upright position.")
    input("Press Enter when ready to start calibration...")

    # Record angles while moving from upright to left stopper
    print("Calibrating left side...")
    last_raw_angles = []
    while True:
        raw_angle = read_angle(bus, address)
        calibration_data.append(raw_angle)
        last_raw_angles.append(raw_angle)

        # Check if the left stopper is reached
        if is_stable(last_raw_angles):
            break

    print("Move the encoder to the upright position.")
    input("Press Enter when ready to continue calibration...")

    # Record angles while moving from upright to right stopper
    print("Calibrating right side...")
    last_raw_angles = []
    while True:
        raw_angle = read_angle(bus, address)
        calibration_data.append(raw_angle)
        last_raw_angles.append(raw_angle)

        # Check if the right stopper is reached
        if is_stable(last_raw_angles):
            break

    return calibration_data


def map_angle(raw_angle, start_angle, left_stop_angle, right_stop_angle):
    """
    Map the raw angle to a desired range based on the calibration data.
    """
    if raw_angle < start_angle:
        # Angle is to the left of the start position, map to the left stop angle and make it negative
        mapped_angle = -(start_angle - raw_angle) / (start_angle - left_stop_angle) * left_stop_angle
    else:
        # Angle is to the right of the start position, map to the right stop angle
        mapped_angle = (raw_angle - start_angle) / (right_stop_angle - start_angle) * right_stop_angle

    return mapped_angle

def main():
    # Create an instance of the smbus2 SMBus
    bus = smbus2.SMBus(1)

    # Perform calibration and get the calibration data
    calibration_data = perform_calibration(bus, AS5048B_ADDRESS)
    print("Calibration complete")

    # Calculate the angles corresponding to the left and right stoppers
    start_angle = min(calibration_data)
    right_stop_angle = max(calibration_data)
    left_stop_angle = min([angle for angle in calibration_data if angle > start_angle])

    try:
        while True:
            raw_angle = read_angle(bus, AS5048B_ADDRESS)
            mapped_angle = map_angle(raw_angle, start_angle, left_stop_angle, right_stop_angle)
            print("Mapped Angle: {:.2f} degrees".format(mapped_angle))
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()

if __name__ == "__main__":
    main()