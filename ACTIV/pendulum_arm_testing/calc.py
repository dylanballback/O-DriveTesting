import matplotlib.pyplot as plt
import numpy as np

def calculate_force(mass, g, angle_radians):
    """
    Calculates the centripetal force on a mass at a given angle due to gravity.
    
    Parameters:
    - mass: Mass at the end of the arm (in kilograms)
    - g: Acceleration due to gravity (in m/s^2)
    - angle_radians: Angle of the arm with respect to the vertical (in radians)
    
    Returns:
    - The component of gravitational force acting as centripetal force (in Newtons)
    """
    # Calculate gravitational force
    Fg = mass * g
    
    # Calculate component of the gravitational force acting as centripetal force
    F = Fg * np.sin(angle_radians)
    
    return F




# Constants
mass = 0.085  # 85g converted to kg
g = 9.81  # Acceleration due to gravity in m/s^2

# Generating angle range from 0 to 360 degrees
angles_degrees = np.linspace(0, 360, 360)
angles_radians = np.radians(angles_degrees)

# Calculating force for each angle
forces = [calculate_force(mass, g, angle) for angle in angles_radians]


"""
# Plotting
plt.figure(figsize=(10, 6))
plt.plot(angles_degrees, forces, label='Force')
plt.xlabel('Angle (θ) in Degrees')
plt.ylabel('Force (N)')
plt.title('Force vs. Angle')
plt.legend()
plt.grid(True)
plt.show()
"""


def calculate_torque(mass, g, arm_length, angle_radians):
    """
    Calculates the torque required to counteract the force due to gravity
    on a mass at the end of an arm at a given angle.
    
    Parameters:
    - mass: Mass at the end of the arm (in kilograms)
    - g: Acceleration due to gravity (in m/s^2)
    - arm_length: Length of the arm (in meters)
    - angle_radians: Angle of the arm with respect to the vertical (in radians)
    
    Returns:
    - The torque required to counteract the gravitational force (in Newton-meters)
    """
    # Calculate the force
    F = calculate_force(mass, g, angle_radians)
    
    # Calculate the torque
    torque = F * arm_length
    
    return torque

# Constants
arm_length = 0.1  # 100mm converted to meters

# Calculating torque for each angle
torques = [calculate_torque(mass, g, arm_length, angle) for angle in angles_radians]

# Plotting force and torque on the same graph for comparison
fig, ax1 = plt.subplots(figsize=(10, 6))

color = 'tab:red'
ax1.set_xlabel('Angle (θ) in Degrees')
ax1.set_ylabel('Force (N)', color=color)
ax1.plot(angles_degrees, forces, color=color, label='Centripetal Force')
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
color = 'tab:blue'
ax2.set_ylabel('Torque (Nm)', color=color)  # we already handled the x-label with ax1
ax2.plot(angles_degrees, torques, color=color, label='Torque')
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  # otherwise the right y-label is slightly clipped
plt.title('Centripetal Force and Required Torque vs. Angle')
fig.legend(loc="upper right", bbox_to_anchor=(1,1), bbox_transform=ax1.transAxes)
plt.show()
