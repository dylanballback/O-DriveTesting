import can
import struct
import time


"""
12/1/23 

Testing out all the different O-Drive CAN data. 

"""

# Define the node IDs for your ODrives
odrive_node_ids = [0, 1]

bus = can.interface.Bus("can0", bustype="socketcan")


def flush_can_buffer():
    #Flush CAN RX buffer to ensure no old pending messages.
    while not (bus.recv(timeout=0) is None): pass
    print("I have cleared all CAN Messages on the BUS!")


# Put axis into closed loop control state
def set_control_state(node_id):
    flush_can_buffer()
    print(f"Attempting to set control state to ODrive {node_id}...")
    try:
        bus.send(can.Message(
            arbitration_id=(node_id << 5 | 0x07), # 0x07: Set_Axis_State
            data=struct.pack('<I', 8), # 8: AxisState.CLOSED_LOOP_CONTROL
            is_extended_id=False
        ))
        
        print(f"Checking Hearbeat for ODrive {node_id}")
        # Wait for axis to enter closed loop control by scanning heartbeat messages
        for msg in bus:
            if msg.arbitration_id == (node_id << 5 | 0x01): # 0x01: Heartbeat
                error, state, result, traj_done = struct.unpack('<IBBB', bytes(msg.data[:7]))
                if state == 8: # 8: AxisState.CLOSED_LOOP_CONTROL
                    break
        print(f"Successfully set control state to ODrive {node_id}")

    except Exception as e:
        print(f"Error connecting to ODrive {node_id}: {str(e)}")




# Function to print encoder feedback for a specific O-Drive
def get_encoder_estimate(node_id):
    for msg in bus:
        if msg.arbitration_id == (node_id << 5 | 0x09):  # 0x09: Get_Encoder_Estimates
            pos, vel = struct.unpack('<ff', bytes(msg.data))
            print(f"O-Drive {node_id} - pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")


# Function to print torque target and torque estimate for a specific O-Drive
def get_torque(node_id):
    for msg in bus:
        if msg.arbitration_id == (node_id << 5 | 0x1C):  # 0x1C: Get_Torques
            torque_target, torque_estimate = struct.unpack('<ff', bytes(msg.data))
            print(f"O-Drive {node_id} - Torque Target: {torque_target:.3f} [Nm], Torque Estimate: {torque_estimate:.3f} [Nm]")



# Function to print torque target and torque estimate for a specific O-Drive
def get_bus_voltage_current(node_id):
    for msg in bus:
        if msg.arbitration_id == (node_id << 5 | 0x17):  # 0x17: Get_Bus_Voltage_Current
            bus_voltage, bus_current = struct.unpack('<ff', bytes(msg.data))
            print(f"O-Drive {node_id} - Bus Voltage: {bus_voltage:.3f} [V], Bus Curretn: {bus_current:.3f} [A]")



# Function to print current setpoint and current measured for a specific O-Drive
def get_iq_setpoint_measured(node_id):
    for msg in bus:
        if msg.arbitration_id == (node_id << 5 | 0x14):  # 0x14: Get_Iq
            iq_setpoint, iq_measured = struct.unpack('<ff', bytes(msg.data))
            print(f"O-Drive {node_id} - Iq Setpoint: {iq_setpoint:.3f} [A], Iq Measured: {iq_measured:.3f} [A]")

