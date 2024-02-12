import pyodrivecan
import asyncio
from datetime import datetime, timedelta
import aysnc_as5048b
import pid

#Functions to clamp a variables upper and lower limit.        
def clamp(x, lower, upper):
    return lower if x < lower else upper if x > upper else x


#Example of how you can create a controller to get data from the O-Drives and then send motor comands based on that data.
async def controller(odrive1, encoder, pid):
        odrive1.set_torque(0)

        #Run for set time delay example runs for 15 seconds.
        stop_at = datetime.now() + timedelta(seconds=15)
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
    
    #Set up Encoder 
    encoder = aysnc_as5048b.Encoder_as5048b()
    encoder.calibrate()
    #encoder.run(controller(encoder))

    #Initalize PID Controller (Make setpoint between -4 and 4)
    pid = pid.PID(kp=1.0, ki=0.1, kd=0.01, setpoint=(-4, 4), lower_limit=-0.2, upper_limit=0.2)


    #add each odrive to the async loop so they will run.
    await asyncio.gather(
        odrive1.loop(),
        controller(odrive1), 
        encoder.run(controller(encoder)) #This runs the external encoder code
    )

if __name__ == "__main__":
    asyncio.run(main())

    