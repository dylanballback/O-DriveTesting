import can
import struct
import threading
import time
import sys

# Define the node IDs for your ODrives
odrive_node_ids = [0, 1, 2]

# Function to set position for a specific ODrive
def set_position(node_id, position):
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x00c),
        data=struct.pack('<ff', float(position), 0.0),
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

# Set up a thread to move each ODrive's position by +300 turns every 3 seconds
def move_odrive_position(node_id):
    position = 0
    while True:
        position += 300
        set_position(node_id, position)
        time.sleep(3)

# Start threads to move position
for node_id in odrive_node_ids:
    position_thread = threading.Thread(target=move_odrive_position, args=(node_id,))
    position_thread.daemon = True
    position_thread.start()

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nKeyboard interrupt detected. Stopping all ODrives.")
    for node_id in odrive_node_ids:
        set_position(node_id, 0)
    bus.shutdown()
    sys.exit(0)
