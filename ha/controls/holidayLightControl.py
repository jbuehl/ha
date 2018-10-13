holidayLightPatternDefault = "on"
holidayLightAnimationDefault = "solid"

import time
import threading
from ha import *

# colors
def color(r, g, b):
    return 65536*r+256*g+b
    
on = [color(255,255,255)]
off = [color(0,0,0)]

white = [color(255,191,127)]
pink = [color(255,63,63)]
red = [color(255,0,0)]
orange = [color(255,63,0)]
yellow = [color(255,127,0)]
green = [color(0,255,0)]
blue = [color(0,0,127)]
purple = [color(63,0,63)]
cyan = [color(0,255,255)]
magenta = [color(255,0,63)]
rust = [color(63,7,0)]

# dictionary of patterns
patterns = {"on": on,
            "off": off,
            "white": white,
            "pink": pink,
            "red": red,
            "orange": orange,
            "yellow": yellow,
            "green": green,
            "blue": blue,
            "purple": purple,
            "cyan": cyan,
            "magenta": magenta,
            "rust": rust,
            "xmas": 3*red+3*green,
            "hanukkah": 3*blue+3*white,
            "halloween": 2*orange+rust+purple+rust,
            "valentines": white+pink+red+pink,
            "stpatricks": green,
            "mardigras": purple+yellow+green,
            "july": 3*red+3*white+3*blue,
            "cincodemayo": green+white+red,
            "easter": yellow+blue+green+cyan+magenta,
            "sweden": blue+yellow,
            "fall": red+orange+rust+orange,
            "pride": pink+red+orange+yellow+green+blue+purple,
            "holi": red+yellow+blue+green+orange+purple+pink+magenta,
            "mayday": red,
            "columbus": green+white+red,
            "mlk": white+red+yellow+rust,
            }

# animation types
animations = ["solid", "crawl", "sparkle", "flicker", "blink", "fade"]

def display(strip, length, pattern, repeat=1, shift=0):
    debug("debugHolidayLights", "display", "strip:", strip.name, "pattern:", str(pattern))
    p = shift
    while p < length+shift:
        for c in range(len(pattern)):
            for r in range(repeat):
                if p < length+shift:
                    strip.write(p%length, pattern[c])
                    p += 1
    strip.show()

     
class HolidayLightControl(Control):
    def __init__(self, name, interface, patternControl=None, animationControl=None, 
                    addr=None, group="", type="control", location=None, label="", event=None):
        Control.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, event=event)
        self.className = "Control"
        self.patternControl = patternControl
        self.pattern = holidayLightPatternDefault
        self.animationControl = animationControl
        self.animation = holidayLightAnimationDefault
        self.running = False

    def getState(self):
        return self.running

    def setState(self, value):
        debug("debugHolidayLights", self.name, "setState", "value:", value)
        def runDisplay():
            if self.patternControl:
                self.setPattern(self.patternControl.getState())
            if self.animationControl:
                self.setAnimation(self.animationControl.getState())
            debug("debugHolidayLights", self.name, "runDisplay started", "pattern:", self.pattern, "animation:", self.animation)
            display(self.interface, self.interface.length, patterns[self.pattern], 1)
            shift = 1
            while self.running:
                time.sleep(.1)
                if self.animation == "crawl":
                    display(self.interface, self.interface.length, patterns[self.pattern], 1, shift)
                    shift += 1
            debug("debugHolidayLights", self.name, "runDisplay terminated")
            display(self.interface, self.interface.length, patterns["off"])
        if value:
            displayThread = threading.Thread(target=runDisplay)
            self.running = True
            displayThread.start()
        else:
           self.running = False
                
    def setPattern(self, value):
        if value in patterns.keys():
            self.pattern = value
        else:
            self.pattern = "off"
            
    def setAnimation(self, value):
        if value in animations:
            self.animation = value
        else:
            self.animation = "solid"
    
