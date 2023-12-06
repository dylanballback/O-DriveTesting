import multiprocessing
import time
from ODriveCAN import ODriveCAN
from torqueReactionTestDatabase import TorqueReactionTestDatabase

#Create object of ODriveCAN class with node ID 0 
odrive = ODriveCAN(0)

#Initalize odrive 
odrive.initCanBus()


def set_torque_process(queue):
    odrive = ODriveCAN(0)
    odrive.initCanBus()

    while True:
        if not queue.empty():
            new_torque = queue.get()
            odrive.set_torque(new_torque)
            print(f"Torque set to {new_torque} Nm")
        time.sleep(5)  # Adjust the sleep duration as needed


def read_data_process(queue, db_name, trial_id):
    odrive = ODriveCAN(0)
    odrive.initCanBus()
    db = TorqueReactionTestDatabase(db_name)

    while True:
        current_time = time.time()  # Get the current time in seconds
        data = odrive.get_all_data_rtr()
        complete_data = (current_time,) + data  # Prepend the time to the data tuple
        db.add_data(trial_id, *complete_data)
        time.sleep(0.01)  # Adjust the sleep duration as needed


if __name__ == "__main__":
    db_name = "torqueReactionTestDatabase.db"
    torque_reaction_test_database = TorqueReactionTestDatabase(db_name)
    trial_id = torque_reaction_test_database.add_trial()
    print(f"Added Trial with ID: {trial_id}")

    torque_queue = multiprocessing.Queue()

    torque_process = multiprocessing.Process(target=set_torque_process, args=(torque_queue,))
    data_process = multiprocessing.Process(target=read_data_process, args=(torque_queue, db_name, trial_id))

    torque_process.start()
    data_process.start()

    try:
        torques = [0, 0.005, 0]  # Define your torque values here
        for torque in torques:
            torque_queue.put(torque)
            time.sleep(5)  # Wait some time before changing the torque
        print("All torque values have been processed.")
    except KeyboardInterrupt:
        print("Keyboard Interrupt received, stopping processes.")

    finally:
        torque_process.terminate()
        data_process.terminate()
        torque_process.join()
        data_process.join()
        print("Processes terminated. Exiting program.")