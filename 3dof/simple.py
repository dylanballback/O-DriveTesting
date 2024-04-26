import pyodrivecan
import asyncio
from datetime import datetime, timedelta
import time



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




#Example of how you can create a controller to get data from the O-Drives and then send motor comands based on that data.
async def controller(odrive0, odrive1, odrive2):
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
    odrive0.clear_errors(identify=False)
    odrive1.clear_errors(identify=False)
    odrive2.clear_errors(identify=False)
    #await asyncio.sleep(0.2)
    #odrive1.setAxisState("closed_loop_control")
    await asyncio.sleep(0.2)
    odrive0.set_torque(0)
    odrive1.set_torque(0)
    odrive2.set_torque(0)

    last_time = time.time()  # Capture the current time
    last_angle = 0 
    angle_error_prev = 0

    fixed_duration = 0.01 # Fixed sleep duration to control loop frequency
    
    #Run for set time delay example runs for 15 seconds.
    stop_at = datetime.now() + timedelta(seconds=100000)
    while datetime.now() < stop_at:
        # Sleep for a fixed duration to maintain loop frequency
        #await asyncio.sleep(fixed_duration)


        current_time = time.time()  # Capture the current time
        dt = current_time - last_time  # Calculate dt as the difference between current time and last time
        #print(f"dt: {dt}")
        #dt = fixed_duration

        # Clamping the output torque to be withing the min and max of the O-Drive Controller (Max Torque limit of motor for 1DOF is 0.6 NM)
        #controller_torque_output_clamped= clamp(controller_torque_output, -0.1, 0.1)
        

        #Send controller output torque to motor
        odrive0.set_torque(0.1)
        odrive1.set_torque(0)
        odrive2.set_torque(0)

        last_time = current_time  # Update last_time for the next iteration

        """
        #Prepare data for websocket
        websocket_data = {
            "angle_setpoint" : desired_attitude_deg,
            "current_angle" : current_angle,
            "angle_error" : angle_error,
            "current_angular_velocity" : current_angular_velocity,
            "omega_desired" : omega_desired,
            "controller_torque_output" : controller_torque_output,
            "controller_torque_output_clamped" : controller_torque_output_clamped,
        }

        #Send data through websocket
        send_websocket_data(data)
        """
        

    odrive1.running = False
    




# Run multiple busses.
async def main():
    #Set up Node_ID 0
    odrive0 = pyodrivecan.ODriveCAN(0)
    odrive0.initCanBus()
    
    #Set up Node_ID 1
    odrive1 = pyodrivecan.ODriveCAN(1)
    odrive1.initCanBus()

    #Set up Node_ID 2
    odrive2 = pyodrivecan.ODriveCAN(2)
    odrive2.initCanBus()
    
    #print(odrive1.database)
    #This sets up the database path the same as odrive1 object.
    database = pyodrivecan.OdriveDatabase('odrive_data.db')

    #This gets the next trial id from the database
    next_trial_id = database.get_next_trial_id()
    print(f"Using trial_id: {next_trial_id}")


    try:
        #add each odrive to the async loop so they will run.
        await asyncio.gather(
            odrive0.loop(),
            odrive1.loop(),
            odrive2.loop(),
            controller(odrive0, odrive1, odrive2), 
        )
    except KeyboardInterrupt:
        odrive0.estop()
        odrive1.estop()
        odrive2.estop()
    finally:
        odrive0.running = False
        odrive1.running = False
        odrive2.running = False




if __name__ == "__main__":
    asyncio.run(main())