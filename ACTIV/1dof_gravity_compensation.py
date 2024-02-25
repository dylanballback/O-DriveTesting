import pyodrivecan
import asyncio
import math
from datetime import datetime, timedelta


mass = 0.085  # Kg
length = 0.1  # Meters

async def controller(odrive):
    await asyncio.sleep(1)

    #Run for set time delay example runs for 15 seconds.
    stop_at = datetime.now() + timedelta(seconds=10000)
    while datetime.now() < stop_at:
        current_position_rev = odrive.position

        # Convert to radians and adjust to be within -pi to pi
        current_position_rad = (current_position_rev * 2 * math.pi) % (2 * math.pi)
        if current_position_rad > math.pi:
            current_position_rad -= 2 * math.pi

        # Calculate next torque
        next_torque = math.sin(current_position_rad) * mass * length * 9.8

        # Limit next_torque to between -0.129 and 0.129
        next_torque = max(-0.1, min(0.1, next_torque))
        
        # Set the calculated torque
        odrive.set_torque(next_torque)  # Assuming this is an async method
        print(f"Current position {current_position_rev} (revs), Current Position {current_position_rad} (rad), Torque Set to {next_torque} (Nm)")

        await asyncio.sleep(0)  # 15ms sleep, adjust based on your control loop requirements


#Set up Node_ID 10 ACTIV NODE ID = 10
odrive = pyodrivecan.ODriveCAN(0)

# Run multiple busses.
async def main():
    odrive.clear_errors(identify=False)
    print("Cleared Errors")
    await asyncio.sleep(1)

    #Initalize odrive
    odrive.initCanBus()

    
    print("Put Arm at bottom center to calibrate Zero Position.")
    await asyncio.sleep(5)
    odrive.set_absolute_position(position=0)
    await asyncio.sleep(1)
    current_position = odrive.position
    print(f"Encoder Absolute Position Set: {current_position}")

    #odrive.setAxisState("closed_loop_control")

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
        odrive.estop()
        
        # Perform any additional cleanup if necessary
