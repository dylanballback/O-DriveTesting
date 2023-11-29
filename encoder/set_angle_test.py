import smbus2
import time

# AS5048B I2C address
AS5048B_ADDRESS = 0x40

# Registers for the AS5048B angle value
AS5048B_REG_ANGLE_HIGH = 0xFE  # Register for bits 13 to 6 of the angle
AS5048B_REG_ANGLE_LOW = 0xFF   # Register for bits 5 to 0 of the angle

# This variable will hold the zero offset
zero_offset = 0
# This variable will hold the last raw angle to detect rollover
last_raw_angle = None

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

def read_angle(bus, address):
    """
    Read the angle data from the encoder, adjust for zero offset, and handle rollover.
    """
    global last_raw_angle
    raw_angle = read_raw_angle(bus, address)

    # If it's the first read, initialize last_raw_angle
    if last_raw_angle is None:
        last_raw_angle = raw_angle

    # Calculate the difference from the last raw angle
    difference = raw_angle - last_raw_angle

    # Check for rollover from 0x3FFF to 0x0000 (clockwise)
    if difference < -8192:  # More than half the range in the negative direction
        difference += 16384
    # Check for rollover from 0x0000 to 0x3FFF (counter-clockwise)
    elif difference > 8192:  # More than half the range in the positive direction
        difference -= 16384

    # Update the last_raw_angle with the current raw_angle
    last_raw_angle = raw_angle

    # Adjust the angle based on the zero offset and the difference
    adjusted_angle = (zero_offset + difference) % 16384

    # Convert to degrees
    return adjusted_angle * 360 / 16384.0

def main():
    # Create an instance of the smbus2 SMBus
    bus = smbus2.SMBus(1)

    try:
        # Set the current position as zero
        set_zero_position(bus, AS5048B_ADDRESS)
        
        while True:
            angle = read_angle(bus, AS5048B_ADDRESS)
            print("Angle: {:.2f} degrees".format(angle))
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()

if __name__ == "__main__":
    main()