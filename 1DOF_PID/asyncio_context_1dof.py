import asyncio
import struct
from contextlib import contextmanager

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

@contextmanager
def get_can_bus(node, bus_id, bus_type):
    # Create the bus.
    can_bus = can.interface.Bus(bus_id, bustype=bus_type)\
    
    # Flush the buffer.
    while can_bus.recv(timeout=0) is not None:
        pass
    
    # Set control state.
    can_bus.send(can.Message(
        arbitration_id=(node << 5 | 0x07),
        data=struct.pack("<I", 8),
        is_extended_id=False,
    ))
    
    # Flush the can bus.
    for msg in can_bus:
        if msg.arbitration_id == (node << 5 | 0x01):
            error, state, result, traj_done = struct.unpack("<IBBB", bytes(msg.data[:7]))
            if state == 8:
                break
    
    try:
        # Share the can bus.
        yield can_bus
    
    # Shutdown bus when done.
    finally:
        can_bus.send(can.Message(
            arbitration_id=(node << 5 | 0x0E),
            data=struct.pack("<f", 0.0),
            is_extended_id=False,
        ))
        can_bus.shutdown()

async def read_angles(data, sm_bus, address, angle_reg, frequency):
    """
    """
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
    angle = None
    try:
        # Loop until flagged to stop.
        while data["is_running"]:
            
            # Wait a certain amount of time between iterations.
            await asyncio.sleep(frequency)
            
            # Skip iteration if no angle yet.
            if "angle" not in data:
                continue
            
            # Calculate the torque.
            data_angle = data["angle"]
            if angle is None:
                angle = data_angle
            elif (data_angle - angle) % 360 < 180:
                angle += (data_angle - angle) % 360
            else:
                angle += (data_angle - angle) % 360
                angle -= 360
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


p = 0.05
i = 0
d = 0.001

async def main(can_bus):
    # Shared data.
    data = {"is_running": True}
    
    # Create PID.
    pid = PID(p, i, d, setpoint=180)
    
    # Limit the PID output.
    lower = -0.63
    upper = +0.63
    pid.output_limits = (lower, upper)
    
    try:
        # Run both until everything is done.
        await asyncio.gather(
            read_angles(data, SM_BUS, AS5048A_ADDRESS, AS5048A_ANGLE_REG, 0.001),
            set_torque(data, pid, can_bus, NODE_ID, 0.001),
        )
    
    # Ensure everything stops if something stops.
    finally:
        data["is_running"] = False

with get_can_bus(NODE_ID, CAN_BUS_ID, CAN_BUS_TYPE) as can_bus:
    # Run asyncio.
    asyncio.run(main(can_bus))