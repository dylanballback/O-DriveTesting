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


def calibrate_map_angles(bus, address):
    """
    Read the start angle while inverted pendulum is striaght up and down 
    Move all the was to the left stopper and meaasure angle
    Move all the way to the right stopper and measure the angle 

    Now map the vertical start angle as 0 and then angles 
    moving left or right accordingly.
    """
    
    print("Move the inverted pendulum to the upright position with the lock.")
    time.sleep(3)
    start_angle = read_angle(bus, address)
    print(f"The raw verical angle recorded is {start_angle}")

    print("Move the inverted pendulum to the left stopper.")
    time.sleep(5)
    left_max_angle = read_angle(bus, address)
    print(f"The raw verical angle recorded is {left_max_angle}")

    print("Move the inverted pendulum to the right stopper.")
    time.sleep(5)
    right_max_angle = read_angle(bus, address)
    print(f"The raw verical angle recorded is {right_max_angle}")

    return start_angle, left_max_angle, right_max_angle


def map_angle(raw_angle, start_angle, left_max_angle, right_max_angle):
    """
    Map the raw angle to a desired range based on the measured limits.
    """
    if raw_angle >= start_angle:
        # Angle is to the right of the start position, map to the right_max_angle
        mapped_angle = (raw_angle - start_angle) / (right_max_angle - start_angle) * right_max_angle
    else:
        # Angle is to the left of the start position, map to the left_max_angle
        mapped_angle = -((raw_angle - start_angle) / (start_angle - left_max_angle) * left_max_angle)

    return mapped_angle


def main():
    # Create an instance of the smbus2 SMBus
    bus = smbus2.SMBus(1)

    start_angle, left_max_angle, right_max_angle = calibrate_map_angles(bus, AS5048B_ADDRESS)
    print(f"Calibration complete: Raw Upright= {start_angle}, Raw Left Max= {left_max_angle}, Raw Right Max {right_max_angle}")

    try:
        while True:
            raw_angle = read_angle(bus, AS5048B_ADDRESS)
            mapped_angle = map_angle(raw_angle, start_angle, left_max_angle, right_max_angle)
            print("Mapped Angle: {:.2f} degrees".format(mapped_angle))
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()

if __name__ == "__main__":
    main()