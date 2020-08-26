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
    def __init__(self, start, length, pattern=None, animation=None):
        self.name = "segment"
        self.start = start
        self.length = length
        if pattern:
            self.pattern = pattern
        else:
            self.pattern = [0]
        self.animation = animation
        debug("debugHolidayLights", "segment", self.name, start, length, self.pattern, self.animation)
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

    # shift the pattern by the specified number of pixels in the specified direction
    def shift(self, n, direction):
        debug("debugHolidayLights", "segment", self.name, "shift", n, direction)
        if direction > 0:   # shift out
            pixels = self.pixels[-n:]
            self.pixels = pixels+self.pixels[:-n]
        else:       # shift in
            pixels = self.pixels[n:]
            self.pixels = pixels+self.pixels[:n]

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
        self.segment.shift(1, self.direction)

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

# class AliasControl(Control):
#     def __init__(self, name, interface, resources, control,
#                     addr=None, group="", type="control", location=None, label="", event=None):
#         Control.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, event=event)
#         self.className = "Control"
#         self.resources = resources
#         self.control = control
#
#     def getState(self, missing=None):
#         return self.resources.getRes(self.control.getState()).getState()
#
#     def setState(self, value):
#         return self.resources.getRes(self.control.getState()).setState(value)
#
class HolidayLightControl(Control):
    def __init__(self, name, interface, patterns, patternControl,
                 **kwargs):
        Control.__init__(self, name, interface, **kwargs)
        self.className = "Control"
        self.patterns = patterns                # list of patterns
        self.patternControl = patternControl    # a Control whose state specifies which pattern is active
        self.pattern = ""                       # name of the active pattern
        self.running = False

    # set the pattern based on the pattern control
    def setPattern(self):
        #  do nothing if the pattern has not changed
        newPattern = self.patternControl.getState()
        if newPattern != self.pattern:
            self.pattern = newPattern
            debug("debugHolidayLights", self.name, "setPattern", "pattern:", self.pattern)
            self.segments = self.patterns[self.pattern]
            # compute segment positions if not explicitly specified
            pos = 0
            for segment in self.segments:
                if segment.start == 0:
                    segment.start = pos
                debug("debugHolidayLights", self.name, "segment", segment.start, segment.length, segment.pattern)
                pos += segment.length
            # if it is running, fill the segments
            if self.running:
                for segment in self.segments:
                    segment.fill()
                    segment.display(self.interface)
                self.interface.show()

    def getState(self, missing=None):
        return self.running

    def setState(self, value):
        debug("debugHolidayLights", self.name, "setState", "value:", value)
        def runDisplay():
            debug("debugHolidayLights", self.name, "runDisplay started")
            self.setPattern()
            for segment in self.segments:
                segment.fill()
                segment.display(self.interface)
            self.interface.show()
            # run the animations
            while self.running:
                self.setPattern()
                for segment in self.segments:
                    segment.animate()
                    segment.display(self.interface)
                self.interface.show()
            # turn all lights off
            for segment in self.segments:
                segment.fill([off])
                segment.display(self.interface)
            self.interface.show()
            debug("debugHolidayLights", self.name, "runDisplay terminated")
        if value:
            displayThread = LogThread(target=runDisplay)
            self.running = True
            displayThread.start()
        else:
           self.running = False
