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

def clear_can_buffer(max_iterations=100):
    """
    Clear any pending messages in the CAN bus buffer.
    
    Args:
    - max_iterations: Maximum number of messages to clear to avoid infinite loop.
    """
    count = 0
    while count < max_iterations:
        msg = bus.recv(timeout=0.1)
        if msg is None:
            break
        print(f"Clearing message: {msg}")  # Printing the message being cleared
        count += 1
    if count == max_iterations:
        print("Warning: Reached max iterations while clearing buffer. Buffer might not be fully cleared.")


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
    bus = can.interface.Bus("can0", bustype="socketcan")
    print("CAN bus initialized!")
    print("Clearing CAN bus buffer...")  # Add this
    clear_can_buffer()
    print("Buffer cleared!")  # Add this

    for node_id in odrive_node_ids:
        print(f"Attempting to connect to ODrive {node_id}...")  # This already exists in the function but adding here for emphasis
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
