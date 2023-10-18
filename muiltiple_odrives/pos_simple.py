import can
import struct
import time
import sys

odrive_node_ids = [0, 1, 2]

def set_position(node_id, position):
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x0a),
        data=struct.pack('<ff', float(position), 0.0),
        is_extended_id=False
    ))

bus = can.interface.Bus("can0", bustype="socketcan")

for node_id in odrive_node_ids:
    set_position(node_id, 0)

positions = {node_id: 0 for node_id in odrive_node_ids}

try:
    while True:
        for node_id in odrive_node_ids:
            positions[node_id] += 300
            set_position(node_id, positions[node_id])
        time.sleep(3)

except KeyboardInterrupt:
    print("\nKeyboard interrupt detected. Stopping all ODrives.")
    for node_id in odrive_node_ids:
        set_position(node_id, 0)
    bus.shutdown()
    sys.exit(0)
