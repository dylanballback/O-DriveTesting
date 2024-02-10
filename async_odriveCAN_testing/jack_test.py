import asyncio
import can
import struct
import time
from datetime import datetime, timedelta
from odrivedatabase import OdriveDatabase

"""
Testing if recv timeout=0 still gets messages.
"""


class ODriveCAN:
    def __init__(self, nodeID, canBusID="can0", canBusType="socketcan", position=None, velocity=None, torque_target=None, torque_estimate=None, bus_voltage=None, bus_current=None, iq_setpoint=None, iq_measured=None, electrical_power=None, mechanical_power=None):
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
        self.latest_data = {}
        self.running = True
        #O-Drive Data
        self.position = position
        self.velocity = velocity
        self.torque_target = torque_target
        self.torque_estimate = torque_estimate
        self.bus_voltage = bus_voltage
        self.bus_current = bus_current
        self.iq_setpoint = iq_setpoint
        self.iq_measured = iq_measured
        self.electrical_power = electrical_power
        self.mechanical_power = mechanical_power



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


    def process_can_message(self, message):
        """Processes received CAN messages and updates the latest data."""
        arbitration_id = message.arbitration_id
        data = message.data
        if arbitration_id == (self.nodeID << 5 | 0x09):  # Encoder estimate
            position, velocity = struct.unpack('<ff', data)
            self.latest_data['encoder_estimate'] = (position, velocity)
            print(f"Encoder Estimate - Position: {position:.3f} turns, Velocity: {velocity:.3f} turns/s")
        elif arbitration_id == (self.nodeID << 5 | 0x1C):  # Torque
            torque_target, torque_estimate = struct.unpack('<ff', data)
            self.latest_data['torque'] = (torque_target, torque_estimate)
            print(f"Torque - Target: {torque_target:.3f} Nm, Estimate: {torque_estimate:.3f} Nm")
        elif arbitration_id == (self.nodeID << 5 | 0x17):  # Bus voltage and current
            bus_voltage, bus_current = struct.unpack('<ff', data)
            self.latest_data['bus_voltage_current'] = (bus_voltage, bus_current)
            print(f"Bus Voltage and Current - Voltage: {bus_voltage:.3f} V, Current: {bus_current:.3f} A")
        elif arbitration_id == (self.nodeID << 5 | 0x14):  # IQ setpoint and measured
            iq_setpoint, iq_measured = struct.unpack('<ff', data)
            self.latest_data['iq_set_measured'] = (iq_setpoint, iq_measured)
            print(f"IQ Setpoint and Measured - Setpoint: {iq_setpoint:.3f} A, Measured: {iq_measured:.3f} A")
        elif arbitration_id == (self.nodeID << 5 | 0x1D):  # Powers
            electrical_power, mechanical_power = struct.unpack('<ff', data)
            self.latest_data['power'] = (electrical_power, mechanical_power)
            print(f"Powers - Electrical: {electrical_power:.3f} W, Mechanical: {mechanical_power:.3f} W")


    async def recv_all(self):
        while self.running:
            await asyncio.sleep(0)
            msg = self.canBus.recv(timeout=0)
            if msg is not None:
                self.process_can_message(msg)

    

    async def save_data(self, timeout=0.1):
        # Fetch the next trial_id
        next_trial_id = self.database.get_next_trial_id()
        print(f"Using trial_id: {next_trial_id}")
        node_id = self.nodeID
        while self.running:
            await asyncio.sleep(timeout)
            # Calculate elapsed time since the start of the program
            current_time = time.time() - self.start_time
            self.database.add_odrive_data(
                next_trial_id,
                node_id,
                current_time,
                self.position,
                self.velocity,
                self.torque_target,
                self.torque_estimate,
                self.bus_voltage,
                self.bus_current,
                self.iq_setpoint,
                self.iq_measured,
                self.electrical_power,
                self.mechanical_power
            )


    async def loop(self, *others):
        await asyncio.gather(
            self.recv_all(),
            self.save_data(),
            *others,
        )

    def run(self, *others):
        asyncio.run(self.loop(*others))
            

async def controller(odrive):
        odrive.set_torque(0.2)
        await asyncio.sleep(5)
        odrive.running = False
        


if __name__ == "__main__":
    # Initialize ODriveCAN to node_id 0 
    odrive = ODriveCAN(1)
    odrive.initCanBus()
    odrive.run(controller(odrive))