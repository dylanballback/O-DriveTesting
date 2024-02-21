import pyodrivecan
import asyncio
import math

mass = 0.2  # Kg
length = 0.1  # Meters

async def controller(odrive):
    while odrive.running:
        current_position_rev = await odrive.get_position()  # Assuming this is async and correct method to get position
        current_position_rad = current_position_rev * 2 * math.pi

        # Calculate next torque
        next_torque = math.sin(current_position_rad) * mass * length * 9.8

        # Limit next_torque to between -0.129 and 0.129
        next_torque = max(-0.129, min(0.129, next_torque))
        
        # Set the calculated torque
        odrive.set_torque(next_torque)  # Assuming this is an async method
        print(f"Current position {current_position_rev} (revs), Torque Set to {next_torque} (Nm)")

        await asyncio.sleep(0.015)  # 15ms sleep, adjust based on your control loop requirements

if __name__ == "__main__":
    # Initialize ODriveCAN to node_id 10 
    odrive = pyodrivecan.ODriveCAN(10)
    odrive.initCanBus()
    odrive.running = True  # Ensure there's a mechanism to update this flag
    
    try:
        asyncio.gather(
            odrive.loop(),
            controller(odrive)
            )  
    except KeyboardInterrupt:
        print("KeyboardInterrupt caught, stopping...")
        odrive.running = False
        # Perform any additional cleanup if necessary
