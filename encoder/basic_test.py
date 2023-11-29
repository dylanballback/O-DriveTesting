import smbus2
import time

# AS5048B I2C address
AS5048B_ADDRESS = 0x40

# Registers for the AS5048B angle value
AS5048B_REG_ANGLE_HIGH = 0xFE  # High byte of the angle value
AS5048B_REG_ANGLE_LOW = 0xFF   # Low byte of the angle value

def read_angle(bus, address):
    """
    Read the angle data from the encoder.
    """
    # Read two bytes of data from the angle registers
    angle_high = bus.read_byte_data(address, AS5048B_REG_ANGLE_HIGH)
    angle_low = bus.read_byte_data(address, AS5048B_REG_ANGLE_LOW)

    # Combine the two bytes to create one 14-bit number
    # Masking the lower 6 bits of the high byte and shifting left by 8 bits,
    # then adding the low byte.
    angle = ((angle_high & 0x3F) << 8) | angle_low

    # The value is 14-bit, so we normalize it to a 360 degree scale
    return angle * 360 / 16384.0

def main():
    # Create an instance of the smbus2 SMBus
    bus = smbus2.SMBus(1)

    try:
        while True:
            angle = read_angle(bus, AS5048B_ADDRESS)
            print("Angle: {:.2f} degrees".format(angle))
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()

if __name__ == "__main__":
    main()