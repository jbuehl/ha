from ha.HAClasses import *
import RPIO as gpio

gpioInterfaces = {}

def interruptCallback(pin, value):
    debug('debugGPIO', "interruptCallback", "pin:", pin, "value:", value)
    gpioInterfaces[pin].interrupt()

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

    interruptPins = [23, 24]
    
    # direct GPIO
    gpioPins = [12, 16, 18, 22, 15, 13, 11, 7]   # A/B
#            32, 36, 38, 40, 37, 35, 33, 31]     # B+
    
    def __init__(self, name, interface=None, event=None,
                                             addr=0x20, # I2C address of MCP23017
                                             bank=0,    # bank within MCP23017 A=0, B=1
                                             inOut=0x00,# I/O direction out=0, in=1
                                             config=[]):# additional configuration
        HAInterface.__init__(self, name, interface=interface, event=event)
        global gpioInterfaces
        gpioInterfaces[GPIOInterface.interruptPins[bank]] = self
        self.name = name
        if interface:
            self.addr = addr
            self.bank = bank
            self.inOut = inOut
            self.config = config
            self.state = 0x00
#            self.sensors = [None]*8
        else:
            self.interface = None
            self.bank = 0
    
    def start(self):
        gpio.setwarnings(False)
        if self.interface:
            # configure the MCP23017
            self.interface.write((self.addr, GPIOInterface.IODIR+self.bank), self.inOut)
            self.interface.write((self.addr, GPIOInterface.GPINTEN+self.bank), self.inOut)
            self.interface.write((self.addr, GPIOInterface.GPPU+self.bank), self.inOut)
            self.interface.write((self.addr, GPIOInterface.IOCON), 0x04)
            # additional configuration
            for config in self.config:
                debug('debugGPIO', self.name, "start", self.addr, config[0], config[1])
                self.interface.write((self.addr, config[0]), config[1])
            # get the current state
            self.readState()
            # set up the interrupt handling
            gpio.add_interrupt_callback(GPIOInterface.interruptPins[self.bank], interruptCallback, edge="falling", pull_up_down=gpio.PUD_UP)
            gpio.wait_for_interrupts(threaded=True)
        else:   # direct only supports output - FIXME
            gpio.setmode(gpio.BOARD)
            for pin in GPIOInterface.gpioPins:
                debug('debugGPIO', self.name, "setup", pin, gpio.OUT)
                gpio.setup(pin, gpio.OUT)
                debug('debugGPIO', self.name, "write", pin, 0)
                gpio.output(pin, 0)

    # interrupt handler
    def interrupt(self):
        intFlags = self.interface.read((self.addr, GPIOInterface.INTF+self.bank))
        debug('debugGPIO', self.name, "interrupt", "addr:", self.addr, "bank:", self.bank, "intFlags:", intFlags)
        self.readState()
        for i in range(8):
            if (intFlags >> i) & 0x01:
#                try:
                    sensor = self.sensorAddrs[i]
                    state = (self.state >> i) & 0x01
                    debug('debugGPIO', self.name, "notifying", sensor.name)
                    sensor.notify()
                    if sensor.interrupt:
                        debug('debugGPIO', self.name, "calling", sensor.name, state)
                        sensor.interrupt(sensor, state)
#                except:
#                    pass

    def read(self, addr):
        if self.interface:
            return (self.state >> addr) & 0x01
        else:
            return 0

    def readState(self):
        byte = self.interface.read((self.addr, GPIOInterface.GPIO+self.bank))
        debug('debugGPIO', self.name, "read", self.addr, GPIOInterface.GPIO+self.bank, byte)
        self.state = byte
    
    def write(self, addr, value):
        if self.interface:
            byte = self.state
            mask = 0x01<<addr
            byte = (byte & (~mask)) | ((value << addr) & mask)
            debug('debugGPIO', self.name, "write", self.addr, GPIOInterface.GPIO+self.bank, byte)
            self.interface.write((self.addr, GPIOInterface.GPIO+self.bank), byte)
            self.state = byte
        else:
            debug('debugGPIO', self.name, "write", addr, value)
            gpio.output(GPIOInterface.gpioPins[addr], value)
            
#    def addSensor(self, sensor):
#        self.sensors[sensor.addr.start] = sensor

#class GPIOAddr(object):
#    def __init__(self, control, bank, start, width=1):
#        self.control = control  # the I/O chip (deprecated, use a separate instance of GPIOInterface per chip)
#        self.bank = bank        # the 8 bit bank of I/O pins within the chip (A=0, B=1)
#        self.start = start      # the starting pin
#        self.width = width      # the number of pins

#    def __str__(self):
#        return "(%2d, %2d, %2d, %2d)"%(self.control, self.bank, self.start, self.width)

