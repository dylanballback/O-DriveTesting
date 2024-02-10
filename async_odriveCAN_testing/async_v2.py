import asyncio
import can
import struct
import time
from odrivedatabase import OdriveDatabase


class ODriveCAN:
    def __init__(self, nodeID, canBusID="can0", canBusType="socketcan"):
        self.nodeID = nodeID
        self.canBusID = canBusID
        self.canBusType = canBusType
        self.canBus = can.interface.Bus(canBusID, bustype=canBusType)
        self.latest_data = {}
        self.running = True
        self.database = OdriveDatabase('odrive_data.db')
        self.collected_data = []  # Initialize an empty list to store data
        self.start_time = time.time()  # Capture the start time when the object is initialized

    

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




    async def continuous_can_reading(self):
        """Continuously reads CAN messages and updates the latest data."""
        while self.running:
            message = await self.async_recv()
            if message:
                self.process_can_message(message)

    async def async_recv(self):
        """Asynchronously receives a CAN message."""
        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(None, self.canBus.recv)
        return message

    def process_can_message(self, message):
        """Processes received CAN messages and updates the latest data."""
        arbitration_id = message.arbitration_id
        data = message.data
        if arbitration_id == (self.nodeID << 5 | 0x09):  # Encoder estimate
            self.latest_data['encoder_estimate'] = struct.unpack('<ff', data)
        elif arbitration_id == (self.nodeID << 5 | 0x1C):  # Torque
            self.latest_data['torque'] = struct.unpack('<ff', data)
        elif arbitration_id == (self.nodeID << 5 | 0x17):  # Bus voltage and current
            self.latest_data['bus_voltage_current'] = struct.unpack('<ff', data)
        elif arbitration_id == (self.nodeID << 5 | 0x14):  # IQ setpoint and measured
            self.latest_data['iq_set_measured'] = struct.unpack('<ff', data)
        elif arbitration_id == (self.nodeID << 5 | 0x1D):  # Powers
            self.latest_data['power'] = struct.unpack('<ff', data)

    async def collect_data_at_interval(self, interval, trial_id):
        """Collects the latest data at set intervals."""
        while self.running:
            current_data_snapshot = self.latest_data.copy()  # Take a snapshot of the latest data
            print(f"Collected Data at {time.time()}: {current_data_snapshot}")
            await asyncio.sleep(interval)
        self.insert_collected_data_into_db(trial_id)


    def insert_collected_data_into_db(self, trial_id):
        for data_point in self.collected_data:
            current_time, data = data_point
            position, velocity = data.get('encoder_estimate', (None, None))
            torque_target, torque_estimate = data.get('torque', (None, None))
            bus_voltage, bus_current = data.get('bus_voltage_current', (None, None))
            iq_setpoint, iq_measured = data.get('iq_set_measured', (None, None))
            electrical_power, mechanical_power = data.get('power', (None, None))
            # Assuming trial_id and node_ID need to be set appropriately
            trial_id = trial_id  
            node_ID = self.nodeID
            self.insert_data(trial_id, node_ID, current_time, position, velocity, torque_target, torque_estimate, bus_voltage, bus_current, iq_setpoint, iq_measured, electrical_power, mechanical_power)

    def insert_data(self, trial_id, node_ID, current_time, position, velocity, torque_target, torque_estimate, bus_voltage, bus_current, iq_setpoint, iq_measured, electrical_power, mechanical_power):
        self.database.add_odrive_data(trial_id, node_ID, current_time, position, velocity, torque_target, torque_estimate, bus_voltage, bus_current, iq_setpoint, iq_measured, electrical_power, mechanical_power)


    def start(self):
        """Starts the continuous reading and data collection tasks."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(
            self.continuous_can_reading(),
            self.collect_data_at_interval(0.1)  # Collect data every 0.1 seconds
        ))

    def stop(self):
        """Stops the continuous reading and data collection."""
        self.running = False

    async def set_torque_async(self, torque, duration):
        """Asynchronously sets the torque and waits for a specified duration."""
        print(f"Setting torque to {torque} Nm")
        self.set_torque(torque)
        await asyncio.sleep(duration)

async def main():
    odrive_can = ODriveCAN(1)

    # Initialize CAN bus and prepare for operations
    odrive_can.initCanBus()

    #Database path
    database = OdriveDatabase('odrive_data.db')
    # Fetch the next trial_id
    next_trial_id = database.get_next_trial_id()
    print(f"Using trial_id: {next_trial_id}")


    # Start continuous CAN reading and data collection in the background
    loop = asyncio.get_event_loop()
    continuous_reading_task = loop.create_task(odrive_can.continuous_can_reading())
    data_collection_task = loop.create_task(odrive_can.collect_data_at_interval(0.1, next_trial_id))
    
    

    # Sequentially set torque values
    await odrive_can.set_torque_async(0.1, 5)  # Set torque to 0.1 Nm, wait 5 seconds
    await odrive_can.set_torque_async(0.2, 5)  # Set torque to 0.2 Nm, wait 5 seconds
    await odrive_can.set_torque_async(0.0, 5)  # Reset torque to 0 Nm, wait 5 seconds

    # Stop the continuous reading and data collection tasks
    odrive_can.stop()
    continuous_reading_task.cancel()
    data_collection_task.cancel()
    try:
        await continuous_reading_task
        await data_collection_task
    except asyncio.CancelledError:
        pass  # Task cancellation is expected

    # Shutdown CAN bus
    odrive_can.bus_shutdown()

if __name__ == "__main__":
    asyncio.run(main())