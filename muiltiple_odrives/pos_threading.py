import can
import struct
import threading
import time
import sys

# Define the node IDs for your ODrives
odrive_node_ids = [0, 1, 2]

# Function to set position for a specific ODrive
def set_position(node_id, position, vel_ff=0.0, torque_ff=0.0):
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x00c),  # Using the correct CMD ID for Set_Input_Pos
        data=struct.pack('<f', float(position)),  # Packing only the position for now
        is_extended_id=False
    ))

# Define the CAN bus interface
bus = can.interface.Bus("can0", bustype="socketcan")

# Flush CAN RX buffer
while not (bus.recv(timeout=0) is None):
    pass

# Function to connect to and configure an ODrive
def connect_odrive(node_id):
    print(f"Attempting to connect to ODrive {node_id}...")
    try:
        # Connection code goes here
        print(f"Successfully connected to ODrive {node_id}")
        # Initialize its position to 0 after connecting
        set_position(node_id, 0)
    except Exception as e:
        print(f"Error connecting to ODrive {node_id}: {str(e)}")

# Connect to and configure each ODrive
for node_id in odrive_node_ids:
    connect_odrive(node_id)

# Function to move a single ODrive's position
def move_single_odrive_position(node_id):
    position = 0
    while True:
        try:
            position += 300
            print(f"Setting position for ODrive {node_id} to {position}")  # Debug print
            set_position(node_id, position)
            time.sleep(3)
        except Exception as e:
            print(f"Error in move_single_odrive_position for ODrive {node_id}: {str(e)}")

# Start threads to move position for each ODrive one at a time
for node_id in odrive_node_ids:
    print(f"Starting thread for ODrive {node_id}")  # Debug print
    position_thread = threading.Thread(target=move_single_odrive_position, args=(node_id,))
    position_thread.daemon = True  # This ensures the thread will be terminated when the main program exits
    position_thread.start()

# Main loop to keep the script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nKeyboard interrupt detected. Stopping all ODrives.")
    for node_id in odrive_node_ids:
        set_position(node_id, 0)  # Reset position to 0 for all ODrives
    bus.shutdown()  # Close the CAN bus connection
    sys.exit(0)  # Exit the script
