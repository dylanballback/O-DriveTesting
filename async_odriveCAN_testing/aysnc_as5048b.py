import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from smbus import SMBus


@dataclass
class Encoder_as5048b:
    bus: SMBus = field(default_factory=lambda: SMBus(1))
    address: int = 0x40 # AS5048B default address
    angle_reg: int = 0xFE # AS5048B Register
    angle: float = 0.0
    offset: float = 0.0
    running: bool = True

    def read_angle(self):
        data = self.bus.read_i2c_block_data(self.address, self.angle_reg, 2)
        angle = data[0] * 256 + data[1]
        angle *= 45 / 16383
        return angle - self.offset

    def calibrate(self):
        self.offset = self.read_angle()

    async def listen_to_angle(self):
        while self.running:
            await asyncio.sleep(0)
            self.angle = self.read_angle()

    async def loop(self, *others):
        if others:
            await asyncio.gather(
                self.listen_to_angle(),
                *others,
            )
        else:
            await self.listen_to_angle()

    def run(self, *others):
        asyncio.run(self.loop(*others))


async def controller(encoder):
    stop_at = datetime.now() + timedelta(seconds=15)
    
    while datetime.now() < stop_at:
        await asyncio.sleep(0.001)
        print("Encoder angle:", encoder.angle)
    
    encoder.running = False

if __name__ == "__main__":
    encoder = Encoder_as5048b()
    encoder.calibrate()
    encoder.run(controller(encoder))