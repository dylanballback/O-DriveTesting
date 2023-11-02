import can
import struct
import time


"""
11/1/23
This code is for controlling 3 O-Drives using position control.

You have to ensure that each O-Drive is configured using the Web-GUI first and set to postion control. 

You also have to go to the inspector tab on the GUI and change the 'node_ID' of two of the O-Drives to '1' and '2' then save the configuration.

Then this code will set each of the 3 O-Drives to close axis state, and change the position of each O-Drive by 10 turns every 2 seconds for a total of 10 times.

When you keyboard interrupt the position will be set to 0 for all O-Drives and the CAN Bus connection will be shutdown.
"""


# Define the node IDs for your ODrives
odrive_node_ids = [0, 1, 2]

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



# Function to set position for a specific O-Drive
def set_position(node_id, position, velocity_feedforward=0, torque_feedforward=0):
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x0C),
        data=struct.pack('<fhh', float(position), velocity_feedforward, torque_feedforward),
        is_extended_id=False
    ))
    print(f"Successfully moved ODrive {node_id} to {position}")
    


# Function to set velocity for a specific O-Drive
def set_velocity(node_id, velocity, torque_feedforward=0.0):
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x0d),  # 0x0d: Set_Input_Vel
        data=struct.pack('<ff', velocity, torque_feedforward),
        is_extended_id=False
    ))


# Function to print encoder feedback for a specific O-Drive
def print_feedback(node_id):
    for msg in bus:
        if msg.arbitration_id == (node_id << 5 | 0x09):  # 0x09: Get_Encoder_Estimates
            pos, vel = struct.unpack('<ff', bytes(msg.data))
            print(f"O-Drive {node_id} - pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")



if __name__ == "__main__":
    
    try:
        velocity = 0
        flush_can_buffer()

        for node_id in odrive_node_ids:
            set_control_state(node_id)
            time.sleep(2)

        
        for x in range(10):
            for node_id in odrive_node_ids:
                velocity += 1
                set_velocity(node_id, velocity)
                #print_feedback(node_id)
                time.sleep(2)
        
        

        """
        Testing if there is a delay between O-Drives starting without threading.
        set_position(0, 100)
        set_position(1, 100)
        set_position(2, 100)
        """
        
        

    except KeyboardInterrupt:
        for node_id in odrive_node_ids:
            set_position(node_id, 0)
        bus.shutdown()

