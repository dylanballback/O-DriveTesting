import asyncio
import can
import struct

# Example values for node_id and bus, you should replace them with your actual values
node_id = 1
bus = can.interface.Bus(channel='can0', bustype='socketcan')

# Set velocity function to vel_set turns/s
async def set_vel(vel_set):
    bus.send(can.Message(
        arbitration_id=(node_id << 5 | 0x0d),  # 0x0d: Set_Input_Vel
        data=struct.pack('<ff', float(vel_set), 0.0),  # 1.0: velocity, 0.0: torque feedforward
        is_extended_id=False
    ))

# Print encoder feedback
async def get_pos_vel():
    while True:
        for msg in bus:
            if msg.arbitration_id == (node_id << 5 | 0x09):  # 0x09: Get_Encoder_Estimates
                pos, vel = struct.unpack('<ff', bytes(msg.data))
                print(f"pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")

# This task runs the print_values and set_vel concurrently
async def print_values_and_set_vel():
    value = 0
    step = 0.25

    while value <= 10:
        print(value)
        await set_vel(value)  # Set velocity with the current value
        value += step
        await asyncio.sleep(1)

async def main():
    # Create a task for get_pos_vel to run continuously in the background
    background_task = asyncio.create_task(get_pos_vel())
    
    # Run print_values_and_set_vel
    await print_values_and_set_vel()
    
    # Cancel the background_task when print_values_and_set_vel completes
    background_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
