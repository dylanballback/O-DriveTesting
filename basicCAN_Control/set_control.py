
#This code is trying to set the O-Drive Control Type through CAN 

"""
To my understanding: 

Axis_Set_Controller_Mode 
    ID: 0x2B
        Signals:
            - Control_Mode
                VALUE DESCRIPTIONS:
                    - 0x0  = VOLTAGE_CONTROL
                    - 0x1  = TORQUE_CONTROL 
                    - 0x2  = VELOCITY_CONTROL
                    - 0x3  = POSITION_CONTROL
            - Input_Mode
                VALUE DESCRIPTIONS:
                    - 0x0  = INACTIVE
                    - 0x1  = PASSTHROUGH 
                    - 0x2  = VEL_RAMP
                    - 0x3  = POS_FILTER
                    - 0x4  = MIX_CHANNELS
                    - 0x5  = TRAP_TRAJ
                    - 0x6  = TORQUE_RAMP
                    - 0x7  = MIRROR
                    - 0x8  = TUNING


"""

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
def set_vel(vel_set):
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x0d), # 0x0d: Set_Input_Vel
        data=struct.pack('<ff', float(vel_set), 0.0), # 1.0: velocity, 0.0: torque feedforward
        is_extended_id=False
    ))



def set_odrive_torque_control(node_id, torque_value):
    """
    Puts the ODrive motor controller (specified by node_id) into torque control mode 
    and sets the desired torque value.
    
    Parameters:
    - node_id: The CAN node ID of the ODrive motor controller.
    - torque_value: Desired torque value (in Nm, ensure it's within the limits of your ODrive configuration).
    """
    
    bus = can.interface.Bus("can0", bustype="socketcan")
    
    # 1. Set control mode to torque control (assuming the command ID for setting control mode is similar to the one provided in your example)
    CONTROL_MODE_TORQUE = 1  # This might vary based on ODrive's CAN protocol
    control_mode_data = struct.pack('<I', CONTROL_MODE_TORQUE)
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x00B),  # 0x00B: Set_Controller_Mode
        data=control_mode_data,
        is_extended_id=False
    ))

    # 2. Send the desired torque command (assuming the command ID for setting torque is different)
    torque_data = struct.pack('<f', torque_value)  # Assuming torque is sent as a 4-byte float
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x00E),  # 0x00E: Set_Input_Torque
        data=torque_data,
        is_extended_id=False
    ))

# Example usage:
# set_odrive_torque_control(0, 0.5)  # Node ID 0, Torque 0.5 Nm