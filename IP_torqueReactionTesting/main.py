import time
from ODriveCAN import ODriveCAN
from torqueReactionTestDatabase import TorqueReactionTestDatabase

def main():
    # Initialize ODriveCAN and database
    odrive = ODriveCAN(0)
    odrive.initCanBus()

    db_name = "torqueReactionTestDatabase.db"
    torque_reaction_test_database = TorqueReactionTestDatabase(db_name)
    trial_id = torque_reaction_test_database.add_trial()
    print(f"Added Trial with ID: {trial_id}")

    # Define your torque values here
    torques = [0, 0.05, 0]
    measurement_interval = 0.01  # Time between measurements
    torque_change_delay = 5  # Time to wait before changing torque

    # Capture the start time
    start_time = time.time()

    # Iterate through each torque setting
    for torque in torques:
        # Set torque
        odrive.set_torque(torque)
        print(f"Torque set to {torque} Nm")

        # Wait some time for the system to stabilize
        time.sleep(5)

        # Calculate elapsed time since start
        elapsed_time = time.time() - start_time

        # Measure and store data
        data_dict = odrive.get_all_data_rtr()

        data_tuple = (
            elapsed_time,
            data_dict.get('pos', 0),
            data_dict.get('vel', 0),
            data_dict.get('torque_setpoint', 0),
            data_dict.get('torque_estimate', 0),
            data_dict.get('bus_voltage', 0),
            data_dict.get('bus_current', 0),
            data_dict.get('iq_setpoint', 0),
            data_dict.get('iq_measured', 0)
        )

        torque_reaction_test_database.add_data(trial_id, *data_tuple)

    print("All torque values have been processed.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program interrupted by user. Exiting.")