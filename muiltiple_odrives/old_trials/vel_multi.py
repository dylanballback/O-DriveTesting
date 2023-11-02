import can
import struct
import threading
import time

# List of node_ids for the 4 O-Drives
node_ids = [0, 1, 2, 3]

bus = can.interface.Bus("can0", bustype="socketcan")

def flush_can_buffer():
    """Flush CAN RX buffer to ensure no old pending messages."""
    while not (bus.recv(timeout=0) is None): pass

def set_closed_loop_control(node_id):
    """Put a specific O-Drive into closed loop control mode."""
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x07), # 0x07: Set_Axis_State
        data=struct.pack('<I', 8), # 8: AxisState.CLOSED_LOOP_CONTROL
        is_extended_id=False
    ))

    # Wait for the O-Drive to enter closed loop control mode
    for msg in bus:
        if msg.arbitration_id == (node_id << 5 | 0x01): # 0x01: Heartbeat
            error, state, result, traj_done = struct.unpack('<IBBB', bytes(msg.data[:7]))
            if state == 8: # 8: AxisState.CLOSED_LOOP_CONTROL
                break

def set_vel(node_id, vel_set):
    """Set the velocity for a specific O-Drive."""
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x0d), # 0x0d: Set_Input_Vel
        data=struct.pack('<ff', float(vel_set), 0.0),
        is_extended_id=False
    ))

def velocity_ramp(node_id):
    """Gradually increase and then decrease the velocity for a specific O-Drive."""
    for velocity in range(11):  # 0 to 10
        set_vel(node_id, velocity)
        time.sleep(1)
    for velocity in reversed(range(11)):  # 10 to 0
        set_vel(node_id, velocity)
        time.sleep(1)

def print_feedback():
    """Print position and velocity feedback for all O-Drives."""
    while True:
        for node_id in node_ids:
            # Request encoder estimates
            bus.send(can.Message(
                arbitration_id=(node_id << 5 | 0x09), # 0x09: Get_Encoder_Estimates
                is_extended_id=False
            ))
            msg = bus.recv()
            if msg and msg.arbitration_id == (node_id << 5 | 0x09):
                pos, vel = struct.unpack('<ff', bytes(msg.data))
                print(f"O-Drive {node_id} - pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")
        time.sleep(1)  # Print feedback every second

flush_can_buffer()

# Set each O-Drive to closed loop control mode
for node_id in node_ids:
    set_closed_loop_control(node_id)

# Start a thread to print feedback for all O-Drives
feedback_thread = threading.Thread(target=print_feedback)
feedback_thread.start()

# Create and start threads for each O-Drive to control their velocity
velocity_threads = []
for node_id in node_ids:
    t = threading.Thread(target=velocity_ramp, args=(node_id,))
    velocity_threads.append(t)
    t.start()

# Wait for all velocity control threads to complete
for t in velocity_threads:
    t.join()

# Stop the feedback thread once all velocity control threads have completed
feedback_thread.join()

bus.shutdown()
