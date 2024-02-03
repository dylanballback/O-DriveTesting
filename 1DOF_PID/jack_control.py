import asyncio
import struct
import time
from contextlib import contextmanager

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
    """
    1. Creates the can bus.
    2. Sets up the can bus.
    3. Returns the can bus.
    4. Shuts down the can bus.
    
    Usage:
        with get_can_bus(...) as can_bus:
            can_bus.send(...)
            can_bus.send(...)
            can_bus.send(...)
    """
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
    Reads angles from the SM Bus
    and saves them to the data.
    
    Usage:
        data = {}
        
        def use_angles(data):
            while True:
                await asyncio.sleep(0)
                if "angle" in data:
                    print(data["angle"])
        
        # Read the angles and save them into the data.
        # Use the angles in another async function.
        await asyncio.gather(
            read_angles(data, ...),
            use_angles(data),
        )
    """
    try:
        # Loop until flagged to stop.
        while data["is_running"]:
            
            # Wait a certain amount of time between iterations.
            await asyncio.sleep(frequency)
            
            # Read from the SM bus.
            block_data = sm_bus.read_i2c_block_data(address, angle_reg, 2)
            
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
    """
    Reads angles from the data, processes
    them into torque using a PID, and sets
    the torque onto thecan bus.
    
    Usage:
        data = {}
        
        def read_angles(data):
            for angle in range(10)
                await asyncio.sleep(1)
                data["angle"] = angle
        
        # Read the angles in another async function.
        # Use the angles to set the torque on the can bus.
        await asyncio.gather(
            read_angles(data),
            set_torque(data, ...),
        )
    """
    v2 = 0.0
    w = 0.0
    d = 0.0001
    t1 = None
    try:
        # Loop until flagged to stop.
        while data["is_running"]:
            
            # Wait a certain amount of time between iterations.
            await asyncio.sleep(frequency)
            
            # Skip iteration if no angle yet.
            if "angle" not in data:
                continue
            
            # Calculate the torque.
            angle = data["angle"]
            torque = pid(angle)

            if t is None:
                t1 = time.monotonic_ns()
                a = angle
            else:
                t2 = time.monotonic_ns()
                dt = t2 - t1
                da = angle - a
                v = da / dt
                v2 *= (1 - d) ** dt
                v2 += (1 - (1 - d) ** dt) * (v ** 2)
                w *= (1 - d) ** dt
                w += 1 - (1 - d) ** dt
                t1 = t2
                a = angle
                torque *= v * (w / v2) ** 0.5
            
            # Send a message to the can bus.
            can_bus.send(can.Message(
                arbitration_id=(node_id << 5 | 0x0E),
                data=struct.pack("<f", torque),
                is_extended_id=False,
            ))
    
    # Signal everything to stop if something stops.
    finally:
        data["is_running"] = False

p = 0.01
i = 0
d = 0.001

async def main(can_bus):
    """
    1. Use a can bus.
    2. Create a PID controller.
    3. Run async.
        a. Read angle data from the SM bus.
        b. Set the torque by:
            1. Process the angle with the PID controller.
            2. Send the torque to the can bus.
    4. Stop everything if KeyboardInterrupt.
    """
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

# Setup can bus and shutdown when done.
with get_can_bus(NODE_ID, CAN_BUS_ID, CAN_BUS_TYPE) as can_bus:
    # Run asyncio.
    asyncio.run(main(can_bus))
