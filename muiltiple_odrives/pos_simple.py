import can
import struct
import time
import sys

# List of node IDs for the ODrives to be controlled.
odrive_node_ids = [0, 1, 2]

# Define the timeout period to wait for a heartbeat message.
HEARTBEAT_TIMEOUT = 2.0  # timeout in seconds

def set_position(node_id, position):
    """
    Set the position of a specific ODrive.

    Args:
    - node_id: The ID of the ODrive.
    - position: Desired position.
    """
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x0a),  # Command to set position
        data=struct.pack('<ff', float(position), 0.0),
        is_extended_id=False
    ))

def clear_can_buffer():
    """
    Clear any pending messages in the CAN bus buffer.
    """
    while True:
        msg = bus.recv(timeout=0.1)
        if msg is None:
            pass

def check_heartbeat(node_id):
    """
    Check the heartbeat of a specific ODrive to ensure it's in the CLOSED_LOOP_CONTROL state.

    Args:
    - node_id: The ID of the ODrive.

    Returns:
    - True if the ODrive is in the correct state, else False.
    """
    start_time = time.time()
    while time.time() - start_time < HEARTBEAT_TIMEOUT:
        msg = bus.recv(timeout=HEARTBEAT_TIMEOUT)
        if msg and msg.arbitration_id == (node_id << 5 | 0x01):  # Heartbeat message
            error, state, _, _ = struct.unpack('<IBBB', bytes(msg.data[:7]))
            if state == 8:  # Check if state is CLOSED_LOOP_CONTROL
                return True
            else:
                print(f"ODrive {node_id} reported an error code: {error}")
                return False
    print(f"ODrive {node_id} heartbeat timeout!")
    return False

def connect_odrive(node_id):
    """
    Connect to a specific ODrive, set it to closed-loop control mode, and check its heartbeat.

    Args:
    - node_id: The ID of the ODrive.
    """
    print(f"Attempting to connect to ODrive {node_id}...")

    # Simulate some delay for the connection (this can be replaced with actual logic if needed)
    time.sleep(0.5)

    # Send command to transition ODrive to closed-loop control state
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x07),
        data=struct.pack('<I', 8),  # 8 corresponds to CLOSED_LOOP_CONTROL state
        is_extended_id=False
    ))

    # Check the heartbeat to confirm the state transition
    if check_heartbeat(node_id):
        print(f"Successfully connected and transitioned ODrive {node_id} to CLOSED_LOOP_CONTROL state.")
        set_position(node_id, 0)
    else:
        print(f"Failed to connect to ODrive {node_id} due to heartbeat issues.")

try:
    # Initialize the CAN bus
    bus = can.interface.Bus("can0", bustype="socketcan")
    print("CAN bus initialized!")
    
    # Clear the CAN bus buffer of any stale messages
    clear_can_buffer()

    # Iterate over each ODrive, connect to it, and check its heartbeat
    for node_id in odrive_node_ids:
        connect_odrive(node_id)

    # Dictionary to track the position of each ODrive
    positions = {node_id: 0 for node_id in odrive_node_ids}

    # Main control loop: Move each ODrive by 300 turns every 3 seconds
    while True:
        for node_id in odrive_node_ids:
            positions[node_id] += 300
            set_position(node_id, positions[node_id])
        time.sleep(3)

# Handle keyboard interrupts to safely stop the ODrives
except KeyboardInterrupt:
    print("\nKeyboard interrupt detected. Stopping all ODrives.")
    for node_id in odrive_node_ids:
        set_position(node_id, 0)
    bus.shutdown()
    sys.exit(0)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit(1)
