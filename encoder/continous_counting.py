import smbus2
import time

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

def main():
    # Create an instance of the smbus2 SMBus
    bus = smbus2.SMBus(1)

    # Initialize variables
    total_angle = 0.0

    try:
        while True:
            angle = read_angle(bus, AS5048B_ADDRESS)

            # Calculate the change in angle
            angle_change = angle - total_angle

            # Update the total angle
            total_angle += angle_change

            # Ensure the total angle stays within 0 to 360 degrees
            if total_angle >= 360:
                total_angle -= 360
            elif total_angle < 0:
                total_angle += 360

            print("Total Angle: {:.2f} degrees".format(total_angle))
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()

if __name__ == "__main__":
    main()
