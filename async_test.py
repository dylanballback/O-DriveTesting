import asyncio
import can
import struct

node_id = 0 # must match `<odrv>.axis0.config.can.node_id`. The default is 0.

bus = can.interface.Bus("can0", bustype="socketcan")

# Flush CAN RX buffer so there are no more old pending messages
while not (bus.recv(timeout=0) is None): pass

# Put axis into closed loop control state
bus.send(can.Message(
    arbitration_id=(node_id << 5 | 0x07), # 0x07: Set_Axis_State
    data=struct.pack('<I', 8), # 8: AxisState.CLOSED_LOOP_CONTROL
    is_extended_id=False
))

# Wait for axis to enter closed loop control by scanning heartbeat messages
for msg in bus:
    if msg.arbitration_id == (node_id << 5 | 0x01): # 0x01: Heartbeat
        error, state, result, traj_done = struct.unpack('<IBBB', bytes(msg.data[:7]))
        if state == 8: # 8: AxisState.CLOSED_LOOP_CONTROL
            break

# Set velocity function to vel_set turns/s
async def set_vel(vel_set):
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x0d),  # 0x0d: Set_Input_Vel
        data=struct.pack('<ff', float(vel_set), 0.0),  # 1.0: velocity, 0.0: torque feedforward
        is_extended_id=False
    ))

# Print encoder feedback
async def get_pos_vel():
    for msg in bus:
        if msg.arbitration_id == (node_id << 5 | 0x09):  # 0x09: Get_Encoder_Estimates
            pos, vel = struct.unpack('<ff', bytes(msg.data))
            print(f"pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")
            return  # To exit the loop

async def print_values_and_set_vel():
    value = 0
    step = 0.25

    while value <= 10:
        print(value)
        await set_vel(value)  # Set velocity with the current value
        value += step
        await asyncio.sleep(1)

async def main():
    await asyncio.gather(
        print_values_and_set_vel(),
        get_pos_vel()
    )

if __name__ == "__main__":
    asyncio.run(main())
