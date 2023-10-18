import can
import struct
import threading
import time
import signal
import sys

# Number of O-Drives you want to control. Change this value as needed (2, 4, 9, etc.).
NUM_MOTORS = 4  # Example: 4 O-Drives

# Generate a list of node_ids for the O-Drives based on NUM_MOTORS.
node_ids = list(range(NUM_MOTORS))

bus = can.interface.Bus("can0", bustype="socketcan")

def flush_can_buffer():
    """Flush CAN RX buffer to ensure no old pending messages."""
    while not (bus.recv(timeout=0) is None): pass

def set_closed_loop_control(node_id):
    """Put a specific O-Drive into closed loop control mode."""
    try:
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
        print(f"Connected to O-Drive {node_id}")
    except Exception as e:
        print(f"Error connecting to O-Drive {node_id}: {str(e)}")

def set_pos(node_id, pos_set):
    """Set the position for a specific O-Drive."""
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x0e), # 0x0e: Set_Input_Pos
        data=struct.pack('<f', float(pos_set)),
        is_extended_id=False
    ))

def move_motor(node_id):
    """Move a specific motor 200 turns every 3 seconds."""
    while not exit_program:
        set_pos(node_id, 200.0)
        time.sleep(3)
        set_pos(node_id, 0.0)
        time.sleep(3)

def print_feedback():
    """Print position feedback for all O-Drives."""
    while not exit_program:
        for node_id in node_ids:
            # Request encoder estimates
            bus.send(can.Message(
                arbitration_id=(node_id << 5 | 0x09), # 0x09: Get_Encoder_Estimates
                is_extended_id=False
            ))
            msg = bus.recv()
            if msg and msg.arbitration_id == (node_id << 5 | 0x09):
                pos, _ = struct.unpack('<ff', bytes(msg.data))
                print(f"O-Drive {node_id} - pos: {pos:.3f} [turns]")
        time.sleep(1)  # Print feedback every second

def handle_keyboard_interrupt(signal, frame):
    global exit_program
    print("Keyboard interrupt received. Exiting...")
    exit_program = True
    bus.shutdown()
    sys.exit(0)

# Register a handler for the keyboard interrupt (Ctrl+C)
signal.signal(signal.SIGINT, handle_keyboard_interrupt)

exit_program = False
flush_can_buffer()

# Check connection to each O-Drive and set to closed loop control mode
for node_id in node_ids:
    set_closed_loop_control(node_id)

# Start a thread to print feedback for all O-Drives
feedback_thread = threading.Thread(target=print_feedback)
feedback_thread.start()

# Create and start threads for each O-Drive to control their position
position_threads = []
for node_id in node_ids:
    t = threading.Thread(target=move_motor, args=(node_id,))
    position_threads.append(t)
    t.start()

# Wait for all position control threads to complete
for t in position_threads:
    t.join()

# Stop the feedback thread once all position control threads have completed
feedback_thread.join()

bus.shutdown()
