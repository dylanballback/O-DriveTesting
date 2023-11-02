import can

def set_odrive_mode(channel, node_id, control_mode_str, input_mode_str):
    # Define control mode mappings
    CONTROL_MODES = {
        "Voltage Control": 0x0,
        "Torque Control": 0x1,
        "Velocity Control": 0x2,  # Corrected spelling
        "Position Control": 0x3,
    }

    # Define input mode mappings
    INPUT_MODES = {
        "Inactive": 0x0,
        "Passthrough": 0x1,
        "Velocity Ramp": 0x2,  # Corrected spelling
        "Position Filter": 0x3,
        "Mix Channels": 0x4,
        "Trap Traj": 0x5,
        "Torque Ramp": 0x6,
        "Mirror": 0x7,
        "Tuning": 0x8,
    }

    # Check valid modes
    if control_mode_str not in CONTROL_MODES:
        raise ValueError(f"Invalid control mode: {control_mode_str}")
    
    if input_mode_str not in INPUT_MODES:
        raise ValueError(f"Invalid input mode: {input_mode_str}")

    # Get the selected modes
    control_mode = CONTROL_MODES[control_mode_str]
    input_mode = INPUT_MODES[input_mode_str]

    # Define the CAN message ID. Assuming standard CAN 11-bit ID.
    # Here, I'm assuming node_id is part of the CAN ID, but adjust as necessary.
    can_id = 0x00b | (node_id << 4)

    # Construct the data payload
    data = control_mode.to_bytes(4, 'little') + input_mode.to_bytes(4, 'little')

    # Create and send the CAN message
    message = can.Message(arbitration_id=can_id, data=data, is_extended_id=False)
    bus = can.interface.Bus(channel=channel, bustype='socketcan')
    bus.send(message)
    bus.shutdown()

# Usage example:
set_odrive_mode('can0', 0x01, "Torque Control", "Passthrough")
