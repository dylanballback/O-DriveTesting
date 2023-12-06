from torqueReactionTestDatabase import TorqueReactionTestDatabase
import matplotlib.pyplot as plt
import numpy as np

def remove_outliers(data):
    data = np.array(data)
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    cleaned_data = data[(data >= lower_bound) & (data <= upper_bound)]
    return cleaned_data.tolist()


def plot_torque_data(db, trial_id):
    trial_data = db.get_trial_data(trial_id)

    if trial_data:
        # Extracting each column
        times, torque_setpoints, torque_estimates, velocities = zip(*trial_data)

        # Cleaning the data
        cleaned_torque_setpoints = remove_outliers(torque_setpoints)
        cleaned_torque_estimates = remove_outliers(torque_estimates)

        # Plotting
        plt.figure(figsize=(10, 6))
        plt.plot(times[:len(cleaned_torque_setpoints)], cleaned_torque_setpoints, label='Torque Setpoint')
        plt.plot(times[:len(cleaned_torque_estimates)], cleaned_torque_estimates, label='Torque Estimate')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Torque')
        plt.title(f'Torque Setpoint and Estimate for Trial ID {trial_id}')
        plt.legend()
        plt.show()
    else:
        print(f"No data available for Trial ID {trial_id}")



def plot_torque_and_velocity_data(db, trial_id):
    trial_data = db.get_trial_data(trial_id)

    if trial_data:
        # Extracting each column
        times, torque_setpoints, torque_estimates, velocities = zip(*trial_data)

        # Cleaning the data
        cleaned_torque_setpoints = remove_outliers(torque_setpoints)
        cleaned_torque_estimates = remove_outliers(torque_estimates)
        cleaned_velocities = remove_outliers(velocities)

        # Ensure all cleaned data lists are of the same length
        min_length = min(len(cleaned_torque_setpoints), len(cleaned_torque_estimates), len(cleaned_velocities))
        times = times[:min_length]

        # Create the main figure and first y-axis
        fig, ax1 = plt.subplots(figsize=(10, 6))

        # Plot torque setpoint and estimate on the first y-axis
        color = 'tab:blue'
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel('Torque', color=color)
        ax1.plot(times, cleaned_torque_setpoints[:min_length], label='Torque Setpoint', color='yellow')
        ax1.plot(times, cleaned_torque_estimates[:min_length], label='Torque Estimate', color='blue')
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.legend(loc='upper left')

        # Create a second y-axis for velocity
        ax2 = ax1.twinx()  
        color = 'tab:red'
        ax2.set_ylabel('Velocity', color=color)
        ax2.plot(times, cleaned_velocities[:min_length], label='Velocity', color='red')
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.legend(loc='upper right')

        # Title and show plot
        plt.title(f'Torque Setpoint, Estimate, and Velocity for Trial ID {trial_id}')
        plt.show()
    else:
        print(f"No data available for Trial ID {trial_id}")




db = TorqueReactionTestDatabase("torqueReactionTestDatabase.db")

#trial_id = int(input("Enter trial ID to plot:"))

plot_torque_data(db, 16)  
plot_torque_and_velocity_data(db, 16)  
