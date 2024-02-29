import pyodrivecan
import asyncio
from datetime import datetime, timedelta
import aysnc_as5048b


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
        ("u_Z", "REAL"),
    ]

    #Create table
    database.create_user_defined_table(controller_data_table_name, table_columns_type)


async def upload_controller_data(database, controller_data_table_name, controller_data):
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

    #database.insert_into_user_defined_table(controller_data_table_name, columns, values)
    # Use run_in_executor to run the synchronous database insert operation in a background thread
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, database.insert_into_user_defined_table, controller_data_table_name, columns, values)





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
async def controller(odrive1, encoder, database, controller_data_table_name, next_trial_id, J_zz, K):
        odrive1.clear_errors(identify=False)
        await asyncio.sleep(0.2)
        odrive1.setAxisState("closed_loop_control")
        await asyncio.sleep(0.2)
        odrive1.set_torque(0)


        await asyncio.sleep(2)
        #Run for set time delay example runs for 15 seconds.
        stop_at = datetime.now() + timedelta(seconds=100000)
        while datetime.now() < stop_at:
            await asyncio.sleep(0) #Need this for async to work.
            
            #Get the current angle of the encoder
            #current_angle = encoder.angle

            # Get the current angluar velocity of the encoder
            current_angular_velocity = encoder.angular_velocity


            # Check if the pendulum has fallen by comparing the current angle with the thresholds
            #if current_angle < angle_threshold_min or current_angle > angle_threshold_max:
                #print("Pendulum has fallen. Initiating emergency stop.")
                #odrive1.estop()
                #break  # Exit the loop to stop further execution

            #Input the current encoder angular velocity into the Controller and get its torque output
            controller_torque_output = control_law_single_axis(J_zz, K, current_angular_velocity)
            controller_torque_output_clamped= clamp(controller_torque_output, -0.1, 0.1)
            print(f"Controller Raw Output: {controller_torque_output}, Controller Clampped Output: {controller_torque_output_clamped}, Current Angular Velocity: {current_angular_velocity}")

            #Send pid_output to control motor Torque
            odrive1.set_torque(controller_torque_output_clamped)

            data = [next_trial_id, encoder.previous_time, current_angular_velocity, controller_torque_output]
            #Add to database
            upload_controller_data( database, controller_data_table_name, data)
          

            
        #await asyncio.sleep(15) #no longer need this the timedelta =15 runs the program for 15 seconds.
        odrive1.running = False
        odrive1.estop()





# Run multiple busses.
async def main():
    #Set up Node_ID 0
    odrive1 = pyodrivecan.ODriveCAN(0)
    odrive1.initCanBus()
    
    print(odrive1.database)
    #This sets up the database path the same as odrive1 object.
    database = pyodrivecan.OdriveDatabase('odrive_data.db')

    #This gets the next trial id from the database
    next_trial_id = database.get_next_trial_id()
    print(f"Using trial_id: {next_trial_id}")

    #Set up Encoder 
    encoder = aysnc_as5048b.Encoder_as5048b()
    encoder.calibrate()
    encoder.encoder_table_init()

    #Controller Parameters Table Name
    controller_param_table_name = 'controllerParameters'

    #Create the PID Parameters Database Table with the Initalization Function
    upload_controller_parameters(database, controller_param_table_name)

    #Controller Consts
    J_zz = 0.001666667
    K = 1
    controller_trial_notes = "Here we can take notes on our controller"

    controller_param_data = (next_trial_id, J_zz, K, controller_trial_notes)
    #Upload PID parameters and notes to database
    upload_controller_parameters(database, controller_param_table_name, controller_param_data)

    controller_data_table_name = 'controllerData'

    #Set up Controller database table
    controller_data_table_init(database, controller_data_table_name)


    try:
        #add each odrive to the async loop so they will run.
        await asyncio.gather(
            odrive1.loop(),
            controller(odrive1, encoder, database, controller_data_table_name, next_trial_id, J_zz, K), 
            encoder.loop(), #This runs the external encoder code
        )
    except KeyboardInterrupt:
         odrive1.estop()




if __name__ == "__main__":
    asyncio.run(main())
