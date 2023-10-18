import can
import struct
import threading
import time
import signal
import sys

# Define the node IDs for your ODrives
odrive_node_ids = [0, 1, 2]
bus_lock = threading.Lock()

# Function to set position for a specific ODrive
def set_position(node_id, position):
    with bus_lock:
        bus.send(can.Message(
            arbitration_id=(node_id << 5 | 0x0a),
            data=struct.pack('<ff', float(position), 0.0),
            is_extended_id=False
        ))

# Define the CAN bus interface
bus = can.interface.Bus("can0", bustype="socketcan")

# Flush CAN RX buffer
while not (bus.recv(timeout=0) is None):
    pass

# Function to get position and velocity for a specific ODrive
def get_pos_vel(node_id):
    while True:
        with bus_lock:
            for msg in bus:
                if msg.arbitration_id == (node_id << 5 | 0x09):
                    pos, vel = struct.unpack('<ff', bytes(msg.data))
                    # Ensure each print statement goes to a new line
                    print(f"ODrive {node_id} - Position: {pos:.3f} [turns], Velocity: {vel:.3f} [turns/s]")
                    time.sleep(0.5)
                    break

# Function to connect to and configure an ODrive
def connect_odrive(node_id):
    print(f"Attempting to connect to ODrive {node_id}...")
    try:
        # Connection code goes here
        print(f"Successfully connected to ODrive {node_id}")

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

# Start threads
for node_id in odrive_node_ids:
    # Start a thread for each ODrive to move its position
    position_thread = threading.Thread(target=move_odrive_position, args=(node_id,))
    position_thread.daemon = True
    position_thread.start()

    # Start a thread for each ODrive to continuously fetch and print its position and velocity
    pos_vel_thread = threading.Thread(target=get_pos_vel, args=(node_id,))
    pos_vel_thread.daemon = True
    pos_vel_thread.start()

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nKeyboard interrupt detected. Stopping all ODrives.")
    # Stop all motors
    for node_id in odrive_node_ids:
        set_position(node_id, 0)
    bus.shutdown()
    sys.exit(0)
