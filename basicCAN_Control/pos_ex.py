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


def set_odrive_position(node_id, desired_position, bus_channel="can0"):
    """
    Sets the desired position for the ODrive motor through CAN messages.
    
    Parameters:
    - node_id: The CAN node ID of the ODrive motor controller.
    - desired_position: The target position value for the motor.
    - bus_channel: The CAN bus channel (default is "can0").


    Axis0_Set_Input_Pos (0xC)
        - Input_Pos
        - Vel_FF
        - Torque_FF
    """
    
    # Pack the desired position as a float (IEEE 754) into a byte array
    position_data = struct.pack('<f', desired_position)
    
    # Send the position command
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x00C), # 0x00C: 
        data=position_data,
        is_extended_id=False
    ))

    print(f"Position set to {desired_position}.")


# Print encoder feedback
def get_pos_vel():
    for msg in bus:
        if msg.arbitration_id == (node_id << 5 | 0x09): # 0x09: Get_Encoder_Estimates
            pos, vel = struct.unpack('<ff', bytes(msg.data))
            return print(f"pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")


# Example usage:
set_odrive_position(0, 1000.0)  # Node ID 0, desired position 1000.0 units
