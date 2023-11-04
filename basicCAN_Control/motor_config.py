import board 
import can
import struct


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
    def __init__(self, canBusID="can0", canBus="socketcan", nodeID):
        self.canBusID = canBusID
        self.canBus = canBus
        self.nodeID = nodeID




    def initCanBus(self):
        """
        Initalize connection to CAN Bus

        canBusID (String): Default "can0" this is the name of the can interface
        canBus (String): Default "socketcan" this is the python can libary CAN type
        """
        can.interface.Bus(self.canBusID, self.canBus)




    def flush_can_buffer(self):
        #Flush CAN RX buffer to ensure no old pending messages.
        while not (self.canBus.recv(timeout=0) is None): pass
        print("I have cleared all CAN Messages on the BUS!")




    #I don't know if you can do this through CAN, you need to use webGUI
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




    # setAxisState into closed loop control state
    def set_control_state(self):
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




  
    # Function to set position for a specific O-Drive
    def set_position(self, node_id, position, velocity_feedforward=0, torque_feedforward=0):
        self.canBus.send(can.Message(
            arbitration_id=(node_id << 5 | 0x0C),
            data=struct.pack('<fhh', float(position), velocity_feedforward, torque_feedforward),
            is_extended_id=False
        ))
        print(f"Successfully moved ODrive {node_id} to {position}")
        


    # Function to set velocity for a specific O-Drive
    def set_velocity(self, node_id, velocity, torque_feedforward=0.0):
        self.canBus.send(can.Message(
            arbitration_id=(node_id << 5 | 0x0d),  # 0x0d: Set_Input_Vel
            data=struct.pack('<ff', velocity, torque_feedforward),
            is_extended_id=False
        ))



    # Function to set torque for a specific O-Drive
    def set_torque(self, node_id, torque):
        self.canBus.send(can.Message(
            arbitration_id=(node_id << 5 | 0x0E),  # 0x0E: Set_Input_Torque
            data=struct.pack('<f', torque),
            is_extended_id=False
        ))
        print(f"Successfully set ODrive {node_id} to {torque} [Nm]")





#Example on how to use:

odrive1 = ODriveCAN(0)

odrive1.initCanBus()

odrive1.set_torque(5)



odrive2 = ODriveCAN(2)

odrive2.initCanBus()


