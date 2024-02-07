from ODriveCAN import ODriveCAN


# Initialize ODriveCAN to node_id 0 
odrive = ODriveCAN(0)
odrive.initCanBus()

def main():
    # Set torque
    odrive.set_torque(.2)

    while True:
        all_data = odrive.get_all_data_rtr()
        #print(all_data)

        

        
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        odrive.set_torque(0)

        odrive.bus_shutdown()

        print("Program interrupted by user. Exiting.")