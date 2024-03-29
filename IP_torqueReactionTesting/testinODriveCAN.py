from ODriveCAN import ODriveCAN

# Initialize ODriveCAN to node_id 0 
odrive = ODriveCAN(0)
odrive.initCanBus()

#drive2 = ODriveCAN(1)
#odrive2.initCanBus()


def main():
    # Set torque
    odrive.set_torque(.2)
    #odrive2.set_torque(.2)
    

    while True:
        #odrive.get_one_encoder_estimate()
        #odrive.get_one_torque()
        #odrive.get_one_iq_setpoint_measured()
        #odrive.get_one_bus_voltage_current()
        #odrive.get_one_powers()
        odrive.get_all_data()

        #odrive.get_encoder_estimate_rtr()
        #odrive.get_torque_rtr()
        #odrive.get_bus_voltage_current_rtr()
        #odrive.get_iq_setpoint_measured_rtr()
        #odrive.get_powers_rtr()
        #odrive.get_encoder_estimate_rtr()
        #odrive.get_all_data_rtr()
        #odrive2.get_all_data_rtr()
        pass

        

        
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        odrive.set_torque(0)
        #odrive2.set_torque(0)

        odrive.bus_shutdown()
        #odrive2.bus_shutdown()

        print("Program interrupted by user. Exiting.")