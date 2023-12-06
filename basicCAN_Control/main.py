import board 
import can
import struct
import time


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


#-------------------------------------- Motor Controls ----------------------------------------------------
  
    # Function to set position for a specific O-Drive
    def set_position(self, position, velocity_feedforward=0, torque_feedforward=0):
        self.canBus.send(can.Message(
            arbitration_id=(self.nodeID << 5 | 0x0C),
            data=struct.pack('<fhh', float(position), velocity_feedforward, torque_feedforward),
            is_extended_id=False
        ))
        print(f"Successfully moved ODrive {self.nodeID} to {position}")
        


    # Function to set velocity for a specific O-Drive
    def set_velocity(self, velocity, torque_feedforward=0.0):
        self.canBus.send(can.Message(
            arbitration_id=(self.nodeID << 5 | 0x0d),  # 0x0d: Set_Input_Vel
            data=struct.pack('<ff', velocity, torque_feedforward),
            is_extended_id=False
        ))



    # Function to set torque for a specific O-Drive
    def set_torque(self, torque):
        self.canBus.send(can.Message(
            arbitration_id=(self.nodeID << 5 | 0x0E),  # 0x0E: Set_Input_Torque
            data=struct.pack('<f', torque),
            is_extended_id=False
        ))
        print(f"Successfully set ODrive {self.nodeID} to {torque} [Nm]")




#-------------------------------------- Motor Feedback ----------------------------------------------------


    # Function to print torque feedback for a specific O-Drive (will get stuck in for loop forever)
    def get_torques(self):
        print(f"I am trying to get torque for {self.nodeID}")
        for msg in self.canBus:
            if msg.arbitration_id == (self.nodeID << 5 | 0x1C):  # 0x1C: Get_Torques
                torque_target, torque_estimate = struct.unpack('<ff', bytes(msg.data))
                print(f"O-Drive {self.nodeID} - Torque Target: {torque_target:.3f} [Nm], Torque Estimate: {torque_estimate:.3f} [Nm]")





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



#-------------------------------------- Motor Feedback with CAN RTR ----------------------------------------------------

    def send_rtr_message(self, request_id):
        try:
            # Create an RTR frame
            rtr_frame = can.Message(
                arbitration_id=(self.nodeID << 5 | request_id),
                is_remote_frame=True,
                is_extended_id=False
            )

            # Send the RTR frame
            self.canBus.send(rtr_frame)

        except Exception as e:
            print(f"Error sending RTR message to ODrive {self.nodeID}, request_id {request_id}: {str(e)}")

    def get_encoder_estimate_rtr(self):
        request_id = 0x09
        self.send_rtr_message(request_id)

        # Wait for a response
        response = self.canBus.recv(timeout=1.0)

        if response:
            pos, vel = struct.unpack('<ff', bytes(response.data))
            print(f"O-Drive {self.nodeID} - pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")
            return pos, vel
        else:
            print(f"No response received for ODrive {self.nodeID}, request_id {request_id}")

    def get_torque_rtr(self):
        request_id = 0x1C
        self.send_rtr_message(request_id)

        # Wait for a response
        response = self.canBus.recv(timeout=1.0)

        if response:
            torque_target, torque_estimate = struct.unpack('<ff', bytes(response.data))
            print(f"O-Drive {self.nodeID} - Torque Target: {torque_target:.3f} [Nm], Torque Estimate: {torque_estimate:.3f} [Nm]")
            return torque_target, torque_estimate
        else:
            print(f"No response received for ODrive {self.nodeID}, request_id {request_id}")


    def get_bus_voltage_current_rtr(self):
        request_id = 0x17
        self.send_rtr_message(request_id)

        # Wait for a response
        response = self.canBus.recv(timeout=1.0)

        if response:
            bus_voltage, bus_current = struct.unpack('<ff', bytes(response.data))
            print(f"O-Drive {self.nodeID} - Bus Voltage: {bus_voltage:.3f} [V], Bus Current: {bus_current:.3f} [A]")
            return bus_voltage, bus_current
        else:
            print(f"No response received for ODrive {self.nodeID}, request_id {request_id}")


    def get_iq_setpoint_measured_rtr(self):
        request_id = 0x14
        self.send_rtr_message(request_id)

        # Wait for a response
        response = self.canBus.recv(timeout=1.0)

        if response:
            iq_setpoint, iq_measured = struct.unpack('<ff', bytes(response.data))
            print(f"O-Drive {self.nodeID} - Iq Setpoint: {iq_setpoint:.3f} [A], Iq Measured: {iq_measured:.3f} [A]")
            return iq_setpoint, iq_measured
        else:
            print(f"No response received for ODrive {self.nodeID}, request_id {request_id}")


    
    def get_all_data_rtr(self):
        # Collect data from each function
        encoder_data = self.get_encoder_estimate_rtr()
        torque_data = self.get_torque_rtr()
        voltage_current_data = self.get_bus_voltage_current_rtr()
        iq_setpoint_measured_data = self.get_iq_setpoint_measured_rtr()

        # Compile all data into a single structure (dictionary for better readability)
        all_data = {
            "encoder_data": encoder_data,
            "torque_data": torque_data,
            "voltage_current_data": voltage_current_data,
            "iq_setpoint_measured_data": iq_setpoint_measured_data
        }

        return all_data


#Example on how to use:

odrive1 = ODriveCAN(0)

odrive1.initCanBus()

#Example how to print all data 
all_data = odrive1.get_all_data_rtr()
print(all_data)


#odrive1.set_torque(5)



#odrive2 = ODriveCAN(2)

#odrive2.initCanBus()


