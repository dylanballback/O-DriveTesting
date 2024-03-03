import pyodrivecan
import asyncio
from datetime import datetime, timedelta
import aysnc_as5048b
import time

#------------------------ Controller Parameters from each Trial --------------------------------------------

#Function to setup Custom Controller parameters Table in the  Database
def controller_param_table_init(database,  controller_param_table_name):
    """
    Initializes a table in the database for storing custom controller parameters for each trial.

    Parameters:
    - database: The database instance where the table will be created.
    - controller_param_table_name: The name of the table to be created.
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
    Uploads the controller parameters data to the specified database table.

    Parameters:
    - database: The database instance to interact with.
    - controller_param_table_name: The name of the table where data will be inserted.
    - controller_params_data: The data (parameters) to be uploaded.
    """
     #Define the columns of the PID Parameters table
     columns = ["trial_id", "J_zz", "K", "notes"]

     values = controller_params_data

     database.insert_into_user_defined_table(controller_param_table_name, columns, values)


#------------------------ Controller Data from each cycle --------------------------------------------

def controller_data_table_init(database, controller_data_table_name):
    """
    Initializes a table in the database to store data from each controller cycle.

    Parameters:
    - database: The database instance where the table will be created.
    - controller_data_table_name: The name of the table to create.
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
    Uploads controller cycle data to the specified database table.

    Parameters:
    - database: The database instance to interact with.
    - controller_data_table_name: The name of the table where data will be inserted.
    - controller_data: The data to be uploaded.
    """
    #Define the columns of the PID Parameters table
    columns = ["trial_id", "current_time", "omega_z", "u_Z"]

    values = controller_data

    database.insert_into_user_defined_table(controller_data_table_name, columns, values)
    


#Functions to clamp a variables upper and lower limit.        
def clamp(x, lower, upper):
    """
    Clamps a value between a lower and upper bound.

    Parameters:
    - x: The value to clamp.
    - lower: The lower bound.
    - upper: The upper bound.

    Returns:
    - The clamped value.
    """
    return lower if x < lower else upper if x > upper else x


def control_law_single_axis(J_zz, K, omega_z):
    """
    Calculates the control input (torque) for rotation about the z-axis based on the current and desired angular velocity.

    Parameters:
    - J_zz: Moment of inertia about the z-axis.
    - K: Control gain for the z-axis.
    - omega_z: Current angular velocity about the z-axis.
    - calculated_omega_desired: Desired angular velocity about the z-axis.

    Returns:
    - u_z: Control input (torque) about the z-axis in Nm.
    """
    u_z = -J_zz * K * omega_z
    return u_z


def calculate_w_angle_desired(angle_error, angle_error_prev, dt, Kp, Kd, current_angular_velocity):
    """
    Calculates the desired angular velocity based on angle error using a PD control strategy.

    Parameters:
    - angle_error: Current angle error.
    - angle_error_prev: Previous angle error.
    - dt: Time step between the current and previous error.
    - Kp: Proportional gain.
    - Kd: Derivative gain on the current angular velocity.

    Returns:
    - omega_desired: Desired angular velocity.
    """
    # angle errror
    e = angle_error  
    
    # Calculate the derivative of the error
    e_prev = angle_error_prev  
    de_dt = (e - e_prev) / dt
    
    # Apply PD control law
    omega_desired = (Kp * e) + (Kd * de_dt)
  
    return omega_desired



#Example of how you can create a controller to get data from the O-Drives and then send motor comands based on that data.
async def controller(odrive1, encoder, database, controller_data_table_name, next_trial_id, J_zz, K, Kp, Kd, desired_attitude_deg):
    """
    Controls the motor based on encoder data, calculates control inputs, and sends commands to the motor.

    Parameters:
    - odrive1: The ODrive controller instance.
    - encoder: The encoder instance.
    - database: The database instance to log data.
    - controller_data_table_name: Name of the database table for controller data.
    - next_trial_id: Identifier for the next trial.
    - J_zz: Moment of inertia about the z-axis.
    - K: Control gain.
    - Kp: Proportional gain for PD control.
    - Kd: Derivative gain for PD control.
    - desired_attitude_deg: Desired attitude in degrees.
    - omega_desired: Desired angular velocity in radians per second.
    """
    odrive1.clear_errors(identify=False)
    await asyncio.sleep(0.2)
    odrive1.setAxisState("closed_loop_control")
    await asyncio.sleep(0.2)
    odrive1.set_torque(0)

    last_time = time.time()  # Capture the current time
    last_angle = 0 
    angle_error_prev = 0

    fixed_duration = 0.01 # Fixed sleep duration to control loop frequency
    
    #Run for set time delay example runs for 15 seconds.
    stop_at = datetime.now() + timedelta(seconds=100000)
    while datetime.now() < stop_at:
        # Sleep for a fixed duration to maintain loop frequency
        await asyncio.sleep(fixed_duration)


        current_time = time.time()  # Capture the current time
        #dt = current_time - last_time  # Calculate dt as the difference between current time and last time
        dt = fixed_duration

        #Get the current angle of the encoder
        current_angle = encoder.angle
        #print(f"Current Angle: {current_angle}")

        angle_error = current_angle - desired_attitude_deg 

        # Get the current angluar velocity of the encoder
        current_angular_velocity = encoder.angular_velocity

        omega_desired = calculate_w_angle_desired(angle_error, angle_error_prev, dt, Kp, Kd, current_angular_velocity)

        # Use the desired angular velocity to compute the control torque
        # Assuming omega_z is the component of omega_desired along the z-axis
        controller_torque_output = control_law_single_axis(J_zz, K, omega_desired)

        # Clamping the output torque to be withing the min and max of the O-Drive Controller
        controller_torque_output_clamped= clamp(controller_torque_output, -0.1, 0.1)
        
        print(f"Current: {current_angle}; Error: {angle_error};  Desired Angular Velocity: {omega_desired:.10f};  Current Angular Velocity: {current_angular_velocity:.10f};  Controller Clampped Output: {controller_torque_output_clamped:.10f}")

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
    K = 2

    #For Control Desired Angular Velocity PD Controller
    Kp = 0.12
    Kd = 0.000001
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
    finally:
        odrive1.estop()




if __name__ == "__main__":
    asyncio.run(main())