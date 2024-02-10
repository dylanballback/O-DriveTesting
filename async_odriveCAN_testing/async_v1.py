import asyncio
import can
import struct
import time
from datetime import datetime
from odrivedatabase import OdriveDatabase

class ODriveCAN:
    def __init__(self, nodeID, canBusID="can0", canBusType="socketcan"):
        """
        Initializes the ODriveCAN object for interacting with an ODrive controller via CAN.

        Para:
            nodeID (int): The node ID of the ODrive controller.
            canBusID (str): Identifier for the CAN bus, default is 'can0'.
            canBusType (str): Type of the CAN bus, default is 'socketcan'.
        
        Example:
            >>> odrive_can = ODriveCAN(nodeID=1)
        """
        self.canBusID = canBusID
        self.canBusType = canBusType
        self.nodeID = nodeID
        self.canBus = can.interface.Bus(canBusID, bustype=canBusType)
        self.database = OdriveDatabase('odrive_data.db')
        self.collected_data = []  # Initialize an empty list to store data
        self.start_time = time.time()  # Capture the start time when the object is initialized



    async def async_recv(self, timeout=1):
        """
        Asynchronously receives a CAN message with a specified timeout.

        Para:
            timeout (float): The maximum time to wait for a message, in seconds.

        Returns:
            The received CAN message, or None if no message is received within the timeout.

        Example:
            >>> msg = await odrive_can.async_recv(timeout=1.0)
            >>> print(msg)
        """
        return self.canBus.recv(timeout)


#-------------------------------------- O-Drive CAN SETUP START-------------------------------------------------
   
    def initCanBus(self):
        """
        Initalize connection to CAN Bus

        canBusID (String): Default "can0" this is the name of the can interface
        canBus (String): Default "socketcan" this is the python can libary CAN type
        """
         # Create and assign the CAN bus interface object to self.canBus
        self.canBus = can.interface.Bus(self.canBusID, bustype=self.canBusType)

        # Flush the CAN Bus of any previous messages
        self.flush_can_buffer()

        # Set the Odrive to closed axis state control
        self.closed_loop_control()



    def flush_can_buffer(self):
        """
        Flushes the CAN receive buffer to clear any pending messages.

        Example:
            >>> odrive_can.flush_can_buffer()
        """
        #Flush CAN RX buffer to ensure no old pending messages.
        while not (self.canBus.recv(timeout=0) is None): pass
        print("I have cleared all CAN Messages on the BUS!")


    
    # Put axis into closed loop control state
    def closed_loop_control(self):
        """
        Sets the ODrive controller to closed-loop control mode.

        Example:
            >>> odrive_can.closed_loop_control()
        """
        self.flush_can_buffer()
        print(f"Attempting to set control state to ODrive {self.nodeID}...")
        try:
            self.canBus.send(can.Message(
                arbitration_id=(self.nodeID << 5 | 0x07), # 0x07: Set_Axis_State
                data=struct.pack('<I', 8), # 8: AxisState.CLOSED_LOOP_CONTROL
                is_extended_id=False
            ))
            
            print(f"Checking Hearbeat for ODrive {self.nodeID}")
            # Wait for axis to enter closed loop control by scanning heartbeat messages
            for msg in self.canBus:
                if msg.arbitration_id == (self.nodeID << 5 | 0x01): # 0x01: Heartbeat
                    error, state, result, traj_done = struct.unpack('<IBBB', bytes(msg.data[:7]))
                    if state == 8: # 8: AxisState.CLOSED_LOOP_CONTROL
                        break
            print(f"Successfully set control state to ODrive {self.nodeID}")

        except Exception as e:
            print(f"Error connecting to ODrive {self.nodeID}: {str(e)}")



    #Shutdown can bus at the end of a program. 
    def bus_shutdown(self):
        """
        Run this method at the end of your program to shundown the can bus to prevent can errors.

        Example:
        >>> import pyodrivecan
        >>> odrivecan.bus_shutdown()
        ...
        ... Can bus successfully shut down.
        """
        self.canBus.shutdown

        print("Can bus successfully shut down.")
    
#-------------------------------------- O-Drive CAN SETUP END-------------------------------------------------


#-------------------------------------- Motor Controls START------------------------------------------------
  
    # Function to set position for a specific O-Drive
    def set_position(self, position, velocity_feedforward=0, torque_feedforward=0):
        """
        Sets the position of the ODrive motor.

        Para:
            position (float): Target position for the motor.
            velocity_feedforward (float): Feedforward velocity, default is 0.
            torque_feedforward (float): Feedforward torque, default is 0.

        Example:
            >>> odrive_can.set_position(1000.0)
        """
        self.canBus.send(can.Message(
            arbitration_id=(self.nodeID << 5 | 0x0C),
            data=struct.pack('<fhh', float(position), velocity_feedforward, torque_feedforward),
            is_extended_id=False
        ))
        print(f"Successfully moved ODrive {self.nodeID} to {position}")
        


    # Function to set velocity for a specific O-Drive
    def set_velocity(self, velocity, torque_feedforward=0.0):
        """
        Sets the velocity of the ODrive motor.

        Para:
            velocity (float): Target velocity for the motor.
            torque_feedforward (float): Feedforward torque, default is 0.

        Example:
            >>> odrive_can.set_velocity(500.0)
        """
        self.canBus.send(can.Message(
            arbitration_id=(self.nodeID << 5 | 0x0d),  # 0x0d: Set_Input_Vel
            data=struct.pack('<ff', velocity, torque_feedforward),
            is_extended_id=False
        ))



    # Function to set torque for a specific O-Drive
    def set_torque(self, torque):
        """
        Sets the torque of the ODrive motor.

        Para:
            torque (float): Target torque for the motor.

        Example:
            >>> odrive_can.set_torque(10.0)
        """
        self.canBus.send(can.Message(
            arbitration_id=(self.nodeID << 5 | 0x0E),  # 0x0E: Set_Input_Torque
            data=struct.pack('<f', torque),
            is_extended_id=False
        ))
        print(f"Successfully set ODrive {self.nodeID} to {torque} [Nm]")

#-------------------------------------- Motor Controls END-------------------------------------------------
        

    

#-------------------------------------- Motor Feedback ----------------------------------------------------
# In order for these functions to work you need to have the O-Drive set with the Cyclic messages 
# The cyclic messgaes for CAN will make the O-Drive automatically send the data you want to collect at the set rate.

    

    async def get_one_encoder_estimate(self, timeout=1.0):
        """
        Asynchronously gets one encoder estimate from the ODrive.

        Para:
            timeout (float): Timeout for receiving the encoder estimate, in seconds.

        Returns:
            A tuple of (position, velocity) if successful, None otherwise.

        Example:
            >>> pos, vel = await odrive_can.get_one_encoder_estimate(timeout=1.0)
            >>> print(pos, vel)
        """
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            msg = await self.async_recv(timeout=timeout - (time.time() - start_time))
            if msg and msg.arbitration_id == (self.nodeID << 5 | 0x09):  # Encoder estimate
                pos, vel = struct.unpack('<ff', bytes(msg.data))
                print(f"O-Drive {self.nodeID} - pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")
                return pos, vel
        return None, None



    async def get_one_torque(self, timeout=1.0):
        """
        Asynchronously retrieves a single torque measurement from the ODrive controller.

        Para:
            timeout (float): The timeout for the operation in seconds.

        Returns:
            A tuple containing the torque target and torque estimate (torque_target, torque_estimate),
            or (None, None) if no data is received within the timeout period.

        Example:
            >>> torque_target, torque_estimate = await odrive_can.get_one_torque(timeout=1.0)
            >>> print(f"Torque Target: {torque_target}, Torque Estimate: {torque_estimate}")
        """
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            msg = await self.async_recv(timeout=timeout - (time.time() - start_time))
            if msg and msg.arbitration_id == (self.nodeID << 5 | 0x1C):  # 0x1C: Get_Torques
                torque_target, torque_estimate = struct.unpack('<ff', bytes(msg.data))
                print(f"O-Drive {self.nodeID} - Torque Target: {torque_target:.3f} [Nm], Torque Estimate: {torque_estimate:.3f} [Nm]")
                return torque_target, torque_estimate
        return None, None


    
    async def get_one_bus_voltage_current(self, timeout=1.0):
        """
        Asynchronously retrieves a single bus voltage and current measurement from the ODrive controller.

        Para:
            timeout (float): The timeout for the operation in seconds.

        Returns:
            A tuple containing the bus voltage and current (bus_voltage, bus_current),
            or (None, None) if no data is received within the timeout period.

        Example:
            >>> bus_voltage, bus_current = await odrive_can.get_one_bus_voltage_current(timeout=1.0)
            >>> print(f"Bus Voltage: {bus_voltage}, Bus Current: {bus_current}")
        """
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            msg = await self.async_recv(timeout=timeout - (time.time() - start_time))
            if msg and msg.arbitration_id == (self.nodeID << 5 | 0x17):  # Bus voltage and current
                bus_voltage, bus_current = struct.unpack('<ff', bytes(msg.data))
                print(f"O-Drive {self.nodeID} - Bus Voltage: {bus_voltage:.3f} [V], Bus Current: {bus_current:.3f} [A]")
                return bus_voltage, bus_current
        return None, None



    async def get_one_iq_setpoint_measured(self, timeout=1.0):
        """
        Asynchronously retrieves a single IQ setpoint and measured current from the ODrive controller.

        Para:
            timeout (float): The timeout for the operation in seconds.

        Returns:
            A tuple containing the IQ setpoint and measured current (iq_setpoint, iq_measured),
            or (None, None) if no data is received within the timeout period.

        Example:
            >>> iq_setpoint, iq_measured = await odrive_can.get_one_iq_setpoint_measured(timeout=1.0)
            >>> print(f"IQ Setpoint: {iq_setpoint}, IQ Measured: {iq_measured}")
        """
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            msg = await self.async_recv(timeout=timeout - (time.time() - start_time))
            if msg.arbitration_id == (self.nodeID << 5 | 0x14):  # IQ setpoint and measured
                iq_setpoint, iq_measured = struct.unpack('<ff', bytes(msg.data))
                print(f"O-Drive {self.nodeID} - Iq Setpoint: {iq_setpoint:.3f} [A], Iq Measured: {iq_measured:.3f} [A]")
                return iq_setpoint, iq_measured
        return None, None



    async def get_one_powers(self, timeout=1.0):
        """
        Asynchronously retrieves a single power measurement (electrical and mechanical) from the ODrive controller.

        Para:
            timeout (float): The timeout for the operation in seconds.

        Returns:
            A tuple containing the electrical power and mechanical power (electrical_power, mechanical_power),
            or (None, None) if no data is received within the timeout period.

        Example:
            >>> electrical_power, mechanical_power = await odrive_can.get_one_powers(timeout=1.0)
            >>> print(f"Electrical Power: {electrical_power}, Mechanical Power: {mechanical_power}")
        """
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            msg = await self.async_recv(timeout=timeout - (time.time() - start_time))
            if msg.arbitration_id == (self.nodeID << 5 | 0x1D):  # Powers
                electrical_power, mechanical_power = struct.unpack('<ff', bytes(msg.data))
                print(f"O-Drive {self.nodeID} - Electrical Power: {electrical_power:.3f} [W], Mechanical Power: {mechanical_power:.3f} [W]")
                return electrical_power, mechanical_power
        return None, None


    
    async def get_all_data(self):
        """
        Collects all relevant data from the ODrive asynchronously and concurrently.

        Returns:
            A dictionary containing all collected data points.
        """
        # Start all get data tasks concurrently
        tasks = [
            self.get_one_encoder_estimate(),
            self.get_one_torque(),
            self.get_one_bus_voltage_current(),
            self.get_one_iq_setpoint_measured(),
            self.get_one_powers()
        ]
        results = await asyncio.gather(*tasks)

        # Unpack results (ensure the order matches the tasks order)
        pos_vel, torque_target_estimate, bus_voltage_current, iq_setpoint_measured, powers = results

        # Combine all collected data into a dictionary or any structure that suits your needs
        all_data = {
            "pos_vel": pos_vel or (None, None),  # Default to (None, None) if result is None
            "torque_target_estimate": torque_target_estimate or (None, None),
            "bus_voltage_current": bus_voltage_current or (None, None),
            "iq_setpoint_measured": iq_setpoint_measured or (None, None),
            "powers": powers or (None, None),
        }

        # Optionally print or process the collected data
        print(f"Collected Data: {all_data}")

        return all_data



    #This function will take the collected data from the odrive and store each dictionary in a python list while the trial is running.
    #Another function will then take the list at the end and upload it to the database.
    async def collect_data(self):
        """Collects data and appends it to the collected_data list."""
        data = await self.get_all_data()  # Assuming this returns a dictionary of collected data
        self.collected_data.append(data)



    async def collect_and_store_data(self, trial_id):
        """
        Collects data from the ODrive and stores it in the database asynchronously.

        Example:
            >>> await odrive_can.collect_and_store_data()
        """
        # Collect data using the existing async methods
        pos_vel = await self.get_one_encoder_estimate(timeout=1.0)
        torque_target_estimate = await self.get_one_torque(timeout=1.0)
        bus_voltage_current = await self.get_one_bus_voltage_current(timeout=1.0)
        iq_setpoint_measured = await self.get_one_iq_setpoint_measured(timeout=1.0)
        powers = await self.get_one_powers(timeout=1.0)

        # Use datetime to format the current time as a string
        #current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Calculate elapsed time since the start of the program
        current_time = time.time() - self.start_time

        # Prepare your data for insertion
        # (Adjust according to the actual structure of your data and database schema)
        trial_id = trial_id  
        node_ID = self.nodeID
        position, velocity = pos_vel if pos_vel else (None, None)
        torque_target, torque_estimate = torque_target_estimate if torque_target_estimate else (None, None)
        bus_voltage, bus_current = bus_voltage_current if bus_voltage_current else (None, None)
        iq_setpoint, iq_measured = iq_setpoint_measured if iq_setpoint_measured else (None, None)
        electrical_power, mechanical_power = powers if powers else (None, None)

        # Execute the database operation in the thread pool
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, 
            self.insert_data, 
            trial_id, node_ID, current_time, position, velocity, 
            torque_target, torque_estimate, bus_voltage, bus_current, 
            iq_setpoint, iq_measured, electrical_power, mechanical_power
        )
    


    def insert_data(self, trial_id, node_ID, current_time, position, velocity, torque_target, torque_estimate, bus_voltage, bus_current, iq_setpoint, iq_measured, electrical_power, mechanical_power):
        """
        Inserts the collected data into the database. This method should be run in the same thread where the database connection is created.
        """
        # This method assumes you modify your OdriveDatabase class to allow creating a new connection for each operation.
        # Create a new instance of your database class or a new connection here
        db = OdriveDatabase('odrive_data.db')
        db.add_odrive_data(trial_id, node_ID, current_time, position, velocity, torque_target, torque_estimate, bus_voltage, bus_current, iq_setpoint, iq_measured, electrical_power, mechanical_power)



    async def data_collection_loop(self, interval, next_trial_id):
        """
        Continuously collects and stores data at the specified interval.

        Para:
            interval (float): Time between data collection cycles, in seconds.
            next_trial_id (int): Auto increments the trial id using function in Database code.

        Example:
            >>> await odrive_can.data_collection_loop(0.2, next_trial_id)
        """
        while True:
            await self.collect_and_store_data(next_trial_id)
            await asyncio.sleep(interval)



#testing torque and data collection of sync and async code
    def set_torque_sync(self, torque, wait_time):
        """
        Synchronously sets the torque of the ODrive motor and waits for a specified time.

        Para:
            torque (float): Target torque for the motor.
            wait_time (float): Time to wait after setting the torque, in seconds.
        """
        print(" ")
        print(" ")
        print(f"Setting torque to {torque} Nm (synchronously)")
        print(" ")
        print(" ")
        self.set_torque(torque)  # Assuming set_torque is your existing synchronous method
        time.sleep(wait_time)  # Synchronous delay

    async def set_torque_and_wait_async(self, torque, wait_time):
        """
        Asynchronously sets the torque of the ODrive motor and waits for a specified time by
        calling the synchronous set_torque_sync method in a non-blocking way.

        Para:
            torque (float): Target torque for the motor.
            wait_time (float): Time to wait after setting the torque, in seconds.
        """
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.set_torque_sync, torque, wait_time)





async def main():
    # Initialize ODriveCAN with a specific node ID
    nodeID = 1
    odrive_can = ODriveCAN(nodeID=nodeID)

    #Database path
    database = OdriveDatabase('odrive_data.db')
    # Fetch the next trial_id
    next_trial_id = database.get_next_trial_id()
    print(f"Using trial_id: {next_trial_id}")
    
    # Start data collection in the background
    # This task will keep running and collect data into odrive_can.collected_data
    data_collection_task = asyncio.create_task(odrive_can.data_collection_loop(0.1, next_trial_id))
    
    # Sequentially change torque and wait
    # Note: Replace odrive_can.set_torque() with the correct method to set torque if different
    # These methods are assumed to be synchronous. Wrap them in asyncio.run_in_executor if they are not.
    await odrive_can.set_torque_and_wait_async(0.1, 5)  # Set torque to 0.1 Nm, wait 5 seconds
    await odrive_can.set_torque_and_wait_async(0.2, 5)  # Set torque to 0.2 Nm, wait 5 seconds
    await odrive_can.set_torque_and_wait_async(0.0, 5)  # Reset torque to 0 Nm, wait 5 seconds
    
    # Stop the data collection task
    data_collection_task.cancel()
    try:
        await data_collection_task
    except asyncio.CancelledError:
        pass  # Task cancellation is expected

    # Upload collected data to the database
    if hasattr(odrive_can, 'collected_data') and odrive_can.collected_data:
        loop = asyncio.get_running_loop()

        # Wait for the bulk insert to complete
        await loop.run_in_executor(None, database.bulk_insert_odrive_data, odrive_can.collected_data)

        print("Completed Uploading Data to Database.")
    else:
        print("No data collected to upload to the database.")
    
    # Clean shutdown
    odrive_can.bus_shutdown()

if __name__ == "__main__":
    asyncio.run(main())






    """
    def get_one_encoder_estimate(self, timeout=1.0):
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            msg = self.canBus.recv(timeout=timeout - (time.time() - start_time))
            if msg is None:
                print("Timeout occurred, no message received.")
                break

            if msg.arbitration_id == (self.nodeID << 5 | 0x09):  # Encoder estimate
                pos, vel = struct.unpack('<ff', bytes(msg.data))
                print(f"O-Drive {self.nodeID} - pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")
                break
        else:
            print(f"No encoder estimate message received for O-Drive {self.nodeID} within the timeout period.")

    

    # Function to print torque feedback for a specific O-Drive one time
    def get_one_torque(self, timeout=1.0):
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            msg = self.canBus.recv(timeout=timeout - (time.time() - start_time))  # Adjust timeout for recv
            if msg is None:
                print("Timeout occurred, no message received.")
                break

            if msg.arbitration_id == (self.nodeID << 5 | 0x1C):  # 0x1C: Get_Torques
                torque_target, torque_estimate = struct.unpack('<ff', bytes(msg.data))
                print(f"O-Drive {self.nodeID} - Torque Target: {torque_target:.3f} [Nm], Torque Estimate: {torque_estimate:.3f} [Nm]")
                break
        else:
            print(f"No torque message received for O-Drive {self.nodeID} within the timeout period.")



    def get_one_bus_voltage_current(self, timeout=1.0):
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            msg = self.canBus.recv(timeout=timeout - (time.time() - start_time))
            if msg is None:
                print("Timeout occurred, no message received.")
                break

            if msg.arbitration_id == (self.nodeID << 5 | 0x17):  # Bus voltage and current
                bus_voltage, bus_current = struct.unpack('<ff', bytes(msg.data))
                print(f"O-Drive {self.nodeID} - Bus Voltage: {bus_voltage:.3f} [V], Bus Current: {bus_current:.3f} [A]")
                break
        else:
            print(f"No bus voltage or current message received for O-Drive {self.nodeID} within the timeout period.")


    def get_one_iq_setpoint_measured(self, timeout=1.0):
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            msg = self.canBus.recv(timeout=timeout - (time.time() - start_time))
            if msg is None:
                print("Timeout occurred, no message received.")
                break

            if msg.arbitration_id == (self.nodeID << 5 | 0x14):  # IQ setpoint and measured
                iq_setpoint, iq_measured = struct.unpack('<ff', bytes(msg.data))
                print(f"O-Drive {self.nodeID} - Iq Setpoint: {iq_setpoint:.3f} [A], Iq Measured: {iq_measured:.3f} [A]")
                break
        else:
            print(f"No IQ setpoint or measured message received for O-Drive {self.nodeID} within the timeout period.")


    #This doesn't work the default cyclic message isn't set on O-Drive GUI yet. 
    def get_one_powers(self, timeout=1.0):
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            msg = self.canBus.recv(timeout=timeout - (time.time() - start_time))
            if msg is None:
                print("Timeout occurred, no message received.")
                break

            if msg.arbitration_id == (self.nodeID << 5 | 0x1D):  # Powers
                electrical_power, mechanical_power = struct.unpack('<ff', bytes(msg.data))
                print(f"O-Drive {self.nodeID} - Electrical Power: {electrical_power:.3f} [W], Mechanical Power: {mechanical_power:.3f} [W]")
                break
        else:
            print(f"No power message received for O-Drive {self.nodeID} within the timeout period.")



    
    def get_all_data(self):
        # Collect data from each function
        encoder_data = self.get_one_encoder_estimate() 
        torque_data = self.get_one_bus_voltage_current()
        voltage_current_data = self.get_one_bus_voltage_current()
        iq_setpoint_measured_data = self.get_one_iq_setpoint_measured()
        power_data = self.get_one_powers()

        # Format each value to 3 decimal places if they are numeric
        def format_data(data):
            if isinstance(data, tuple):
                return tuple(format(x, '.3f') if isinstance(x, (int, float)) else x for x in data)
            return data

        encoder_data_formatted = format_data(encoder_data)
        torque_data_formatted = format_data(torque_data)
        voltage_current_data_formatted = format_data(voltage_current_data)
        iq_setpoint_measured_data_formatted = format_data(iq_setpoint_measured_data)
        power_data_formatted = format_data(power_data)

        # Print formatted data
        print("Data: {}, {},  {}, {}"
            .format(encoder_data_formatted,
                    torque_data_formatted,
                    voltage_current_data_formatted,
                    iq_setpoint_measured_data_formatted,
                    power_data_formatted
                    ))

        # Compile all data into a single structure (dictionary for better readability)
        all_data = {
            "encoder_data": encoder_data,
            "torque_data": torque_data,
            "voltage_current_data": voltage_current_data,
            "iq_setpoint_measured_data": iq_setpoint_measured_data,
            "power_data": power_data_formatted
        }

        # Format and print all data in one line not limiting how many decimal places printed.
        #print("Data: {}, {}, {}, {}".format(encoder_data, torque_data, voltage_current_data, iq_setpoint_measured_data))

        return all_data

    """


'''
    async def get_all_data(self):
        """
        Collects all relevant data from the ODrive asynchronously.

        Returns:
            A dictionary containing all collected data points.

        Example:
            >>> all_data = await odrive_can.get_all_data()
            >>> print(all_data)
        """
        # Collect data asynchronously from each function
        pos_vel = await self.get_one_encoder_estimate(timeout=1.0)
        torque_target_estimate = await self.get_one_torque(timeout=1.0)
        bus_voltage_current = await self.get_one_bus_voltage_current(timeout=1.0)
        iq_setpoint_measured = await self.get_one_iq_setpoint_measured(timeout=1.0)
        powers = await self.get_one_powers(timeout=1.0)

        # Combine all collected data into a dictionary or any structure that suits your needs
        all_data = {
            "pos_vel": pos_vel,
            "torque_target_estimate": torque_target_estimate,
            "bus_voltage_current": bus_voltage_current,
            "iq_setpoint_measured": iq_setpoint_measured,
            "powers": powers,  
        }

        # Optionally print or process the collected data
        # For example, print the data or store it in a database
        print(f"Collected Data: {all_data}")

        return all_data
'''
        