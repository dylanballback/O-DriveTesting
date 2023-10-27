import board 
import can


class ODriveCAN:
    """
    A class for setting up O-Drive motor controllers using CAN comunincation 

    Attributes:
        Specifically for setting up CAN comunication between Raspberry Pi and CAN Communication Type:
            canBusID (String): Can Bus ID should be default "can0" but if you have muilitiple can buses on your device you can modify here

            canBusType (String): python-can package CAN communication type we by default us "socketcan"

        O-Drive Controller Specific Attributes:
        nodeID (integer): The node ID can be set by the 
    """

    def __init__(self, canBusID, canBusType, nodeID):
        self.canBusID = canBusID
        self.canBusType = canBusType
        self.nodeID = nodeID





    def setNodeID(self):
        """
        Sets NodeID for an O-Drive Controller through CAN BUS
        """

        pass



    def setAxisState(self):
        """
        
        """