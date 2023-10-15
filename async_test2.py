import asyncio
import can
import struct
import signal
import threading

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



#Don't change the code above
#-----------------------------------------------------------------------------


# Set velocity function to vel_set turns/s
def set_vel(vel_set):
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x0d),  # 0x0d: Set_Input_Vel
        data=struct.pack('<ff', float(vel_set), 0.0),  # velocity, torque feedforward
        is_extended_id=False
    ))

# Print encoder feedback
def get_pos_vel():
    while True:
        for msg in bus:
            if msg.arbitration_id == (node_id << 5 | 0x09):  # 0x09: Get_Encoder_Estimates
                pos, vel = struct.unpack('<ff', bytes(msg.data))
                print(f"pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")

def main():
    # Create and start threads for get_pos_vel and set_vel functions
    get_pos_vel_thread = threading.Thread(target=get_pos_vel)
    get_pos_vel_thread.daemon = True  # Allow program to exit if only this thread is running
    get_pos_vel_thread.start()

    value = 0
    step = 0.25

    while value <= 10:
        print(value)
        set_vel(value)  # Set velocity from 0 to 10 in 0.25-second increments
        value += step
        time.sleep(0.25)

    while value >= 0:
        print(value)
        set_vel(value)  # Set velocity from 10 to 0 in 0.25-second increments
        value -= step
        time.sleep(0.25)

if __name__ == "__main__":
    main()





"""
# Set velocity function to vel_set turns/s
async def set_vel(vel_set):
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x0d),  # 0x0d: Set_Input_Vel
        data=struct.pack('<ff', float(vel_set), 0.0),  # velocity, torque feedforward
        is_extended_id=False
    ))

# Print encoder feedback
async def get_pos_vel():
    while True:
        for msg in bus:
            if msg.arbitration_id == (node_id << 5 | 0x09):  # 0x09: Get_Encoder_Estimates
                pos, vel = struct.unpack('<ff', bytes(msg.data))
                print(f"pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")

async def print_and_set_velocity():
    for value in range(0, 11):
        print(value)
        await set_vel(value)  # Set velocity from 0 to 10 in 0.25-second increments
        await asyncio.sleep(0.25)

    for value in range(10, -1, -1):
        print(value)
        await set_vel(value)  # Set velocity from 10 to 0 in 0.25-second increments
        await asyncio.sleep(0.25)

async def main():
    await asyncio.gather(
        get_pos_vel(),  # Continuously run get_pos_vel
        print_and_set_velocity()  # Print and set velocity
    )

if __name__ == "__main__":
    asyncio.run(main())



"""
