import pyodrivecan
import asyncio
from datetime import datetime, timedelta
import aysnc_as5048b
import pid



#Function to setup Custom PID parameters Table in the  Database
def pid_table_init(database,  pid_table_name):

    #Define the table column name and SQL data type
    table_columns_type = [
        ("kp", "REAL"),
        ("ki", "REAL"),
        ("kd", "REAL"),
        ("remarks", "TEXT")
    ]

    #Create encoderData table
    database.create_user_defined_table(pid_table_name, table_columns_type)



def upload_pid_parameters(database, pid_table_name, pid_data):
     """
     This will be a function that will take the latest encoder value and upload it to the database.
     """
     #Define the columns of the PID Parameters table
     columns = ["trial_id", "kp", "ki", "kd", "remarks"]

     values = pid_data

     database.insert_into_user_defined_table(pid_table_name, columns, values)



#Functions to clamp a variables upper and lower limit.        
def clamp(x, lower, upper):
    return lower if x < lower else upper if x > upper else x


#Example of how you can create a controller to get data from the O-Drives and then send motor comands based on that data.
async def controller(odrive1, encoder, pid):
        odrive1.set_torque(0)

        #Run for set time delay example runs for 15 seconds.
        stop_at = datetime.now() + timedelta(seconds=120)
        while datetime.now() < stop_at:
            await asyncio.sleep(0) #Need this for async to work.
            
            #Get the current angle of the encoder
            current_angle = encoder.angle

            #Input the current encoder angle into the PID Controller and get its pid_output
            pid_output = pid.update(current_value=current_angle)
            print(f"PID Output: {pid_output}, Current Angle: {current_angle}")

            #Send pid_output to control motor Torque
            odrive1.set_torque(pid_output)

            
        #await asyncio.sleep(15) #no longer need this the timedelta =15 runs the program for 15 seconds.
        odrive1.running = False





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

    #PID Parameters Table Name
    pid_table_name = 'pidParameters'

    #Create the PID Parameters Database Table with the Initalization Function
    pid_table_init(database, pid_table_name)

    #PID Const
    kp = 1.0
    ki = 0.1
    kd = 0.001
    pid_trial_notes = "Here we can take notes on our pid_values"

    #Initalize PID Controller (Make setpoint between -4 and 4)
    my_pid = pid.PID(kp, ki, kd, setpoint=(-4, 4), lower_limit=-0.2, upper_limit=0.2)

    pid_data = (next_trial_id, kp, ki, kd, pid_trial_notes)
    #Upload PID parameters and notes to database
    upload_pid_parameters(database, pid_table_name, pid_data)

    #add each odrive to the async loop so they will run.
    await asyncio.gather(
        odrive1.loop(),
        controller(odrive1, encoder, my_pid), 
        encoder.loop(), #This runs the external encoder code
    )


if __name__ == "__main__":
    asyncio.run(main())