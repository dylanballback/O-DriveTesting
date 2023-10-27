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




    def setAxisNodeID(self):
        """
        Sets Axis NodeID for an O-Drive Controller through CAN BUS

        Set_Axis_NodeID: 0x06
        """

        pass




    def setAxisState(self):
        """
        Set Axis State for an O-Drive Controller through CAN BUS

        
        CAN Set_Axis_State: 0x07
            Axis_Requested_State:
                Undefined:                           0x0
                Idle:                                0x1
                Startup_Sequence:                    0x2
                Full_Calibration_Sequence:           0x3
                Motor_Calibration:                   0x4 
                Encoder_Index_Search:                0x5
                Encoder_Offset_Calibration:          0x6
                Closed_Loop_Control:                 0x7
                Lockin_Spin:                         0x8
                Encoder_DIR_Find:                    0x9
                Homing:                              0xA
                Encoder_Hall_Polarity_Calibration:   0xB
                Encoder_Hall_Phase_Calibration:      0xD
        """
        pass





    def setControllerMode(self):
            """
            Set the O-Drive Controller Mode type 

            Attribute: 
                CAN Set_Controller_Mode: 0x0B
                        Control_Mode:
                            Voltage_Control:   0x0
                            Torque_Control:    0x1
                            Velocity_Control:  0x2
                            Position_Control:  0x3

                        Input_Mode:
                            Inactive:      0x0
                            Passthrough:   0x1
                            VEL_Ramp:      0x2
                            Pos_Filter:    0x3
                            Mix_Channels:  0x4
                            Trap_Traj:     0x5
                            Torque_Ramp:   0x6
                            Mirror:        0x7  
                            Tunning:       0x8 
            """
            pass




    def getAxisEncoderEstimates(self):
        """
        Get Encoder Estimates for specific O-Drive Controller Axis through CAN BUS

        CAN Get_Encoder_Estimates: 0x09
                    - Pos_Estimate 
                    - Vel_Estimate

        Attributes:
            Axis_ID 


        Returns:
            Pos_Estimate
            Vel_Estimate 
        """
        pass




  
