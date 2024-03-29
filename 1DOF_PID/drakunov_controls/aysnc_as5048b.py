import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pyodrivecan
import time
import math

from smbus import SMBus
import socketio

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
    - printing (bool): Flag for controlling the printing of the encoder angle.
    - previous_angle (float): Stores the previous angle for velocity calculation.
    - previous_time (float): Stores the time when the previous angle was read.
    - angular_velocity (float): Angular velocity in radians/second.
    - database (pyodrivecan.OdriveDatabase): Database object for storing encoder data.
    - table_name (str): Name of the table for storing encoder data.
    - start_time (float): Captures the start time when the object is initialized.
    - total_rotations (int): Track total rotations of encoder.
    """
    bus: SMBus = field(default_factory=lambda: SMBus(1))
    address: int = 0x40  # AS5048B default address
    angle_reg: int = 0xFE  # AS5048B Register
    angle: float = 0.0  # Initialized angle
    offset: float = 0.0  # Initial offset
    running: bool = True  # Control flag for running the loop
    printing: bool = False  # Control flag for printing encoder angle
    previous_angle: float = 0.0  # To store the previous angle
    previous_time: float = time.time()  # To store the time when the previous angle was read
    angular_velocity: float = 0.0  # Angular velocity in radians/second
    database: pyodrivecan.OdriveDatabase = field(default_factory=lambda: pyodrivecan.OdriveDatabase('odrive_data.db'))
    table_name: str = 'encoderData'  # Name of the table for storing encoder data
    start_time: float = time.time()  # Capture the start time when the object is initialized
    total_rotations: int = 0  # Add this line to track total rotations
    total_accumulated_angle: float = 0.0  # Track the total accumulated angle in degrees
    ws_url: str = 'http://192.168.1.12:5000'  # Flask-SocketIO server URI
    previous_total_accumulated_angle: float = 0.0  # To store the previous total accumulated angle
    omega_dt: float = 0.0 #To store the dt used for angular velocity calulation

    sio = socketio.Client()  # Initialize the Socket.IO client

    
    def connect_to_server(self):
        """Connects to the WebSocket server."""
        self.sio.connect(self.ws_url)
        print("Connected to the server")
        

    def send_angle_via_socketio(self, angle):
        """Sends the encoder angle over Socket.IO."""
        self.sio.emit('encoder_data', {'angle': angle})



    def read_angle(self):
        """
        Reads the current angle from the AS5048B magnetic rotary encoder.

        This method communicates with the encoder via I2C to read the raw angle data from its designated register.
        The raw data is then converted to an angle in degrees, considering the specific gear ratio used in the application.
        Finally, the calibrated offset is subtracted to adjust the angle based on the initial calibration.

        Returns:
            float: The current angle in degrees, adjusted for the calibrated offset.
        """
        try:
            data = self.bus.read_i2c_block_data(self.address, self.angle_reg, 2)
            angle = data[0] * 256 + data[1]
            angle *= 90 / 16383  # Convert raw data to angle in degrees
            return angle - self.offset  # Adjust by offset
            
        except Exception as e:
            print(f"Error reading angle: {e}")
            # Handle the error appropriately, possibly by logging or retrying
            return self.angle  # Return the last known angle or a default value



    def calibrate(self):
        """
        Calibrates the encoder by setting the current angle as the zero offset.

        This method reads the current angle from the encoder and sets this value as the offset.
        It is assumed that the encoder is in the desired zero position at the time of calibration.
        A 5-second delay is provided after setting the offset to allow for manual adjustment of the encoder's position.
        """
        self.offset = self.read_angle()
        print("Calibration Complete move to top, you have 5 seconds.")
        time.sleep(5) #Wait 5 seconds after calibrate to move to top
        print("5 Seconds Over, Going to run controller.")



    def calculate_angular_velocity(self):
        """
        Asynchronously calculates and updates the angular velocity in radians per second.

        This method computes the angular velocity by calculating the difference between the current and previous angle readings,
        converting this difference from degrees to radians, and then dividing by the time difference between these readings.
        The calculated angular velocity is stored and updated at each call.

        Note: This method should be called repeatedly in a loop to continuously update the angular velocity.
        """
        current_angle = self.read_angle()  # Get the current angle from the encoder in degrees

        # Calculate the new total accumulated angle based on the current reading
        # This logic should be similar to what's in update_rotations_and_accumulated_angle
        # Assuming that method has already been called to update total_accumulated_angle accurately
        current_total_accumulated_angle = self.total_accumulated_angle

        current_time = time.time()  # Get the current time

        # Calculate the change in the total accumulated angle in radians
        angle_difference_radians = math.radians(current_total_accumulated_angle - self.previous_total_accumulated_angle)

        self.omega_dt = current_time - self.previous_time  # Calculate the time difference

        if self.omega_dt > 0:
            self.angular_velocity = angle_difference_radians / self.omega_dt
        else:
            self.angular_velocity = 0

        # Update the previous total accumulated angle and time for the next iteration
        self.previous_total_accumulated_angle = current_total_accumulated_angle
        self.previous_time = current_time



    def update_rotations_and_accumulated_angle(self, current_angle):
        """
        Updates the total accumulated angle based on the current angle reading, taking into account the full
        and partial rotations to accurately track the encoder's movement over time.
        
        Args:
            current_angle (float): The current angle reading from the encoder.
        """
        # Calculate the shortest path difference between angles
        angle_difference = (current_angle - self.previous_angle + 180) % 360 - 180

        # Update the total accumulated angle with the difference
        self.total_accumulated_angle += angle_difference

        # For visual tracking or other purposes, calculate total rotations from the total accumulated angle
        self.total_rotations = int(self.total_accumulated_angle / 360)

        # Update the previous angle for the next calculation
        self.previous_angle = current_angle


    async def listen_to_angle(self):
        """
        An asynchronous loop that continuously reads the encoder's angle and calculates the angular velocity.

        This loop runs indefinitely (until the `running` flag is set to False), reading the current angle from the encoder
        and calculating the angular velocity at each iteration. It uses a non-blocking sleep to yield control, allowing other
        tasks to run concurrently.
        """
        self.connect_to_server() #Connect to Websocket
        while self.running:
            await asyncio.sleep(0)  # Non-blocking sleep to yield control
            current_angle = self.read_angle()  # Read current angle
            # Update total rotations and accumulated angle based on the new reading
            self.update_rotations_and_accumulated_angle(current_angle)
            self.angle = current_angle  # Update the current angle
            self.calculate_angular_velocity()  # Calculate angular velocity
            self.send_angle_via_socketio(self.angular_velocity) #Send angle through websocket
            self.previous_angle = current_angle  # Update previous angle for next iteration



    #Function to setup Custom Encoder Table in the Database 
    def encoder_table_init(self):
        """
        Initializes a custom table in the database for storing encoder data.

        This method defines the structure of the table with columns for the angle and timestamp.
        It then creates this table in the database, ready for storing encoder readings.
        """
        #next_trial_id, current_time, current_angle, current_accumulated_angle, current_angular_velocity, omega_dt

        #Define the table column name and SQL data type
        table_columns_type = [
            ("time", "REAL"),
            ("angle", "REAL"),
            ("accumulated_angle", "REAL"),
            ("total_rotations", "REAL"),
            ("velocity", "REAL"),
            ("omega_dt", "REAL")
        ]

        #Create encoderData table
        self.database.create_user_defined_table(self.table_name, table_columns_type)


    async def save_angle_loop(self): 
        """
        An asynchronous loop that saves the latest encoder angle, angular velocity, and timestamp to the database.

        This loop runs indefinitely until the `running` flag is set to False. It captures the latest encoder angle and
        angular velocity, calculates the elapsed time since the start of the program, and inserts these values along
        with a trial ID into a predefined table in the database. The database table is structured to store the timestamp,
        angle in degrees, and angular velocity in radians per second for each recorded entry.

        This method allows for continuous logging of encoder data for analysis or real-time monitoring purposes, 
        providing valuable insights into the encoder's performance and the system's dynamics.

        Attributes captured and stored:
        - Trial ID: A unique identifier for the set of measurements, facilitating the grouping of data points.
        - Time: The elapsed time in seconds from the start of data collection.
        - Angle: The current angle of the encoder in degrees, adjusted for any offset.
        - Angular Velocity: The current angular velocity of the encoder in radians per second, calculated from successive angle measurements.
        """
        next_trial_id = self.database.get_next_trial_id()
        

        while self.running:
            await asyncio.sleep(0) # Non-blocking sleep to yield control
            #Define the columns of the encoderData table
            columns = ["trial_id", "time", "angle", "accumulated_angle", "total_rotations", "velocity", "omega_dt"]

            #Get latest angle to add to database
            current_angle = self.angle
            #print(current_angle)

            #Get latest angular velocity to add to database
            current_angular_velocity = self.angular_velocity
            #print(current_angular_velocity)

            #Get latest total accumulated angle
            current_accumulated_angle = self.total_accumulated_angle
            
            #Get latest total accumulated angle
            total_rotations = self.total_rotations

            #Get latest angular veloctity dt used for the calulcation
            omega_dt = self.omega_dt

            # Calculate elapsed time since the start of the program
            current_time = time.time() - self.start_time

            values = [next_trial_id, current_time, current_angle, current_accumulated_angle, total_rotations, current_angular_velocity, omega_dt]
            #print(values)

            #Enter latest data in values into the database encoder table.
            self.database.insert_into_user_defined_table(self.table_name, columns, values)



    async def loop(self, *others):
        """
        Runs the `listen_to_angle` method alongside other asynchronous tasks.

        This method uses `asyncio.gather` to concurrently execute the `listen_to_angle` method, the `save_angle_loop`,
        and any additional provided asynchronous tasks.

        Args:
            *others: Additional asyncio tasks to run concurrently with the angle listening and saving loops.
        """
        await asyncio.gather(
            self.listen_to_angle(),
            self.save_angle_loop(),
            *others,
        )
        


    def run(self, *others):
        """
        A convenience method to start the asynchronous loop, wrapping the `loop` method call with `asyncio.run`.

        This method is the entry point for running the encoder's asynchronous functionality, including continuous
        angle reading, angular velocity calculation, and data logging.

        Args:
            *others: Additional asyncio tasks to run concurrently with the main loop.
        """
        asyncio.run(self.loop(*others))


    
async def controller(encoder):
    """
    A simple control loop that prints the encoder's angle for a set duration or indefinitely.

    This function represents a basic example of a control task that utilizes the encoder's angle reading.
    It continually prints the encoder's current angle at a high frequency, demonstrating real-time monitoring.

    Args:
        encoder (Encoder_as5048b): An instance of the `Encoder_as5048b` class to monitor.
    """
    #Create the Encoder Database Table with the Initalization Function
    
    #stop_at = datetime.now() + timedelta(seconds=15)
    
    #while datetime.now() < stop_at:
    while True:
        await asyncio.sleep(0.001) # Reduce sleep to get angles faster
        print("Encoder angle: ", encoder.angle)
        print("Encoder angular velocity: ", encoder.angular_velocity)
        
    
    encoder.running = False # Stop the encoder's listening loop


"""
Example

if __name__ == "__main__":
    encoder = Encoder_as5048b()
    encoder.calibrate()
    encoder.run(controller(encoder))
"""
