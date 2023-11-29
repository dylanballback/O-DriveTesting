#Derived from sosandroid's AMS_AS5048B Arduino library,
#https://github.com.cnpmjs.org/sosandroid/AMS_AS5048B

import sys
import smbus
import time

bus=smbus.SMBus(1)
RE_ADDRESS_LIST = [0x40]
RE_ZEROMSB_REG = 0x16 #Zero, most significant byte
RE_ZEROLSB_REG = 0x17 #Zero, least significant byte
RE_ANGLEMSB_REG = 0xFE #Angle, most significant byte
RE_ANGLELSB_REG = 0xFF #Angle, least significant byte

#sets initial position to zero
for RE_ADDRESS in RE_ADDRESS_LIST:
    bus.write_byte_data(RE_ADDRESS,RE_ZEROMSB_REG,0x00)
    bus.write_byte_data(RE_ADDRESS,RE_ZEROLSB_REG,0x00)
    ANG_M = bus.read_byte_data(RE_ADDRESS,RE_ANGLEMSB_REG)
    ANG_L = bus.read_byte_data(RE_ADDRESS,RE_ANGLELSB_REG)
    bus.write_byte_data(RE_ADDRESS,RE_ZEROMSB_REG,ANG_M)
    bus.write_byte_data(RE_ADDRESS,RE_ZEROLSB_REG,ANG_L)
    
#polling
while True:
    ANG_M1 = bus.read_byte_data(0x40,0x16)
    ANG_L1 = bus.read_byte_data(0x40,0x17)

    ANG1 = (ANG_M1<<6)+(ANG_L1 & 0x3f)

    time.sleep(0.1)