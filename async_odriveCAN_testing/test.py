import asyncio
import time
from datetime import datetime, timedelta

MESSAGES = []

async def recv(stop_at):
    while not MESSAGES and datetime.now() < stop_at:
        time.sleep(0.01)
    if MESSAGES:
        return MESSAGES.pop()

async def send(msg):
    await asyncio.sleep(1)
    MESSAGES.append(msg)

async def get_torque():
    asyncio.create_task(send("torque"))
    msg = await recv(datetime.now() + timedelta(seconds=2))
    print(msg)

async def get_velocity():
    asyncio.create_task(send("velocity"))
    msg = await recv(datetime.now() + timedelta(seconds=2))
    print(msg)

async def main():
    await asyncio.gather(
        get_velocity(),
        get_torque(),
    )

asyncio.run(main())