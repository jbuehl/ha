
from ha.HAClasses import *
#import RPi.GPIO as gpio
import RPIO as gpio

class GPIOInterface(HAInterface):
    # MCP23017 I2C I/O expander
    ioDirRegister = 0x00
    ioPullupRegister = 0x0c
    ioRegister = 0x12
    # direct GPIO
    pins = [12, 16, 18, 22, 15, 13, 11, 7]   # A/B
#            32, 36, 38, 40, 37, 35, 33, 31]     # B+
    
    def __init__(self, name, I2CInterface=None, addr=0x20, inOut=[0x00, 0x00]):
        self.name = name
        if I2CInterface:
            HAInterface.__init__(self, name, I2CInterface)
            self.addr = addr
            self.inOut = inOut
        else:
            self.interface = None
            gpio.setwarnings(False)
            gpio.setmode(gpio.BOARD)
            for pin in GPIOInterface.pins:
	            gpio.setup(pin, gpio.OUT)
	            gpio.output(pin, 0)
    
    def start(self):
        if self.interface:
            for bank in range(2):
                self.interface.write((self.addr, GPIOInterface.ioDirRegister+bank), self.inOut[bank])     # direction
                self.interface.write((self.addr, GPIOInterface.ioPullupRegister+bank), self.inOut[bank])  # pullup
        else:
            pass

    def read(self, gpioAddr):
        if self.interface:
            byte = self.interface.read((self.addr, GPIOInterface.ioRegister+gpioAddr.bank))
            return (byte >> gpioAddr.start) & ((1<<gpioAddr.width)-1)
        else:
            return 0

    def write(self, gpioAddr, value):
        if self.interface:
            byte = self.interface.read((self.addr, GPIOInterface.ioRegister+gpioAddr.bank))
            mask = ((1<<gpioAddr.width)-1)<<gpioAddr.start
            byte = (byte & (~mask)) | ((value << gpioAddr.start) & mask)
            self.interface.write((self.addr, GPIOInterface.ioRegister+gpioAddr.bank), byte)
        else:
        		gpio.output(GPIOInterface.pins[gpioAddr.start], value)
            
        
class GPIOAddr(object):
    def __init__(self, control, bank, start, width=1):
        self.control = control  # the I/O chip (deprecated, use a separate instance of GPIOInterface per chip)
        self.bank = bank        # the 8 bit bank of I/O pins within the chip
        self.start = start      # the starting pin
        self.width = width      # the number of pins

    def __str__(self):
        return "(%2d, %2d, %2d, %2d)"%(self.control, self.bank, self.start, self.width)

