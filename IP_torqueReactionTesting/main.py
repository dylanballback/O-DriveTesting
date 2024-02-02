import time
from ODriveCAN import ODriveCAN
from torqueReactionTestDatabase import TorqueReactionTestDatabase

def main():
    # Initialize ODriveCAN to node_id 0 
    odrive = ODriveCAN(0)
    odrive.initCanBus()

    db_name = "torqueReactionTestDatabase.db"
    torque_reaction_test_database = TorqueReactionTestDatabase(db_name)
    # When initializing the database for the first time
    #db.create_tables()
    trial_id = torque_reaction_test_database.add_trial()
    print(f"Added Trial with ID: {trial_id}")

    # Define your torque values here
    torques = [0, 0.1, 0]
    measurement_interval = 0.01  # Time between measurements
    torque_change_delay = 5  # Time to wait before changing torque

    # Capture the start time
    start_time = time.time()

    # Iterate through each torque setting
    for torque in torques:
        # Set torque
        odrive.set_torque(torque)
        print(f"Torque set to {torque} Nm")

        # Calculate elapsed time since start
        elapsed_time = time.time() - start_time

        # Define how long to collect data after setting torque (e.g., 30 seconds)
        collect_duration = 5
        end_time = time.time() + collect_duration

        while time.time() < end_time:
            # Calculate elapsed time since start
            elapsed_time = time.time() - start_time

            # Measure and store data
            data_dict = odrive.get_all_data_rtr()

            # Function to safely extract tuple elements
            def safe_extract(data, index, default=0):
                if data is not None and len(data) > index:
                    return data[index]
                return default

            # Safely access tuple elements
            pos = safe_extract(data_dict.get('encoder_data'), 0)
            vel = safe_extract(data_dict.get('encoder_data'), 1)
            torque_setpoint = safe_extract(data_dict.get('torque_data'), 0)
            torque_estimate = safe_extract(data_dict.get('torque_data'), 1)
            bus_voltage = safe_extract(data_dict.get('voltage_current_data'), 0)
            bus_current = safe_extract(data_dict.get('voltage_current_data'), 1)
            iq_setpoint = safe_extract(data_dict.get('iq_setpoint_measured_data'), 0)
            iq_measured = safe_extract(data_dict.get('iq_setpoint_measured_data'), 1)

            data_tuple = (
                elapsed_time,
                pos,
                vel,
                torque_setpoint,
                torque_estimate,
                bus_voltage,
                bus_current,
                iq_setpoint,
                iq_measured
            )

            torque_reaction_test_database.add_data(trial_id, *data_tuple)
            time.sleep(0.01)  # Adjust the sleep duration as needed

    print("All torque values have been processed.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program interrupted by user. Exiting.")