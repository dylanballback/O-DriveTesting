import asyncio
# Assuming ODriveCAN and TorqueReactionTestDatabase classes are modified or wrapped for async operation

async def main():
    # Initialize ODriveCAN to node_id 0 
    odrive = ODriveCAN(0)
    await odrive.initCanBus()  # This needs to be an async method or wrapped in asyncio.to_thread() if not

    db_name = "torqueReactionTestDatabase.db"
    torque_reaction_test_database = TorqueReactionTestDatabase(db_name)
    # When initializing the database for the first time
    # await db.create_tables() if create_tables is async
    trial_id = await asyncio.to_thread(torque_reaction_test_database.add_trial)
    print(f"Added Trial with ID: {trial_id}")

    # Define your torque values here
    torques = [0, 0.3, 0]
    measurement_interval = 0.5  # Time between measurements
    torque_change_delay = 5  # Time to wait before changing torque

    # Capture the start time
    start_time = asyncio.get_running_loop().time()

    # Iterate through each torque setting
    for torque in torques:
        # Set torque
        await asyncio.to_thread(odrive.set_torque, torque)  # If set_torque is not async
        print(f"Torque set to {torque} Nm")

        # Calculate elapsed time since start
        elapsed_time = asyncio.get_running_loop().time() - start_time

        # Define how long to collect data after setting torque (e.g., 30 seconds)
        collect_duration = 5
        end_time = asyncio.get_running_loop().time() + collect_duration

        while asyncio.get_running_loop().time() < end_time:
            # Measure and store data asynchronously
            data_dict = await asyncio.to_thread(odrive.get_all_data_rtr)  # If get_all_data_rtr is not async

            # Processing and database operations go here, potentially wrapped with asyncio.to_thread()

            await asyncio.sleep(0.01)  # Adjust the sleep duration as needed

    print("All torque values have been processed.")

if __name__ == "__main__":
    asyncio.run(main())
