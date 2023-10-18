import can
import struct
import threading
import time
import signal
import sys

# Define the node IDs for your ODrives
odrive_node_ids = [0, 1, 2]  # Adjust these based on your ODrive configuration

# Function to set position for a specific ODrive
def set_position(node_id, position):
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x0a),  # 0x0a: Set_Input_Pos
        data=struct.pack('<ff', float(position), 0.0),  # Position, velocity feedforward
        is_extended_id=False
    ))

# Function to stop all ODrives
def stop_all_odrives():
    for node_id in odrive_node_ids:
        set_position(node_id, 0)  # Set position to 0 to stop motion

# Define the CAN bus interface
bus = can.interface.Bus("can0", bustype="socketcan")

# Flush CAN RX buffer so there are no more old pending messages
while not (bus.recv(timeout=0) is None):
    pass

# Set up a thread to monitor ODrive positions and velocities
def monitor_odrive():
    while True:
        for node_id in odrive_node_ids:
            get_pos_vel(node_id)
        time.sleep(1)  # Adjust the update interval as needed

# Function to get position and velocity for a specific ODrive
def get_pos_vel(node_id):
    for msg in bus:
        if msg.arbitration_id == (node_id << 5 | 0x09):  # 0x09: Get_Encoder_Estimates
            pos, vel = struct.unpack('<ff', bytes(msg.data))
            print(f"ODrive {node_id} - Position: {pos:.3f} [turns], Velocity: {vel:.3f} [turns/s]")

# Function to connect to and configure an ODrive
def connect_odrive(node_id):
    try:
        # Add code here to connect to the ODrive and configure it
        # You can print messages indicating the connection status

        print(f"Connecting to ODrive {node_id}...")
        # Your connection code goes here

        print(f"Successfully connected to ODrive {node_id}")

    except Exception as e:
        print(f"Error connecting to ODrive {node_id}: {str(e)}")

# Connect to and configure each ODrive
for node_id in odrive_node_ids:
    connect_odrive(node_id)

# Start the monitoring thread
monitor_thread = threading.Thread(target=monitor_odrive)
monitor_thread.daemon = True
monitor_thread.start()

try:
    while True:
        for node_id in odrive_node_ids:
            set_position(node_id, 200)  # Set the desired position to 200 turns
        time.sleep(3)  # Wait for 3 seconds before updating positions again

except KeyboardInterrupt:
    print("Keyboard interrupt detected. Stopping all ODrives.")
    stop_all_odrives()
    bus.shutdown()
    sys.exit(0)
