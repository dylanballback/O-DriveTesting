from ODriveCAN import ODriveCAN


# Initialize ODriveCAN to node_id 0 
odrive = ODriveCAN(0)
odrive.initCanBus()

odrive2 = ODriveCAN(1)
odrive2.initCanBus()


def main():
    # Set torque
    odrive.set_torque(.2)
    odrive2.set_torque(.2)


    while True:
        #odrive.get_all_data_rtr()
        #odrive2.get_all_data_rtr()
        pass

        

        
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        odrive.set_torque(0)
        odrive2.set_torque(0)

        odrive.bus_shutdown()
        odrive2.bus_shutdown()

        print("Program interrupted by user. Exiting.")