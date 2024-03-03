import pyodrivecan
import asyncio
from datetime import datetime, timedelta
import aysnc_as5048b
import time




#------------------------ Controller Parameters from each Trial --------------------------------------------

#Function to setup Custom Controller parameters Table in the  Database
def controller_param_table_init(database,  controller_param_table_name):
    """
    Initializes a database table for storing custom controller parameters from each trial.

    Parameters:
    - database: The database instance.
    - controller_param_table_name: Name of the table to be created.
    """
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
    """
    Uploads controller parameters to the specified database table.

    Parameters:
    - database: The database instance.
    - controller_param_table_name: Name of the table for data insertion.
    - controller_params_data: Data to be uploaded, including trial_id, J_zz, K, and notes.
    """    
    table_columns_type = [
        ("current_time", "REAL"),
        ("omega_z", "REAL"),
        ("u_Z", "REAL")
    ]

    #Create table
    database.create_user_defined_table(controller_data_table_name, table_columns_type)


def upload_controller_data(database, controller_data_table_name, controller_data):
    """
    Initializes a database table for storing data from each controller cycle.

    Parameters:
    - database: The database instance.
    - controller_data_table_name: Name of the table to be created.
    """
    #Define the columns of the PID Parameters table
    columns = ["trial_id", "current_time", "omega_z", "u_Z"]

    values = controller_data

    database.insert_into_user_defined_table(controller_data_table_name, columns, values)
    


#Functions to clamp a variables upper and lower limit.        
def clamp(x, lower, upper):
    """
    Clamps a value to a specified range.

    Parameters:
    - x: The value to clamp.
    - lower: Lower bound of the range.
    - upper: Upper bound of the range.

    Returns:
    - The clamped value.
    """
    return lower if x < lower else upper if x > upper else x


def control_law_single_axis(J_zz, K, omega_z, calculated_omega_desired):
    """
    Calculates the control input (torque) based on the difference between current and desired angular velocity.

    Parameters:
    - J_zz: Moment of inertia about the z-axis.
    - K: Control gain for the z-axis.
    - omega_z: Current angular velocity about the z-axis.
    - calculated_omega_desired: Desired angular velocity about the z-axis.

    Returns:
    - u_z: Control input (torque) about the z-axis in Nm.
    """
    u_z = -J_zz * K * (omega_z - calculated_omega_desired)
    #print("   ")
    #print(f"Omega current = {omega_z}, Omega Desired = {calculated_omega_desired}")
    #print("   ")
    return u_z


def calculate_w_angle_desired(angle_error, angle_error_prev, dt, Kp, Kd, current_angular_velocity):
    """
    Calculates the desired angular velocity based on the proportional-derivative (PD) control of the angle error.

    Parameters:
    - angle_error: Current angle error.
    - angle_error_prev: Previous angle error.
    - dt: Time step between current and previous error measurements.
    - Kp: Proportional gain.
    - Kd: Derivative gain.
    - current_angular_velocity: Current angular velocity.

    Returns:
    - omega_desired: Desired angular velocity.
    """
    # angle errror
    e = angle_error  
    
    # Calculate the derivative of the error
    e_prev = angle_error_prev  
    de_dt = (e - e_prev) / dt
    

    # Apply PD control law
    omega_desired = Kp * e + Kd * current_angular_velocity
    
    return omega_desired



#Example of how you can create a controller to get data from the O-Drives and then send motor comands based on that data.
async def controller(odrive1, encoder, database, controller_data_table_name, next_trial_id, J_zz, K, Kp, Kd, desired_attitude_deg, omega_desired):
    """
    Main control loop that reads encoder data, calculates control inputs based on desired states, and sends commands to the motor.

    Parameters:
    - odrive1: The ODrive controller instance.
    - encoder: Encoder instance for reading angular position and velocity.
    - database: Database instance for logging control data.
    - controller_data_table_name: Name of the database table for logging control cycle data.
    - next_trial_id: Identifier for the current trial.
    - J_zz: Moment of inertia about the z-axis.
    - K: Control gain for the z-axis.
    - Kp: Proportional gain for PD control.
    - Kd: Derivative gain for PD control.
    - desired_attitude_deg: Desired angular position in degrees.
    - omega_desired: Desired angular velocity.
    """
    odrive1.clear_errors(identify=False)
    await asyncio.sleep(0.2)
    odrive1.setAxisState("closed_loop_control")
    await asyncio.sleep(0.2)
    odrive1.set_torque(0)

    last_time = time.time()  # Capture the current time
    last_angle = 0 
    angle_error_prev = 0
    fixed_duration = 0.005  # Fixed sleep duration to control loop frequency
    
    #Run for set time delay example runs for 15 seconds.
    stop_at = datetime.now() + timedelta(seconds=100000)
    while datetime.now() < stop_at:
        # Sleep for a fixed duration to maintain loop frequency
        await asyncio.sleep(fixed_duration)


        current_time = time.time()  # Capture the current time
        #dt = current_time - last_time  # Calculate dt as the difference between current time and last time
        dt = fixed_duration

        #Get the current angle of the encoder
        current_angle = encoder.total_accumulated_angle
        #print(f"Current Angle: {current_angle}")

        angle_error = current_angle - desired_attitude_deg
            
        # Get the current angluar velocity of the encoder
        current_angular_velocity = encoder.angular_velocity

        calculated_omega_desired = calculate_w_angle_desired(angle_error, angle_error_prev, dt, Kp, Kd, current_angular_velocity)
    
        # Use the desired angular velocity to compute the control torque
        # Assuming omega_z is the component of omega_desired along the z-axis
        controller_torque_output = control_law_single_axis(J_zz, K, current_angular_velocity, calculated_omega_desired)
        
        
        # Clamping the output torque to be withing the min and max of the O-Drive Controller
        controller_torque_output_clamped= clamp(controller_torque_output, -0.1, 0.1)
        #print(f"Controller Raw Output: {controller_torque_output}, Controller Clampped Output: {controller_torque_output_clamped}, Current Angular Velocity: {current_angular_velocity}")

        print(f"Current Angle: {current_angle} deg;    Desired Angular Velocity: {omega_desired} rad/s;   Controller Clampped Output: {controller_torque_output_clamped:.15f} Nm;   Current Angular Velocity: {current_angular_velocity:.15f} rad/s")

        #Send controller output torque to motor
        odrive1.set_torque(controller_torque_output_clamped)


        last_angle = current_angle
        angle_error_prev = angle_error
        last_time = current_time  # Update last_time for the next iteration

        # Example print to debug dt values
        #print(f"dt: {dt:.3f} seconds")


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
    J_zz = 0.0026433333333333335
    K = 20
    controller_trial_notes = "Here we can take notes on our controller"

    #For Quaternion Control Desired Angular Velocity PD Controller
    Kp = 0.02
    Kd = 15
    desired_attitude_deg = 30 #Degrees
    omega_desired = 1 #rad/s


    controller_param_data = (next_trial_id, J_zz, K, "Some notes about the controller trial")
    #Upload PID parameters and notes to database
    upload_controller_parameters(database, controller_param_table_name, controller_param_data)


    #Set up Controller database table name
    controller_data_table_name = 'controllerData'

    #Set up Controller database table
    controller_data_table_init(database, controller_data_table_name)

    try:
        #add each odrive to the async loop so they will run.
        await asyncio.gather(
            odrive1.loop(),
            controller(odrive1, encoder, database, controller_data_table_name, next_trial_id, J_zz, K, Kp, Kd, desired_attitude_deg, omega_desired), 
            encoder.loop(), #This runs the external encoder code
        )
    except KeyboardInterrupt:
         odrive1.estop()
    finally:
        odrive1.estop()




if __name__ == "__main__":
    asyncio.run(main())
