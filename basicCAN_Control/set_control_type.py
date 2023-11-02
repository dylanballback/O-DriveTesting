import can

# Definitions for control modes based on provided table
CONTROL_MODES = {
    "torque": 0x1,
    "velocity": 0x2,
    "position": 0x3
}

COMMAND_ID = 0x0b  # As provided in your previous information

def set_odrive_mode(node_id, mode, channel='can0'):
    """Set the control mode of ODrive with a specific node_id via CAN.
    
    Parameters:
    - node_id (int): CAN node ID of the ODrive.
    - mode (str): One of 'torque', 'velocity', or 'position'.
    - channel (str): CAN channel. Default is 'can0'.
    
    Returns:
    - bool: True if successful, False otherwise.
    """
    
    if mode not in CONTROL_MODES:
        print(f"Invalid mode {mode}. Choose one of {', '.join(CONTROL_MODES.keys())}.")
        return False

    # Create a CAN message
    can_msg = can.Message(
        arbitration_id=node_id,
        data=[CONTROL_MODES[mode], 0x00, 0x00, 0x00],  # Set the control mode and pad with zeros
        is_extended_id=False
    )

    try:
        # Initialize the CAN bus interface
        bus = can.interface.Bus(channel=channel, bustype='socketcan')
        
        # Send the message
        bus.send(can_msg)
        
        # Cleanup
        bus.shutdown()

        return True

    except can.CanError:
        print("Failed to send CAN message.")
        return False


# Example usage:
node_id_example = 0  # Replace with your ODrive's node ID
set_odrive_mode(node_id_example, "torque")
