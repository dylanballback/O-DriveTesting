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

def read_angle(bus, address):
    """
    Read the angle data from the encoder and adjust it by the zero offset.
    """
    raw_angle = read_raw_angle(bus, address)
    # Adjust the raw angle based on the zero offset
    adjusted_angle = (raw_angle - zero_offset + 16384) % 16384

    # If the result is close to the maximum value, and the previous
    # angle was close to zero, we probably wrapped around from 0 to 16383.
    # Similarly, if the result is close to 0 and the previous angle was close to 16383,
    # we wrapped around from 16383 to 0.
    global last_angle
    if last_angle > 16300 and adjusted_angle < 100:
        # If we're close to 0 and the last angle was close to 16383,
        # add 16384 to the angle to handle wrap around
        adjusted_angle += 16384
    elif last_angle < 100 and adjusted_angle > 16300:
        # If we're close to 16383 and the last angle was close to 0,
        # subtract 16384 from the angle to handle wrap around
        adjusted_angle -= 16384

    last_angle = adjusted_angle  # Update the last angle for the next call
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
