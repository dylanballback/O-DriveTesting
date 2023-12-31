"""
Minimal example for controlling an ODrive via the CANSimple protocol.

Puts the ODrive into closed loop control mode, sends a velocity setpoint of 1.0
and then prints the encoder feedback.

Assumes that the ODrive is already configured for velocity control.

See https://docs.odriverobotics.com/v/latest/manual/can-protocol.html for protocol
documentation.
"""

#This code is modified to make the commands into functions. 

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

# Set torque function to torque_set 
def set_torque(torque_set):
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x0E), # 0x0E: Set_Input_Torque
        data=struct.pack('<ff', float(torque_set), 0.0), 
        is_extended_id=False
    ))


# Print encoder feedback
def get_pos_vel():
    for msg in bus:
        if msg.arbitration_id == (node_id << 5 | 0x09): # 0x09: Get_Encoder_Estimates
            pos, vel = struct.unpack('<ff', bytes(msg.data))
            return print(f"pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")






set_vel_prev = 0

set_vel_value = 10

try:
    while True:
        if set_vel_value != set_vel_prev:
            set_vel_prev= set_vel
            set_vel(set_vel_value)
        else:
            get_pos_vel()

except KeyboardInterrupt:
    bus.shutdown()


#
#while True:
#    set_vel(10)



#get_pos_vel()