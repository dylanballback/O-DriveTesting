import pyodrivecan
import asyncio
from datetime import datetime, timedelta
import aysnc_as5048b

import numpy as np
import math

#---------------------------------------- Quaternion START -------------------------------------------------


def angle_to_quaternion(angle_deg):
    """Convert an angle in degrees about the Z-axis to a quaternion."""
    angle_rad = np.radians(angle_deg)
    return np.array([math.cos(angle_rad / 2), 0, 0, math.sin(angle_rad / 2)])


def quaternion_conjugate(quat):
    """Calculate the conjugate of a quaternion."""
    w, x, y, z = quat
    return np.array([w, -x, -y, -z])


def quaternion_multiply(quat1, quat2):
    """Multiply two quaternions."""
    w1, x1, y1, z1 = quat1
    w2, x2, y2, z2 = quat2
    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 + y1*w2 + z1*x2 - x1*z2
    z = w1*z2 + z1*w2 + x1*y2 - y1*x2
    return np.array([w, x, y, z])


def quaternion_rotate(point, quat):
    """Rotate a 3D point by a quaternion."""
    quat = quat / np.linalg.norm(quat)
    w, x, y, z = quat
    qx, qy, qz = point
    
    rotated_x = qx * (1 - 2*y*y - 2*z*z) + qy * (2*x*y - 2*z*w) + qz * (2*x*z + 2*y*w)
    rotated_y = qx * (2*x*y + 2*z*w) + qy * (1 - 2*x*x - 2*z*z) + qz * (2*y*z - 2*x*w)
    rotated_z = qx * (2*x*z - 2*y*w) + qy * (2*y*z + 2*x*w) + qz * (1 - 2*x*x - 2*y*y)
    
    return np.array([rotated_x, rotated_y, rotated_z])


def quaternion_to_euler_z(q):
    """Convert a quaternion to an Euler angle about the Z-axis."""
    # For a single rotation about the Z-axis, the Euler angle is simply the argument of the quaternion
    return np.degrees(2 * np.arctan2(q[3], q[0]))


def calculate_w_desired(q_error, q_error_prev, dt, Kp, Kd):
    """
    Calculate the desired angular velocity based on quaternion error.

    :param q_error: Current quaternion error.
    :param q_error_prev: Previous quaternion error.
    :param dt: Time step between the current and previous error.
    :param Kp: Proportional gain.
    :param Kd: Derivative gain.
    :return: Desired angular velocity.
    """
    # Extract the vector part of the quaternion error
    e = q_error[1:]  # Assuming q_error = [q_w, q_x, q_y, q_z]
    
    # Calculate the derivative of the error
    e_prev = q_error_prev[1:]  # Extract vector part of previous quaternion error
    de_dt = (e - e_prev) / dt
    
    # Apply PD control law
    omega_desired = Kp * e + Kd * de_dt
    
    return omega_desired

#---------------------------------------- Quaternion END -------------------------------------------------



#------------------------ Controller Parameters from each Trial --------------------------------------------

#Function to setup Custom Controller parameters Table in the  Database
def controller_param_table_init(database,  controller_param_table_name):

    #Define the table column name and SQL data type
    table_columns_type = [
        ("J_zz", "REAL"),
        ("K", "REAL"),
        ("notes", "TEXT")
    ]

    #Create table
    database.create_user_defined_table(controller_param_table_name, table_columns_type)


def upload_controller_parameters(database, controller_param_table_name, controller_params_data):
     """
     This will be a function that will take the latest encoder value and upload it to the database.
     """
     #Define the columns of the PID Parameters table
     columns = ["trial_id", "J_zz", "K", "notes"]

     values = controller_params_data

     database.insert_into_user_defined_table(controller_param_table_name, columns, values)


#------------------------ Controller Data from each cycle --------------------------------------------

def controller_data_table_init(database, controller_data_table_name):
        
    table_columns_type = [
        ("current_time", "REAL"),
        ("omega_z", "REAL"),
        ("u_Z", "REAL")
    ]

    #Create table
    database.create_user_defined_table(controller_data_table_name, table_columns_type)


def upload_controller_data(database, controller_data_table_name, controller_data):
    """
    Asynchronously uploads the latest encoder value and related data to the database.

    Parameters:
    - database: The database object to perform operations on.
    - controller_data_table_name: The name of the table where data will be inserted.
    - controller_data: The data to upload to the database.
    """
    #Define the columns of the PID Parameters table
    columns = ["trial_id", "current_time", "omega_z", "u_Z"]

    values = controller_data

    database.insert_into_user_defined_table(controller_data_table_name, columns, values)
    





#Functions to clamp a variables upper and lower limit.        
def clamp(x, lower, upper):
    return lower if x < lower else upper if x > upper else x


def control_law_single_axis(J_zz, K, omega_z):
    """
    Calculate the control input (torque) for rotation about the z-axis.

    Parameters:
    - J_zz: Moment of inertia about the z-axis.
    - K: Control gain for the z-axis.
    - omega_z: Angular velocity about the z-axis.

    Returns:
    - u_z: Control input (torque) about the z-axis in Nm.
    """
    u_z = -J_zz * K * omega_z
    return u_z


#Example of how you can create a controller to get data from the O-Drives and then send motor comands based on that data.
async def controller(odrive1, encoder, database, controller_data_table_name, next_trial_id, J_zz, K, Kp, Kd, desired_attitude_deg):
        odrive1.clear_errors(identify=False)
        await asyncio.sleep(0.2)
        odrive1.setAxisState("closed_loop_control")
        await asyncio.sleep(0.2)
        odrive1.set_torque(0)


        q_desired = angle_to_quaternion(desired_attitude_deg)
        q_error_prev = np.array([1, 0, 0, 0])  # Assume starting with no error
        dt = 0.005  # Assuming loop runs every 5ms

        await asyncio.sleep(2)
        #Run for set time delay example runs for 15 seconds.
        stop_at = datetime.now() + timedelta(seconds=100000)
        while datetime.now() < stop_at:
            await asyncio.sleep(dt)  # Sleep for the duration of the time step

            #Get the current angle of the encoder
            current_angle = encoder.angle
            #print(f"Current Angle: {current_angle}")

            # Convert Current Angle from Encoder to quaternion
            q_current = angle_to_quaternion(current_angle)
            
            # Calculate quaternion error
            q_error = quaternion_multiply(quaternion_conjugate(q_desired), q_current)
            
            # Calculate desired angular velocity using the PD control law
            omega_desired = calculate_w_desired(q_error, q_error_prev, dt, Kp, Kd)
            #print(f"Current Angle: {current_angle} deg;   Desired Angular Velocity: {omega_desired} rad/s")

            # Update previous quaternion error
            q_error_prev = q_error
            
            # Convert omega_desired to a scalar value for single-axis control
            # This step would be different if controlling for multiple axes
            omega_desired_scalar = np.linalg.norm(omega_desired)  # Assuming single-axis, simplification
            
            # Use the desired angular velocity to compute the control torque
            # Assuming omega_z is the component of omega_desired along the z-axis
            controller_torque_output = control_law_single_axis(J_zz, K, omega_desired_scalar)
            
            
            # Get the current angluar velocity of the encoder
            current_angular_velocity = encoder.angular_velocity

            # Clamping the output torque to be withing the min and max of the O-Drive Controller
            controller_torque_output_clamped= clamp(controller_torque_output, -0.3, 0.3)
            #print(f"Controller Raw Output: {controller_torque_output}, Controller Clampped Output: {controller_torque_output_clamped}, Current Angular Velocity: {current_angular_velocity}")

            print(f"Current Angle: {current_angle} deg;  Desired Angular Velocity: {omega_desired_scalar} rad/s; Controller Clampped Output: {controller_torque_output_clamped:.10f} Nm; Current Angular Velocity: {current_angular_velocity:.10f} rad/s")

            #Send controller output torque to motor
            odrive1.set_torque(controller_torque_output_clamped)

            data = [next_trial_id, encoder.previous_time, current_angular_velocity, controller_torque_output]
            #Add to database
            upload_controller_data(database, controller_data_table_name, data)
          
   
        odrive1.running = False
        odrive1.estop()





# Run multiple busses.
async def main():
    #Set up Node_ID 0
    odrive1 = pyodrivecan.ODriveCAN(0)
    odrive1.initCanBus()
    
    #print(odrive1.database)
    #This sets up the database path the same as odrive1 object.
    database = pyodrivecan.OdriveDatabase('odrive_data.db')

    #This gets the next trial id from the database
    next_trial_id = database.get_next_trial_id()
    print(f"Using trial_id: {next_trial_id}")

    #Set up Encoder 
    encoder = aysnc_as5048b.Encoder_as5048b()
    #encoder.calibrate()
    encoder.encoder_table_init()

    #Controller Parameters Table Name
    controller_param_table_name = 'controllerParameters'

    #Create the PID Parameters Database Table with the Initalization Function
    controller_param_table_init(database, controller_param_table_name)

    #Controller Consts
    J_zz = 0.001666667
    K = 15
    controller_trial_notes = "Here we can take notes on our controller"

    #For Quaternion Control Desired Angular Velocity PD Controller
    Kp = 1
    Kd = 0.01
    desired_attitude_deg = 30 #Degrees

    controller_param_data = (next_trial_id, J_zz, K, "Some notes about the controller trial")
    #Upload PID parameters and notes to database
    upload_controller_parameters(database, controller_param_table_name, controller_param_data)

    controller_data_table_name = 'controllerData'

    #Set up Controller database table
    controller_data_table_init(database, controller_data_table_name)

    # odrive1, encoder, database, controller_data_table_name, next_trial_id, J_zz, K, Kp, Kd, desired_attitude_deg

    try:
        #add each odrive to the async loop so they will run.
        await asyncio.gather(
            odrive1.loop(),
            controller(odrive1, encoder, database, controller_data_table_name, next_trial_id, J_zz, K, Kp, Kd, desired_attitude_deg), 
            encoder.loop(), #This runs the external encoder code
        )
    except KeyboardInterrupt:
         odrive1.estop()




if __name__ == "__main__":
    asyncio.run(main())
