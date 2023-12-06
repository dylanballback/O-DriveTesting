import time
import threading
from ODriveCAN import ODriveCAN
from torqueReactionTestDatabase import TorqueReactionTestDatabase

def set_torques(odrive, torques, torque_change_delay):
    for torque in torques:
        odrive.set_torque(torque)
        print(f"Torque set to {torque} Nm")
        time.sleep(torque_change_delay)

def collect_data(odrive, db, trial_id, start_time):
    while True:
        elapsed_time = time.time() - start_time
        
        #Get all data from ODrive
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

        #Add time and all other data from above
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

        #add the data to the database
        db.add_data(trial_id, *data_tuple)
        time.sleep(0.01)  # Adjust the sleep duration as needed


def main():
    odrive = ODriveCAN(0)
    odrive.initCanBus()

    db_name = "torqueReactionTestDatabase.db"
    db = TorqueReactionTestDatabase(db_name)
    trial_id = db.add_trial()
    print(f"Added Trial with ID: {trial_id}")

    torques = [0, 0.1, 0]
    torque_change_delay = 5
    start_time = time.time()

    # Start the data collection thread
    data_thread = threading.Thread(target=collect_data, args=(odrive, db, trial_id, start_time))
    data_thread.daemon = True  # Mark as a daemon thread
    data_thread.start()

    # Set torques in a separate thread
    torque_thread = threading.Thread(target=set_torques, args=(odrive, torques, torque_change_delay))
    torque_thread.start()

    # Wait for the torque_thread to complete
    torque_thread.join()
    print("All torque values have been processed.")

    # Optionally wait a bit before ending the program to ensure last data points are captured
    time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program interrupted by user. Exiting.")
