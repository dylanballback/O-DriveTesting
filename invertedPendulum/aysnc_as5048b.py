import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pyodrivecan
import time

from smbus import SMBus


@dataclass
class Encoder_as5048b:
    """
    A class to represent an AS5048B magnetic rotary encoder.

    Attributes:
    - bus (SMBus): The SMBus object for I2C communication.
    - address (int): The I2C address of the AS5048B encoder.
    - angle_reg (int): The register address to read the angle from.
    - angle (float): The latest read angle value after offset adjustment.
    - offset (float): The calibrated offset value for the angle.
    - running (bool): Flag to control the asynchronous angle reading loop.
    """
    bus: SMBus = field(default_factory=lambda: SMBus(1))
    address: int = 0x40    # AS5048B default address
    angle_reg: int = 0xFE  # AS5048B Register
    angle: float = 0.0     # Initialized angle
    offset: float = 0.0    # Initial offset
    running: bool = True   # Control flag for running the loop
    printing: bool = False    # Control flag for printing encoder angle
    database: database = pyodrivecan.OdriveDatabase('odrive_data.db')
    table_name: table_name = 'encoderData'
    start_time: start_time = time.time()  # Capture the start time when the object is initialized



    def read_angle(self):
        """Reads the current angle from the encoder.

        This method reads a 2-byte value from the encoder's angle register, 
        converts it to an angle, and adjusts it by the calibrated offset.

        Returns:
            float: The current angle in degrees.
        """
        data = self.bus.read_i2c_block_data(self.address, self.angle_reg, 2)
        angle = data[0] * 256 + data[1]
        angle *= 45 / 16383 # Convert raw data to angle in degrees with Inverted Pendulum Gear Ratio
        return angle - self.offset # Adjust by offset

    def calibrate(self):
        """Calibrates the encoder by setting the current angle as the zero offset."""
        self.offset = self.read_angle()
        time.sleep(5) #Wait 5 seconds after calibrate to move to top
        print("Calibration Complete")

    async def listen_to_angle(self):
        """An asynchronous loop that continuously reads the encoder's angle."""
        while self.running:
            await asyncio.sleep(0) # Non-blocking sleep to yield control
            self.angle = self.read_angle() # Update the current angle

    #Function to setup Custom Encoder Table in the Database 
    def encoder_table_init(self):

        #Define the table column name and SQL data type
        table_columns_type = [
            ("angle", "REAL"),
            ("time", "REAL")
        ]

        #Create encoderData table
        self.database.create_user_defined_table(self.table_name, table_columns_type)


    async def save_angle_loop(self): 
        """
        This will be an aysnc function that will take the latest encoder value and upload it to the database.
        """
        next_trial_id = self.database.get_next_trial_id()
        
        while self.running:
            await asyncio.sleep(0) # Non-blocking sleep to yield control
            #Define the columns of the encoderData table
            columns = ["trial_id", "angle", "time"]


            current_angle = self.angle
            #print(current_angle)
            
            # Calculate elapsed time since the start of the program
            current_time = time.time() - self.start_time

            values = [next_trial_id, current_angle, current_time]
            print(values)

            self.database.insert_into_user_defined_table(self.table_name, columns, values)

    async def loop(self, *others):
        """Runs the listen_to_angle method alongside other asynchronous tasks.

        Args:
            *others: Additional asyncio tasks to run concurrently.
        """
        await asyncio.gather(
            self.listen_to_angle(),
            self.save_angle_loop(),
            *others,
        )
        

    def run(self, *others):
        """A convenience method to start the asynchronous loop.

        Args:
            *others: Additional asyncio tasks to run concurrently.
        """
        asyncio.run(self.loop(*others))


    """A simple control loop that prints the encoder's angle for a set duration.

    Args:
        encoder (Encoder_as5048b): The encoder instance to monitor.
    """
    #Create the Encoder Database Table with the Initalization Function
    
    #stop_at = datetime.now() + timedelta(seconds=15)
    
    #while datetime.now() < stop_at:
    while True:
        await asyncio.sleep(0.001) # Reduce sleep to get angles faster
        print("Encoder angle:", encoder.angle)
    
    encoder.running = False # Stop the encoder's listening loop


"""
Example

if __name__ == "__main__":
    encoder = Encoder_as5048b()
    encoder.calibrate()
    encoder.run(controller(encoder))
"""
