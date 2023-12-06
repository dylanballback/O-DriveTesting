from torqueReactionTestDatabase import TorqueReactionTestDatabase
import matplotlib.pyplot as plt
import numpy as np


def plot_torque_data(db, trial_id):
    trial_data = db.get_trial_data(trial_id, cleaned=True)  # Fetch cleaned data

    if trial_data:
        # Extracting each column
        times, torque_setpoints, torque_estimates, velocities = zip(*trial_data)

        # Plotting
        plt.figure(figsize=(10, 6))
        plt.plot(times, torque_setpoints, label='Torque Setpoint')
        plt.plot(times, torque_estimates, label='Torque Estimate')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Torque')
        plt.title(f'Torque Setpoint and Estimate for Trial ID {trial_id}')
        plt.legend()
        plt.show()
    else:
        print(f"No data available for Trial ID {trial_id}")



def plot_torque_and_velocity_data(db, trial_id):
    trial_data = db.get_trial_data(trial_id, cleaned=True)  # Fetch cleaned data

    if trial_data:
        # Extracting each column
        times, torque_setpoints, torque_estimates, velocities = zip(*trial_data)

        # Create the main figure and first y-axis
        fig, ax1 = plt.subplots(figsize=(10, 6))

        # Plot torque setpoint and estimate on the first y-axis
        color = 'tab:blue'
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel('Torque', color=color)
        ax1.plot(times, torque_setpoints, label='Torque Setpoint', color='yellow')
        ax1.plot(times, torque_estimates, label='Torque Estimate', color='blue')
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.legend(loc='upper left')

        # Create a second y-axis for velocity
        ax2 = ax1.twinx()  
        color = 'tab:red'
        ax2.set_ylabel('Velocity', color=color)
        ax2.plot(times, velocities, label='Velocity', color='red')
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.legend(loc='upper right')

        # Title and show plot
        plt.title(f'Torque Setpoint, Estimate, and Velocity for Trial ID {trial_id}')
        plt.show()
    else:
        print(f"No data available for Trial ID {trial_id}")


trial_id = int(input("Enter trial ID to plot:"))


db = TorqueReactionTestDatabase("torqueReactionTestDatabase.db")

#Remove outliers and create new clean data table.
#db.remove_outliers_and_create_clean_table(trial_id)


plot_torque_data(db, trial_id)  
plot_torque_and_velocity_data(db, trial_id)  


def plot_trial_data(db, trial_id, data_type):
    """
    Plots specified data type against time for a given trial ID.

    Parameters:
    db (TorqueReactionTestDatabase): Database object.
    trial_id (int): The ID of the trial to plot.
    data_type (str): The type of data to plot (e.g., 'pos', 'vel', etc.).
    """
    trial_data = db.get_data_for_plotting(trial_id, data_type, cleaned=True)  # Fetch cleaned data

    # Unpack the data
    times, values = zip(*trial_data)

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(times, values, label=f'{data_type.title()} over Time')
    plt.xlabel('Time (seconds)')
    plt.ylabel(f'{data_type.title()}')
    plt.title(f'{data_type.title()} over Time for Trial ID {trial_id}')
    plt.legend()
    plt.show()


plot_trial_data(db, trial_id, data_type='vel')

plot_trial_data(db, trial_id, data_type='torque_estimate')

plot_trial_data(db, trial_id, data_type='bus_current')