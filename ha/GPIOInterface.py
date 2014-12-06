
from ha.HAClasses import *
#import RPi.GPIO as gpio
import RPIO as gpio

class GPIOInterface(HAInterface):
    # MCP23017 I2C I/O expander
    baseAddr = 0x20
    nControls = 1
    ioDirRegister = 0x00
    ioPullupRegister = 0x0c
    ioRegister = 0x12
    # direct GPIO
    pins = [12, 16, 18, 22, 15, 13, 11, 7]
    
    def __init__(self, name, I2CInterface=None):
        self.name = name
        if I2CInterface:
            HAInterface.__init__(self, name, I2CInterface)
        else:
            self.interface = None
            gpio.setwarnings(False)
            gpio.setmode(gpio.BOARD)
            for pin in GPIOInterface.pins:
	            gpio.setup(pin, gpio.OUT)
	            gpio.output(pin, 0)
    
    def start(self):
        if self.interface:
            for control in range(GPIOInterface.nControls):
                addr = GPIOInterface.baseAddr + control
#                self.interface.write((addr, GPIOInterface.ioDirRegister), 0xff)     # bank 0 input
#                self.interface.write((addr, GPIOInterface.ioPullupRegister), 0xff)  # bank 0 pullup
                self.interface.write((addr, GPIOInterface.ioDirRegister), 0x00)   # bank 0 output
#                self.interface.write((addr, GPIOInterface.ioDirRegister+1), 0xff)     # bank 1 input
#                self.interface.write((addr, GPIOInterface.ioPullupRegister+1), 0xff)  # bank 1 pullup
                self.interface.write((addr, GPIOInterface.ioDirRegister+1), 0x00)   # bank 1 output

    def read(self, theAddr):
        if self.interface:
            byte = self.interface.read((GPIOInterface.baseAddr+theAddr.control, GPIOInterface.ioRegister+theAddr.bank))
            return (byte >> theAddr.start) & ((1<<theAddr.width)-1)
        else:
            return 0

    def write(self, theAddr, theValue):
        if self.interface:
            byte = self.interface.read((GPIOInterface.baseAddr+theAddr.control, GPIOInterface.ioRegister+theAddr.bank))
            mask = ((1<<theAddr.width)-1)<<theAddr.start
            byte = (byte & (~mask)) | ((theValue << theAddr.start) & mask)
            self.interface.write((GPIOInterface.baseAddr+theAddr.control, GPIOInterface.ioRegister+theAddr.bank), byte)
        else:
        		gpio.output(GPIOInterface.pins[theAddr.start], theValue)
            
        
class GPIOAddr(object):
    def __init__(self, control, bank, start, width):
        self.control = control  # the I/O chip
        self.bank = bank        # the 8 bit bank of I/O pins within the chip
        self.start = start      # the starting pin
        self.width = width      # the number of pins

    def __str__(self):
        return "(%2d, %2d, %2d, %2d)"%(self.control, self.bank, self.start, self.width)

