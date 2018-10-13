
from neopixel import *
from ha import *
     
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
