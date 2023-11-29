import smbus2
import time

# AS5048B I2C address
AS5048B_ADDRESS = 0x40

# Registers for the AS5048B angle value
AS5048B_REG_ANGLE_HIGH = 0xFE  # Register for bits 13 to 6 of the angle
AS5048B_REG_ANGLE_LOW = 0xFF   # Register for bits 5 to 0 of the angle

# This variable will hold the zero offset
zero_offset = 0

# Global variable to store the last angle read from the encoder
last_angle = 0

def read_raw_angle(bus, address):
    """
    Read the raw angle data from the encoder.
    """
    angle_high = bus.read_byte_data(address, AS5048B_REG_ANGLE_HIGH)
    angle_low = bus.read_byte_data(address, AS5048B_REG_ANGLE_LOW)
    return ((angle_high & 0x7F) << 6) | (angle_low & 0x3F)

def set_zero_position(bus, address):
    """
    Read the current position and set it as the new zero.
    """
    global zero_offset
    zero_offset = read_raw_angle(bus, address)

def read_angle(bus, address, last_angle):
    """
    Read the angle data from the encoder, adjust it by the zero offset, and handle rollover.
    """
    raw_angle = read_raw_angle(bus, address)
    print(raw_angle)
    # Adjust the raw angle based on the zero offset
    adjusted_angle = (raw_angle - zero_offset) % 16384
    
    # Calculate the difference between the new angle and the last angle
    angle_difference = adjusted_angle - last_angle
    
    # Detect rollover from 16383 to 0
    if angle_difference > 8192:  # Half of 16384
        adjusted_angle -= 16384
    # Detect rollover from 0 to 16383
    elif angle_difference < -8192:  # Negative half of 16384
        adjusted_angle += 16384

    # Ensure adjusted_angle is within 0 to 16383
    adjusted_angle = adjusted_angle % 16384

    # Update last_angle for next calculation
    last_angle = adjusted_angle

    # Normalize the angle to a 360 degree scale
    return adjusted_angle * 360 / 16384.0, last_angle



def main():
    # Initialize last_angle to a value that's out of range to force a fresh read
    last_angle = -1
    bus = smbus2.SMBus(1)

    try:
        # Set the initial zero position
        set_zero_position(bus, AS5048B_ADDRESS)
        
        while True:
            angle, last_angle = read_angle(bus, AS5048B_ADDRESS, last_angle)
            print("Angle: {:.2f} degrees".format(angle))
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()

if __name__ == "__main__":
    main()
