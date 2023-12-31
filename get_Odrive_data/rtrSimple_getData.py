import can
import struct
import time

odrive_node_ids = [0]
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



def get_encoder_estimate_rtr(node_id):
    request_id = 0x09
    send_rtr_message(node_id, request_id)

    # Wait for a response
    response = bus.recv(timeout=1.0)

    if response:
        pos, vel = struct.unpack('<ff', bytes(response.data))
        print(f"O-Drive {node_id} - pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")
    else:
        print(f"No response received for ODrive {node_id}, request_id {request_id}")


def get_torque_rtr(node_id):
    request_id = 0x1C
    send_rtr_message(node_id, request_id)

    # Wait for a response
    response = bus.recv(timeout=1.0)

    if response:
        torque_target, torque_estimate = struct.unpack('<ff', bytes(response.data))
        print(f"O-Drive {node_id} - Torque Target: {torque_target:.3f} [Nm], Torque Estimate: {torque_estimate:.3f} [Nm]")
    else:
        print(f"No response received for ODrive {node_id}, request_id {request_id}")


def get_bus_voltage_current_rtr(node_id):
    request_id = 0x17
    send_rtr_message(node_id, request_id)

    # Wait for a response
    response = bus.recv(timeout=1.0)

    if response:
        bus_voltage, bus_current = struct.unpack('<ff', bytes(response.data))
        print(f"O-Drive {node_id} - Bus Voltage: {bus_voltage:.3f} [V], Bus Current: {bus_current:.3f} [A]")
    else:
        print(f"No response received for ODrive {node_id}, request_id {request_id}")


def get_iq_setpoint_measured_rtr(node_id):
    request_id = 0x14
    send_rtr_message(node_id, request_id)

    # Wait for a response
    response = bus.recv(timeout=1.0)

    if response:
        iq_setpoint, iq_measured = struct.unpack('<ff', bytes(response.data))
        print(f"O-Drive {node_id} - Iq Setpoint: {iq_setpoint:.3f} [A], Iq Measured: {iq_measured:.3f} [A]")
    else:
        print(f"No response received for ODrive {node_id}, request_id {request_id}")


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

    except Exception as e:
        print(f"Error sending RTR message to ODrive {node_id}, request_id {request_id}: {str(e)}")


if __name__ == "__main__":
    for node_id in odrive_node_ids:
        try:
            get_encoder_estimate_rtr(node_id)
            get_torque_rtr(node_id)
            get_bus_voltage_current_rtr(node_id)
            get_iq_setpoint_measured_rtr(node_id)

        except KeyboardInterrupt:
            print("KeyboardInterrupt: Exiting loop.")
            break

        time.sleep(0.1)  # Adjust the sleep duration as needed
