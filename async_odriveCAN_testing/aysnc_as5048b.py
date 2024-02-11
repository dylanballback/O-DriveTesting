import asyncio
import smbus

class as5048b:
    def __init__(self):
        self.bus = smbus.SMBus(1)
        self.AS5048B_ADDR = 0x40  # AS5048B default address
        self.AS5048B_ANGLE_REG = 0xFE  # AS5048B Register
        self.angle = 0  # Sensor angle
        self.offset_angle = 0  # Offset angle to calibrate

    async def calibrate_encoder(self):
        print('Ensure CoM is below pivot\n\nCalibration beginning in:\n\n')
        time_remaining = 3

        while time_remaining != 0:
            print(f"{time_remaining} s")
            time_remaining = time_remaining - 1
            await asyncio.sleep(1)  # Use asyncio.sleep for non-blocking delay

        # Use executor to run blocking I/O operation
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, self.bus.read_i2c_block_data, self.AS5048B_ADDR, self.AS5048B_ANGLE_REG, 2)
        angle_pre_conversion = data[0] * 256 + data[1]
        resting_angle = (angle_pre_conversion / 16383.0) * 45

        self.offset_angle = resting_angle  # Here we simply store the resting angle as the offset

    async def read_angle_synch(self):
        # Use executor to run blocking I/O operation
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, self.bus.read_i2c_block_data, self.AS5048B_ADDR, self.AS5048B_ANGLE_REG, 2)

        # Convert the data
        angle_pre_conversion = data[0] * 256 + data[1]
        self.angle = (angle_pre_conversion / 16383.0) * 45.0 - self.offset_angle

        print(self.angle)
        await asyncio.sleep(0.001)  # Non-blocking delay

# Example usage
async def main():
    encoder = as5048b()
    await encoder.calibrate_encoder()
    while True:
        await encoder.read_angle_synch()

# Run the async main loop
asyncio.run(main())
