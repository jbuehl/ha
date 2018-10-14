
from neopixel import *
from ha import *
     
# color definitions
def color(r, g, b):
    return (r<<16)+(g<<8)+b
    
on = color(255,255,255)
off = color(0,0,0)

white = color(255,191,127)
pink = color(255,63,63)
red = color(255,0,0)
orange = color(255,63,0)
yellow = color(255,127,0)
green = color(0,255,0)
blue = color(0,0,127)
purple = color(63,0,63)
cyan = color(0,255,255)
magenta = color(255,0,63)
rust = color(63,7,0)

class NeopixelInterface(Interface):
    def __init__(self, name, interface, length=50, gpio=18, event=None):
        Interface.__init__(self, name, interface=interface, event=event)
        self.length = length
        self.gpio = gpio

    def start(self):
        self.strip = Adafruit_NeoPixel(self.length, self.gpio, 800000, 5, False)
        self.strip.begin()

    def read(self, addr):
        return None

    def write(self, addr, value):
        self.strip.setPixelColor(addr, value)

    def show(self):
        self.strip.show()
