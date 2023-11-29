import smbus2
import time

# AS5048B I2C address
AS5048B_ADDRESS = 0x40

# Registers for the AS5048B angle value
AS5048B_REG_ANGLE_HIGH = 0xFE  # Register for bits 13 to 6 of the angle
AS5048B_REG_ANGLE_LOW = 0xFF   # Register for bits 5 to 0 of the angle

# This variable will hold the zero offset
zero_offset = 0
# This variable will hold the last angle to calculate the correct continuous angle
continuous_angle = 0

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
    global zero_offset, continuous_angle
    zero_offset = read_raw_angle(bus, address)
    continuous_angle = 0  # Reset the continuous angle

def read_angle(bus, address):
    """
    Read the angle data from the encoder, adjust for zero offset, and handle rollover.
    """
    global zero_offset, continuous_angle
    raw_angle = read_raw_angle(bus, address) - zero_offset
    adjusted_angle = raw_angle % 16384  # Adjust the angle for zero offset

    # Calculate the change in angle, considering the rollover
    angle_change = adjusted_angle - (continuous_angle % 16384)
    
    # Detect if rollover occurred
    if angle_change < -8192:  # Rollover from 0 to 16383
        angle_change += 16384
    elif angle_change > 8192:  # Rollover from 16383 to 0
        angle_change -= 16384

    # Update the continuous angle
    continuous_angle += angle_change

    return continuous_angle * 360 / 16384.0  # Convert to degrees

def main():
    # Create an instance of the smbus2 SMBus
    bus = smbus2.SMBus(1)

    try:
        # Set the current position as zero
        set_zero_position(bus, AS5048B_ADDRESS)
        
        while True:
            angle = read_angle(bus, AS5048B_ADDRESS)
            print("Angle: {:.2f} degrees".format(angle))
            time.sleep(0.1)
    except KeyboardInterrupt:
        # Gracefully handle a keyboard interrupt
        print("Interrupted by user")
    except Exception as e:
        # Handle other exceptions
        print("An error occurred:", e)
    finally:
        bus.close()

if __name__ == "__main__":
    main()
