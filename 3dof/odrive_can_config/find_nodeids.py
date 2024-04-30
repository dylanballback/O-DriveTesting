import argparse
import asyncio
import time
import sys

import can

ADDRESS_CMD = 0x06

BROADCAST_NODE_ID = 0x3f

DISCOVERY_MESSAGE_INTERVAL = 0.6

def sn_str(sn):
    return f"{sn:012X}"

def get_address_msg(bus: can.Bus):
    msg = can.Message(
        arbitration_id=(BROADCAST_NODE_ID << 5) | ADDRESS_CMD,
        is_extended_id=False,
        is_remote_frame=True
    )
    bus.send(msg)

class Discoverer():
    def __init__(self, bus):
        self.bus = bus
        self.discovered_devices = {}  # serial_number: node_id

    def __enter__(self):
        self.notifier = can.Notifier(self.bus, [self.on_message_received], loop=asyncio.get_running_loop())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.notifier.stop()
        pass

    def on_message_received(self, msg):
        cmd_id = msg.arbitration_id & 0x1F

        if cmd_id == ADDRESS_CMD:
            node_id = msg.data[0]
            serial_number = int.from_bytes(msg.data[1:7], byteorder='little')
            self.discovered_devices[serial_number] = node_id if node_id != BROADCAST_NODE_ID else None

async def scan_for_devices(bus):
    print(f"Scanning for ODrives...")

    with Discoverer(bus) as discoverer:
        iteration_count = 0
        while True:
            iteration_count += 1
            get_address_msg(bus)
            await asyncio.sleep(DISCOVERY_MESSAGE_INTERVAL)

            # Exit the loop after sending discovery messages a few times
            if iteration_count >= 3:
                break

    print(f"Scan complete. Discovered {len(discoverer.discovered_devices)} ODrives.")
    for serial, node_id in discoverer.discovered_devices.items():
        print(f"ODrive {sn_str(serial)} has node ID {node_id if node_id is not None else 'unaddressed'}")
    return discoverer.discovered_devices

async def main():
    parser = argparse.ArgumentParser(description="Script to display ODrive devices on a CAN bus.")
    parser.add_argument('-i', '--interface', type=str, default='socketcan', help='Interface type (e.g., socketcan, slcan). Default is socketcan.')
    parser.add_argument('-c', '--channel', type=str, required=True, help='Channel/path/interface name of the device (e.g., can0, /dev/tty.usbmodem11201).')
    parser.add_argument('-b', '--bitrate', type=int, default=250000, help='Bitrate for CAN bus. Default is 250000.')
    
    args = parser.parse_args()

    with can.interface.Bus(args.channel, bustype=args.interface, bitrate=args.bitrate) as bus:
        await scan_for_devices(bus)

    sys.exit(0)

if __name__ == '__main__':
    asyncio.run(main())
