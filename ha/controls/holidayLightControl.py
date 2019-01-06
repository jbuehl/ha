holidayLightPatternDefault = "on"
holidayLightAnimationDefault = "solid"

import time
import threading
import random
from ha import *

def randomPattern(length=1, colors=3):
    pattern = [0]*length
    for i in range(length):
        pattern[i] = int(16777215 * random.random()) # random number between 0 and 256**3-1
    return pattern
    
# define a segment of a string of lights
class Segment(object):
    def __init__(self, name, start, length, pattern=None, animation=None):
        self.name = name
        self.start = start
        self.length = length
        if pattern:
            self.pattern = pattern
        else:
            self.pattern = [0]
        self.animation = animation
        debug("debugHolidayLights", "segment", name, start, length, self.pattern, self.animation)
        self.pixels = [0]*length

    # fill the segment with a pattern
    def fill(self, pattern=None):
        if not pattern:
            pattern = self.pattern
        debug("debugHolidayLights", "segment", self.name, "fill", pattern)
        for l in range(self.length):
            self.pixels[l] = pattern[l%len(pattern)]

    # display the segment
    def display(self, strip):
        for l in range(self.length):
            strip.write(self.start+l, self.pixels[l])

    # animate the segment
    def animate(self):
        if self.animation:
            self.animation.animate(self)
            
    # shift the pattern by the specified number of pixels
    def shift(self, n):
        debug("debugHolidayLights", "segment", self.name, "shift", n)
        if n > 0:   # shift right
            pixels = self.pixels[-n:]
            self.pixels = pixels+self.pixels[:-n]
        else:       # shift left
            pixels = self.pixels[:-n]
            self.pixels = self.pixels[-n:]+pixels

    # turn off random pixels based on a culling frequency between 0 and 1
    def decimate(self, factor):
        debug("debugHolidayLights", "segment", self.name, "decimate", factor)
        for p in range(len(self.pixels)):
            if random.random() < factor:
                self.pixels[p] = 0

    # dim the pattern by a specified factor
    def dim(self, factor):
        for p in range(len(self.pixels)):
            pixel = self.pixels[p]
            r = int(factor * ((pixel>>16)&0xff))
            g = int(factor * ((pixel>>8)&0xff))
            b = int(factor * (pixel&0xff))
            self.pixels[p] = (r<<16)+(g<<8)+b

# define an animation for a segment
class Animation(object):
    def __init__(self, name, rate):
        self.name = name
        self.rate = rate
        self.animationCount = 0
        
    # define an animation cycle
    def animate(self, segment):
        self.segment = segment
        if self.animationCount == 0:
            self.cycle()        
        self.animationCount += 1
        if self.animationCount == self.rate:
            self.animationCount = 0

class RandomColorAnimation(Animation):
    def __init__(self, name="randomcolor", rate=3):
        Animation.__init__(self, name, rate)
                                    
    def cycle(self):                                    
        self.segment.fill(randomPattern(len(self.segment.pixels)))

class CrawlAnimation(Animation):
    def __init__(self, name="crawl", rate=3, direction=1):
        Animation.__init__(self, name, rate)
        self.direction = direction
                                    
    def cycle(self):                                    
        self.segment.shift(self.direction)

class SparkleAnimation(Animation):
    def __init__(self, name="sparkle", rate=3, factor=.7):
        Animation.__init__(self, name, rate)
        self.factor = factor
                                    
    def cycle(self):                                    
        self.segment.fill()
        self.segment.decimate(self.factor)

class FlickerAnimation(Animation):
    def __init__(self, name="flicker", rate=1, factor=.7):
        Animation.__init__(self, name, rate)
        self.factor = factor
                                    
    def cycle(self):                                    
        if random.random() < self.factor:
            self.segment.fill()
        else:
            self.segment.fill([0])

class BlinkAnimation(Animation):
    def __init__(self, name="blink", rate=15):
        Animation.__init__(self, name, rate)
        self.state = True
                                    
    def cycle(self):                                    
        if self.state:
            self.segment.fill([off])
            self.state = False
        else:
            self.segment.fill()
            self.state = True

class FadeAnimation(Animation):
    def __init__(self, name="fade", rate=6):
        Animation.__init__(self, name, rate)
        self.fadeFactor = 10
        self.fadeIncr = -1

    def cycle(self):                                    
        self.segment.fill()
        self.segment.dim(float(self.fadeFactor)/10)
        self.fadeFactor += self.fadeIncr
        if (self.fadeFactor == 0) or (self.fadeFactor == 10):
            self.fadeIncr = -self.fadeIncr
     
class HolidayLightControl(Control):
    def __init__(self, name, interface, 
#                    patterns={}, animations=[], patternControl=None, animationControl=None, 
                    segments=None,
                    addr=None, group="", type="control", location=None, label="", event=None):
        Control.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, event=event)
        self.className = "Control"
#        self.patterns = patterns
#        self.animations = animations
#        self.patternControl = patternControl
        self.pattern = holidayLightPatternDefault
#        self.animationControl = animationControl
        self.animation = holidayLightAnimationDefault
        if segments:
            self.segments = segments
        else:
            self.segments = [Segment(self.interface, 0, self.interface.length)]
        # compute segment positions if not explicitly specified
        pos = 0
        for segment in self.segments:
            if segment.start == 0:
                segment.start = pos
            pos += segment.length
        self.running = False

    def getState(self):
        return self.running

    def setState(self, value):
        debug("debugHolidayLights", self.name, "setState", "value:", value)
        def runDisplay():
#            if self.patternControl:
#                self.setPattern(self.patternControl.getState())
#            if self.animationControl:
#                self.setAnimation(self.animationControl.getState())
            debug("debugHolidayLights", self.name, "runDisplay started", "pattern:", self.pattern, "animation:", self.animation)
            for segment in self.segments:
                segment.fill()
                segment.display(self.interface)
            self.interface.show()
            shift = 1
#            last = 0
            while self.running:
#                time.sleep(.1)
#                now = time.time()
#                debug("debugEnable", self.name, now-last)
#                last = now
                for segment in self.segments:
                    segment.animate()
                    segment.display(self.interface)
                self.interface.show()
            debug("debugHolidayLights", self.name, "runDisplay terminated")
            for segment in self.segments:
                segment.fill([off])
                segment.display(self.interface)
            self.interface.show()
        if value:
            displayThread = threading.Thread(target=runDisplay)
            self.running = True
            displayThread.start()
        else:
           self.running = False
                
#    def setPattern(self, value):
#        if value in self.patterns.keys():
#            self.pattern = value
#        else:
#            self.pattern = "off"
            
#    def setAnimation(self, value):
#        if value in self.animations:
#            self.animation = value
#        else:
#            self.animation = "solid"
    
