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

    previous_angle = None

    try:
        while True:
            angle = read_angle(bus, AS5048B_ADDRESS)

            if previous_angle is not None:
                # Calculate the difference between the current angle and the previous angle
                angle_diff = angle - previous_angle

                # Check for wraparound (e.g., from 360 to 0)
                if angle_diff < -180:
                    angle_diff += 360
                elif angle_diff > 180:
                    angle_diff -= 360

                # Calculate the new angle
                angle = previous_angle + angle_diff

            print("Angle: {:.2f} degrees".format(angle))

            # Update the previous angle
            previous_angle = angle

            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()

if __name__ == "__main__":
    main()
