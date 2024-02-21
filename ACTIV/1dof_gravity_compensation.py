import pyodrivecan
import asyncio
import math
from datetime import datetime, timedelta


mass = 0.2  # Kg
length = 0.1  # Meters

async def controller(odrive):
    #Run for set time delay example runs for 15 seconds.
    stop_at = datetime.now() + timedelta(seconds=15)
    while datetime.now() < stop_at:
        current_position_rev = await odrive.get_position()  # Assuming this is async and correct method to get position
        current_position_rad = current_position_rev * 2 * math.pi

        # Calculate next torque
        next_torque = math.sin(current_position_rad) * mass * length * 9.8

        # Limit next_torque to between -0.129 and 0.129
        next_torque = max(-0.129, min(0.129, next_torque))
        
        # Set the calculated torque
        #odrive.set_torque(next_torque)  # Assuming this is an async method
        print(f"Current position {current_position_rev} (revs), Torque Set to {next_torque} (Nm)")

        await asyncio.sleep(0.015)  # 15ms sleep, adjust based on your control loop requirements


#Set up Node_ID 10
odrive = pyodrivecan.ODriveCAN(10)

# Run multiple busses.
async def main():
    #Initalize odrive
    odrive.initCanBus()

    #add each odrive to the async loop so they will run.
    await asyncio.gather(
        odrive.loop(),
        controller(odrive) 
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("KeyboardInterrupt caught, stopping...")
        odrive.set_torque(0)
        odrive.running = False
        # Perform any additional cleanup if necessary
