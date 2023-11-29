import smbus2
import time

# AS5048B I2C address
AS5048B_ADDRESS = 0x40

# Registers for the AS5048B
AS5048B_REG_ANGLE = 0xFE  # The angle register is 0xFE

def read_angle(bus, address):
    """
    Read the angle data from the encoder.
    """
    # Read two bytes of data
    data = bus.read_i2c_block_data(address, AS5048B_REG_ANGLE, 2)

    # Combine the two bytes to create one 14-bit number
    angle = ((data[0] & 0xFF) << 6) | (data[1] & 0x3F)

    # The value is 14-bit, so we can normalize it to a 360 degree scale
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