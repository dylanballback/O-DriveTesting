import smbus

bus = smbus.SMBus(1)  # Change this to 0 if you're using I2C bus 0

for address in range(128):
    try:
        bus.read_byte(address)
        print(f"Device found at address 0x{address:02X}")
    except Exception:
        pass