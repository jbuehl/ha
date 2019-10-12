
import RPi.GPIO as gpio
from ha import *

# all available GPIO pins
bcmPins = [4, 17, 18, 22, 23, 24, 25, 27] # A/B
# bcmPins = [4, 5, 6, 12, 13, 16, 17, 18, 22, 23, 24, 25, 26, 27] # B+

# initial interrupt callback routine that is called when an interrupt pin goes low
def interruptCallback(pin):
    debug('debugGPIO', "interruptCallback", "pin:", pin)
    try:
        sensor = self.sensorAddrs[pin]
        debug('debugGPIO', self.name, "notifying", sensor.name)
        sensor.notify()
        if sensor.interrupt:
            debug('debugGPIO', self.name, "calling", sensor.name, state)
            sensor.interrupt(sensor, state)
    except KeyError:
        debug('debugGPIO', self.name, "no sensor for interrupt on pin", pin)

# Interface to direct GPIO
class GPIOInterface(Interface):
    def __init__(self, name, interface=None, event=None,
                                             inOut=0x00,        # I/O direction out=0, in=1
                                             ):
        Interface.__init__(self, name, interface=interface, event=event)
        self.inOut = inOut

    def start(self):
        gpio.setwarnings(False)
        gpio.setmode(gpio.BCM)
        # set I/O direction of pins
        inOut = self.inOut
        for pin in bcmPins:
            if inOut & 0x01:    # input pin
                debug('debugGPIO', self.name, "setup", pin, gpio.IN)
                gpio.setup(pin, gpio.IN, pull_up_down=gpio.PUD_UP)
                gpio.add_event_detect(pin, gpio.FALLING, callback=interruptCallback)
            else:               # output pin
                debug('debugGPIO', self.name, "setup", pin, gpio.OUT)
                gpio.setup(pin, gpio.OUT)
                debug('debugGPIO', self.name, "write", pin, 0)
                gpio.output(pin, 0)
            inOut >>= 1

    def read(self, addr):
        value = gpio.input(addr)
        debug('debugGPIO', self.name, "read", "addr:", addr, "value:", value)
        return value

    def write(self, addr, value):
        debug('debugGPIO', self.name, "write", "addr:", addr, "value:", value)
        gpio.output(addr, value)
