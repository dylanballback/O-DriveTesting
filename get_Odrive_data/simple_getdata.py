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




"""
#Using RTR to get data (so you don't have to set cyclic message rate)

import can
import struct
import time

odrive_node_ids = [0, 1]
bus = can.interface.Bus("can0", bustype="socketcan")

def send_rtr_message(node_id, request_id):
    try:
        # Create an RTR frame
        rtr_frame = can.Message(
            arbitration_id=(node_id << 5 | request_id),
            is_remote_frame=True,
            is_extended_id=False
        )

        # Send the RTR frame
        bus.send(rtr_frame)

        # Wait for a response
        response = bus.recv(timeout=1.0)

        if response:
            handle_response(node_id, request_id, response)
        else:
            print(f"No response received for ODrive {node_id}, request_id {request_id}")

    except Exception as e:
        print(f"Error sending RTR message to ODrive {node_id}, request_id {request_id}: {str(e)}")


def handle_response(node_id, request_id, response):
    if request_id == 0x07:  # Set_Axis_State
        handle_set_control_state_response(node_id, response)
    elif request_id == 0x09:  # Get_Encoder_Estimates
        handle_encoder_estimate_response(node_id, response)
    elif request_id == 0x1C:  # Get_Torques
        handle_torque_response(node_id, response)
    elif request_id == 0x17:  # Get_Bus_Voltage_Current
        handle_bus_voltage_current_response(node_id, response)
    elif request_id == 0x14:  # Get_Iq
        handle_iq_setpoint_measured_response(node_id, response)
    else:
        print(f"Unhandled response for ODrive {node_id}, request_id {request_id}")


def handle_set_control_state_response(node_id, response):
    # Add logic to handle the response for Set_Axis_State if needed
    pass


def handle_encoder_estimate_response(node_id, response):
    pos, vel = struct.unpack('<ff', bytes(response.data))
    print(f"O-Drive {node_id} - pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")


def handle_torque_response(node_id, response):
    torque_target, torque_estimate = struct.unpack('<ff', bytes(response.data))
    print(f"O-Drive {node_id} - Torque Target: {torque_target:.3f} [Nm], Torque Estimate: {torque_estimate:.3f} [Nm]")


def handle_bus_voltage_current_response(node_id, response):
    bus_voltage, bus_current = struct.unpack('<ff', bytes(response.data))
    print(f"O-Drive {node_id} - Bus Voltage: {bus_voltage:.3f} [V], Bus Current: {bus_current:.3f} [A]")


def handle_iq_setpoint_measured_response(node_id, response):
    iq_setpoint, iq_measured = struct.unpack('<ff', bytes(response.data))
    print(f"O-Drive {node_id} - Iq Setpoint: {iq_setpoint:.3f} [A], Iq Measured: {iq_measured:.3f} [A]")


if __name__ == "__main__":
    for node_id in odrive_node_ids:
        try:
            # Example: Send RTR for Set_Axis_State
            send_rtr_message(node_id, 0x07)

            # Example: Send RTR for Get_Encoder_Estimates
            send_rtr_message(node_id, 0x09)

            # Example: Send RTR for Get_Torques
            send_rtr_message(node_id, 0x1C)

            # Example: Send RTR for Get_Bus_Voltage_Current
            send_rtr_message(node_id, 0x17)

            # Example: Send RTR for Get_Iq
            send_rtr_message(node_id, 0x14)

        except KeyboardInterrupt:
            print("KeyboardInterrupt: Exiting loop.")
            break

        time.sleep(0.1)  # Adjust the sleep duration as needed
"""
