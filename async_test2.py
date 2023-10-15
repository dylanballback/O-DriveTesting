import can
import struct
import threading
import time

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
def set_vel():
    while True:
        for vel_set in range(11):
            bus.send(can.Message(
                arbitration_id=(node_id << 5 | 0x0d),
                data=struct.pack('<ff', float(vel_set), 0.0),
                is_extended_id=False
            ))
            time.sleep(0.25)
        for vel_set in range(10, -1, -1):
            bus.send(can.Message(
                arbitration_id=(node_id << 5 | 0x0d),
                data=struct.pack('<ff', float(vel_set), 0.0),
                is_extended_id=False
            ))
            time.sleep(0.25)

# Print encoder feedback
def get_pos_vel():
    while True:
        for msg in bus:
            if msg.arbitration_id == (node_id << 5 | 0x09):
                pos, vel = struct.unpack('<ff', bytes(msg.data))
                print(f"pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")

# Create two threads to run set_vel and get_pos_vel concurrently
vel_thread = threading.Thread(target=set_vel)
pos_thread = threading.Thread(target=get_pos_vel)

# Start both threads
vel_thread.start()
pos_thread.start()

# Wait for both threads to finish (you may need to manually stop them if needed)
# vel_thread.join()
# pos_thread.join()








#-----------------------------------------------------------------------------


#Example where you can go from 0 to 10 at 0.25 second increments while recieving pos and velocity commands at the same time:
"""


import can
import struct
import threading
import time

node_id = 0
bus = can.interface.Bus("can0", bustype="socketcan")

# Flush CAN RX buffer so there are no more old pending messages
while not (bus.recv(timeout=0) is None):
    pass

# Put the axis into closed loop control state
bus.send(can.Message(
    arbitration_id=(node_id << 5 | 0x07),
    data=struct.pack('<I', 8),
    is_extended_id=False
))

# Wait for the axis to enter closed loop control by scanning heartbeat messages
for msg in bus:
    if msg.arbitration_id == (node_id << 5 | 0x01):
        error, state, result, traj_done = struct.unpack('<IBBB', bytes(msg.data[:7]))
        if state == 8:
            break

# Set velocity function to vel_set turns/s
def set_vel():
    for vel_set in range(11):
        bus.send(can.Message(
            arbitration_id=(node_id << 5 | 0x0d),
            data=struct.pack('<ff', float(vel_set), 0.0),
            is_extended_id=False
        ))
        time.sleep(0.25)

# Print encoder feedback
def get_pos_vel():
    for msg in bus:
        if msg.arbitration_id == (node_id << 5 | 0x09):
            pos, vel = struct.unpack('<ff', bytes(msg.data))
            print(f"pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")

# Create two threads to run set_vel and get_pos_vel concurrently
vel_thread = threading.Thread(target=set_vel)
pos_thread = threading.Thread(target=get_pos_vel)

# Start both threads
vel_thread.start()
pos_thread.start()

# Wait for both threads to finish
vel_thread.join()
pos_thread.join()

"""