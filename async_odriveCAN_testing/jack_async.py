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
        self.MESSAGES = []



    async def async_recv(self, timeout=1.0):
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

    async def recev(self, stop_at):
        while not self.MESSAGES and datetime.now() < stop_at:
            time.sleep(0.01)
        if self.MESSAGES:
            return self.MESSAGES.pop()
        
    
    async def send(self, msg):
        await asyncio.sleep(1)
        self.MESSAGES.append(msg)

    async def get_torque(self):
        asyncio.create_task(send("torque"))
        msg = await recv(datetime.now() + timedelta(seconds=2))
        print(msg)

    async def get_velocity():
        asyncio.create_task(send("velocity"))
        msg = await recv(datetime.now() + timedelta(seconds=2))
        print(msg)


async def main():
    # Initialize ODriveCAN with a specific node ID
    nodeID = 1
    odrive_can = ODriveCAN(nodeID=nodeID)




if __name__ == "__main__":
    asyncio.run(main())

