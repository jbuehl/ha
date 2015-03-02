from ha.HAClasses import *
import RPIO as gpio

def intCallback(gpioId, value):
    if debugGPIO: log(gpioInterface.name, "interrupt", gpioId, value)
    gpioInterface.interrupt()

# Interface to GPIO either directly or via MCP23017 I2C I/O expander
class GPIOInterface(HAInterface):
    # MCP23017 I2C I/O expander
    IODIR = 0x00
    IPOL = 0x02
    GPINTEN = 0x04
    DEFVAL = 0x06
    INTCON = 0x08
    IOCON = 0x0a
    GPPU = 0x0c
    INTF = 0x0e
    INTCAP = 0x10
    GPIO = 0x12
    OLAT = 0x14

    # direct GPIO
    gpioPins = [12, 16, 18, 22, 15, 13, 11, 7]   # A/B
#            32, 36, 38, 40, 37, 35, 33, 31]     # B+
    
    def __init__(self, name, interface=None, addr=0x20, # I2C address of MCP23017
                                             bank=0,    # bank within MCP23017 A=0, B=1
                                             inOut=0x00,# I/O direction out=0, in=1
                                             config=[]):# additional configuration
        global gpioInterface
        gpioInterface = self
        self.name = name
        if interface:
            HAInterface.__init__(self, name, interface)
            self.addr = addr
            self.bank = bank
            self.inOut = inOut
            self.config = config
            self.state = 0x00
            self.sensors = [None]*8
        else:
            self.interface = None
    
    def start(self):
        gpio.setwarnings(False)
        gpio.setmode(gpio.BOARD)
        if self.interface:
            # configure the MCP23017
            self.interface.write((self.addr, GPIOInterface.IODIR+self.bank), self.inOut)
            self.interface.write((self.addr, GPIOInterface.GPINTEN+self.bank), self.inOut)
            self.interface.write((self.addr, GPIOInterface.GPPU+self.bank), self.inOut)
            self.interface.write((self.addr, GPIOInterface.IOCON), 0x04)
            # additional configuration
            for config in self.config:
                if debugGPIO: log(self.name, "start", self.addr, config[0], config[1])
                self.interface.write((self.addr, config[0]), config[1])
            # get the current state
            self.readState()
            # set up the interrupt handling
            intPin = GPIOInterface.gpioPins[self.bank]
            gpio.add_interrupt_callback(intPin, intCallback, edge="falling", pull_up_down=gpio.PUD_UP)
            gpio.wait_for_interrupts(threaded=True)
        else:   # direct only supports output - FIXME
            for pin in GPIOInterface.gpioPins:
	            gpio.setup(pin, gpio.OUT)
	            gpio.output(pin, 0)

    def read(self, gpioAddr):
        if self.interface:
            return (self.state >> gpioAddr.start) & ((1<<gpioAddr.width)-1)
        else:
            return 0

    def interrupt(self):
        intFlags = self.interface.read((self.addr, GPIOInterface.INTF+self.bank))
        if debugGPIO: log(self.name, "interrupt", self.addr, GPIOInterface.INTF+self.bank, intFlags)
        self.readState()
        for i in range(8):
            if (intFlags << i) & 0x01:
                try:
                    if debugGPIO: log(self.name, "calling", self.sensors[i].name, (self.state << i) & 0x01)
                    self.sensors[i].event.set()
                    if debugInterrupt: log(self.sensors[i].name, "event set")
                    self.sensors[i].interrupt(self.sensors[i], (self.state << i) & 0x01)
                except:
                    pass

    def readState(self):
        byte = self.interface.read((self.addr, GPIOInterface.GPIO+self.bank))
        if debugGPIO: log(self.name, "read", self.addr, GPIOInterface.GPIO+self.bank, byte)
        self.state = byte
    
    def write(self, gpioAddr, value):
        if self.interface:
            byte = self.state
            mask = ((1<<gpioAddr.width)-1)<<gpioAddr.start
            byte = (byte & (~mask)) | ((value << gpioAddr.start) & mask)
            if debugGPIO: log(self.name, "write", self.addr, GPIOInterface.GPIO+self.bank, byte)
            self.interface.write((self.addr, GPIOInterface.GPIO+self.bank), byte)
            self.state = byte
        else:
        		gpio.output(GPIOInterface.gpioPins[gpioAddr.start], value)
            
    def addSensor(self, sensor):
        self.sensors[sensor.addr.start] = sensor

class GPIOAddr(object):
    def __init__(self, control, bank, start, width=1):
        self.control = control  # the I/O chip (deprecated, use a separate instance of GPIOInterface per chip)
        self.bank = bank        # the 8 bit bank of I/O pins within the chip (A=0, B=1)
        self.start = start      # the starting pin
        self.width = width      # the number of pins

    def __str__(self):
        return "(%2d, %2d, %2d, %2d)"%(self.control, self.bank, self.start, self.width)

