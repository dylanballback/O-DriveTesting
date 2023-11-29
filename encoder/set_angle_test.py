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
last_raw_angle = -1
# This will hold the total accumulated angle to handle rollover
total_angle = 0

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
    global zero_offset, last_raw_angle, total_angle
    zero_offset = read_raw_angle(bus, address)
    last_raw_angle = zero_offset
    total_angle = 0  # Reset the total angle

def calculate_continuous_angle(raw_angle, last_angle):
    global total_angle
    if last_angle == -1:  # No last angle recorded, skip calculation
        total_angle = 0
    else:
        # Check if there has been a rollover
        difference = raw_angle - last_angle
        if difference > 8191:  # Rollover, counting down
            total_angle -= (16384 - difference)
        elif difference < -8191:  # Rollover, counting up
            total_angle += (16384 + difference)
        else:
            total_angle += difference

    return total_angle

def read_angle(bus, address):
    """
    Read the angle data from the encoder and adjust for zero offset, and handle rollover.
    """
    global last_raw_angle
    raw_angle = read_raw_angle(bus, address)
    continuous_angle = calculate_continuous_angle(raw_angle, last_raw_angle)
    last_raw_angle = raw_angle  # Update the last angle

    # Adjust for zero offset and scale to degrees
    adjusted_angle = (continuous_angle - zero_offset) % 16384
    return adjusted_angle * 360 / 16384.0

def main():
    # Create an instance of the smbus2 SMBus
    bus = smbus2.SMBus(1)

    try:
        # Set the current position as zero
        set_zero_position(bus, AS5048B_ADDRESS)
        
        while True:
            angle = read_angle(bus, AS5048B_ADDRESS)
            print(f"Angle: {angle:.2f} degrees")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        bus.close()

if __name__ == "__main__":
    main()
