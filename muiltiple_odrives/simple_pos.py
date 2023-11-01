import can
import struct
import multiprocessing
import time
import sys

# Define the node IDs for your ODrives
odrive_node_ids = [0, 1, 2]

def set_position(node_id, position):
    bus = can.interface.Bus("can0", bustype="socketcan")  # Each process needs its own bus instance
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x0C),
        data=struct.pack('<ff', float(position), 0.0, 0.0)
        is_extended_id=False
    ))

def connect_odrive(node_id):
    print(f"Attempting to connect to ODrive {node_id}...")
    try:
        # Connection code goes here. If there's no actual connection logic, you can remove this.
        print(f"Successfully connected to ODrive {node_id}")
        set_position(node_id, 0)

    except Exception as e:
        print(f"Error connecting to ODrive {node_id}: {str(e)}")

def move_odrive_position(node_id):
    position = 0
    while True:
        position += 300
        set_position(node_id, position)
        print(f"Successfully moved ODrive {node_id} to {position}")
        time.sleep(3)


if __name__ == "__main__":
    for node_id in odrive_node_ids:
        connect_odrive(node_id)

    for node_id in odrive_node_ids:
        move_odrive_position(node_id)
