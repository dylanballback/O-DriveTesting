import asyncio
import struct

import board
import can
import smbus

from as5048b import as5048b
from simple_pid import PID

AS5048A_ADDRESS = 0x40
AS5048A_ANGLE_REG = 0xFE
NODE_ID = 0
CAN_BUS_ID = "can0"
CAN_BUS_TYPE = "socketcan"

SM_BUS = smbus.SMBus(1)

CAN_BUS = can.interface.Bus(CAN_BUS_ID, bustype=CAN_BUS_TYPE)

# Flush buffer.
while CAN_BUS.recv(timeout=0) is not None:
    pass

# Set control state.
CAN_BUS.send(can.Message(
    arbitration_id=(NODE_ID << 5 | 0x07),
    data=struct.pack("<I", 8),
    is_extended_id=False,
))

# Flush the can bus.
for msg in CAN_BUS:
    if msg.arbitration_id == (NODE_ID << 5 | 0x01):
        error, state, result, traj_done = struct.unpack("<IBBB", bytes(msg.data[:7]))
        if state == 8:
            break

async def read_angles(data, sm_bus, address, angle_reg, frequency):
    try:
        # Loop until flagged to stop.
        while data["is_running"]:
            
            # Wait a certain amount of time between iterations.
            await asyncio.sleep(frequency)
            
            # Read from the SM bus.
            block_data = sm_bus.read_i2c_block_data(AS5048A_ADDRESS, AS5048A_ANGLE_REG, 2)
            
            # Parse the data.
            angle = block_data[0] * 256 + block_data[1]
            angle /= 16383.0
            angle *= 90.0
            
            # Save the data for use elsewhere.
            data["angle"] = angle
    
    # Signal everything to stop if something stops.
    finally:
        data["is_running"] = False

async def set_torque(data, pid, can_bus, node_id, frequency):
    try:
        # Loop until flagged to stop.
        while data["is_running"]:
            
            # Wait a certain amount of time between iterations.
            await asyncio.sleep(frequency)
            
            # Skip iteration if no angle yet.
            if "angle" is not in data:
                continue
            
            # Calculate the torque.
            angle = data["angle"]
            torque = pid(angle)
            
            # Send a message to the can bus.
            can_bus.send(can.Message(
                arbitration_id=(node_id << 5 | 0x0E),
                data=struct.pack("<f", torque),
                is_extended_id=False,
            ))
    
    # Signal everything to stop if something stops.
    finally:
        data["is_running"] = False

async def main():
    # Shared data.
    data = {"is_running": True}
    
    # Create PID.
    pid = PID(p=0.01, i=0, d=0, setpoint=180)
    
    # Limit the PID output.
    lower = -0.63
    upper = +0.63
    pid.output_limits = (lower, upper)
    
    try:
        # Run both until everything is done.
        await asyncio.gather(
            read_angles(data, SM_BUS, AS5048A_ADDRESS, AS5048A_ANGLE_REG, 0.001),
            read_angles(data, pid, CAN_BUS, NODE_ID, 0.001),
        )
    
    # Ensure everything stops if something stops.
    finally:
        data["is_running"] = False

try:
    # Run asyncio.
    asyncio.run(main())

# Shutdown bus when done.
finally:
    CAN_BUS.send(can.Message(
        arbitration_id=(NODE_ID << 5 | 0x0E),
        data=struct.pack("<f", 0.0),
        is_extended_id=False,
    ))
    CAN_BUS.shutdown()