# todo
#
# RGB pixels
# HTML attribute names
# exit button without release
# cancel button press
# truncate at display boundaries
# truncate at element boundaries
# kerning
# text string bbox size
# frame buffer python module

updateInterval = 1

fbLib = "/root/ha/ha/ui/fb/libfb.so"

from ctypes import cdll
import freetype
import evdev
import time
import threading
import copy
import webcolors
import png
import os
import struct
from ha import *
from ha.ui.webViews import *

# select a text color based on temperature value
def tempColor(tempString):
    try:
        temp = int(tempString.split(" ")[0])
    except:
        temp = 0
    if temp > 120:                 # magenta
        red = 252; green = 0; blue = 252
    elif temp > 102:               # red
        red = 252; green = 0; blue = (temp-102)*14
    elif temp > 84:                # yellow
        red = 252; green = (102-temp)*14; blue = 0
    elif temp > 66:                # green
        red = (temp-66)*14; green = 252; blue = 0
    elif temp > 48:                # cyan
        red = 0; green = 252; blue = (66-temp)*14
    elif temp > 30:                # blue
        red = 0; green = (temp-30)*14; blue = 252
    elif temp > 0:
        red = 0; green = 0; blue = 252
    else:
        red = 112; green = 128; blue = 144
    return 'rgb('+str(red)+','+str(green)+','+str(blue)+')'

# convert PNG to frame buffer
def png2fb(pngImage):
    fbPixMap = b""
    pngArrayList = list(pngImage[2])
    pngDict = pngImage[3]
    planes = pngDict["planes"]
    for row in pngArrayList:
        rowList = list(row)
        try:
            for pix in range(0, len(rowList), planes):
                # fbPixMap += chr(rowList[pix+2]) + chr(rowList[pix+1]) + chr(rowList[pix])
                fbPixMap += bytes([rowList[pix+2], rowList[pix+1], rowList[pix]])
                if planes == 4:
                    fbPixMap += bytes([rowList[pix+3]])
                elif planes == 3:
                    fbPixMap += b"\xff"
        except IndexError:
            pass
    return fbPixMap

# read an image file
def readImage(imageFileName):
    debug("debugImage", "readImage()", imageFileName)
    (imageName, ext) = imageFileName.split(".")
    try:
        # attempt to read the .fb file
        with open(imageName+".fb", "rb") as imageFile:
            fbData = imageFile.read()
            (width, height) = struct.unpack("!hh", fbData[0:4])
            return (width, height, fbData[4:])
    except IOError:
        # read the .png file
        pngReader = png.Reader(imageFileName)
        pngImage = pngReader.read()
        width = pngImage[0]
        height = pngImage[1]
        image = png2fb(pngImage)
        # save the fb image for next time
        with open(imageName+".fb", "wb") as imageFile:
            imageFile.write(bytes(struct.pack("!hh", width, height))+image)
        return (width, height, image)

# convert RGB pixmp to frame buffer
def rgb2fb(rgbPixMap):
    fbPixMap = b""
    for pix in range(0, len(rgbPixMap), 3):
        fbPixMap += bytes([rgbPixMap[pix+2], rgbPixMap[pix+1], rgbPixMap[pix]]) + b"\xff"
    return fbPixMap

# return frame buffer value for named color
def color(colorName):
    return rgb2fb(webcolors.name_to_rgb(colorName))

# return printable string of attribute values
def printAttrs(style):
    return ["%s: %s"%(attr, style.__dict__[attr]) for attr in ["name", "xPos", "yPos", "width", "height", "margin"]]

# a Display manages the device upon which the UI is presented
class Display(object):
    def __init__(self, name, displayDevice="/dev/fb0", inputDevice="/dev/input/event0", views=None):
        self.name = name
        self.initDisplay(displayDevice)
        self.initInput(inputDevice)
        self.views = views

    def initDisplay(self, displayDeviceName):
        self.FrameBuffer = cdll.LoadLibrary(fbLib)
        self.frameBuffer = self.FrameBuffer.init(bytes(displayDeviceName, "utf-8"))
        self.xRes = self.FrameBuffer.getXres(self.frameBuffer)
        self.yRes = self.FrameBuffer.getYres(self.frameBuffer)
        self.bitsPerPix = self.FrameBuffer.getBitsPerPix(self.frameBuffer)
        debug("debugDisplay", "xRes", self.xRes)
        debug("debugDisplay", "yRes", self.yRes)
        debug("debugDisplay", "bitsPerPix", self.bitsPerPix)
        self.lock = threading.Lock()
        self.buttons = []
        self.elements = []

    def initInput(self, inputDeviceName):
        self.inputDevice = evdev.InputDevice(inputDeviceName)
        self.curXpos = 0
        self.curYpos = 0

    def start(self, block=False):
        # thread to handle Button inputs
        def InputThread():
            for event in self.inputDevice.read_loop():
                debug("debugButton", event.__str__(), evdev.util.categorize(event))
                if event.type == 1:         # BTN_TOUCH
                    if event.code == 330:
                        element = self.findButton(self.curXpos, self.curYpos)
                        if element:
                            if event.value == 0:    # up
                                element.releaseThread = threading.Thread(target=element.release)
                                element.releaseThread.start()
                            elif event.value == 1:   # down
                                element.pressThread = threading.Thread(target=element.press)
                                element.pressThread.start()
                elif event.type == 3:
                    if (event.code == 0) or (event.code == 53):     # ABS_X or ABS_MT_POSITION_X
                        self.curXpos = event.value
                    elif (event.code == 1) or (event.code == 54):   # ABS_Y or ABS_MT_POSITION_Y
                        self.curYpos = event.value
        inputThread = threading.Thread(target=InputThread)
        inputThread.start()

        # thread to periodically update Element values
        def UpdateThread():
            while True:
                for element in self.elements:
                    debug("debugUpdate", self.name, "Display.update()", element.name, element.visible)
                    if (element.resource) and (element.visible):
                        element.render()
                time.sleep(updateInterval)
        updateThread = threading.Thread(target=UpdateThread)
        updateThread.start()

        if block:
            while True:
                time.sleep(1)

    def addElement(self, element):
        debug("debugUpdate", self.name, "Display.addElement()", element.name)
        self.elements.append((element))

    def findButton(self, xPos, yPos):
        debug("debugButton", self.name, xPos, yPos)
        for element in self.elements:
            debug("debugButton", element.name, element.__class__.__name__, element.xPos, element.yPos)
            if element.__class__.__name__ == "Button":
                if (xPos >= element.xPos) and (xPos <= element.xPos+element.width) and \
                   (yPos >= element.yPos) and (yPos <= element.yPos+element.height):
                    return element
        return None

    # clear the display
    def clear(self, color):
        debug("debugDisplay", "clear", color)
        with self.lock:
            self.FrameBuffer.fill(self.frameBuffer, color)

    # fill an area of the display with a solid color
    def fill(self, xPos, yPos, width, height, color):
        debug("debugDisplay", "fill", xPos, yPos, width, height, color)
        with self.lock:
            self.FrameBuffer.setPixMap(self.frameBuffer, xPos, yPos, width, height, color*width*height)

    # render a pixmap on the display
    def renderPixMap(self, xPos, yPos, width, height, pixMap):
        debug("debugDisplay", "renderPixMap", xPos, yPos, width, height)
        with self.lock:
            self.FrameBuffer.setPixMap(self.frameBuffer, xPos, yPos, width, height, pixMap)

    # render text on the display
    def renderChars(self, face, fontSize, chars, xPos, yPos, xOffset, yOffset, fgColor, bgColor, width, height, just=0):
        debug("debugDisplay", "renderChars", face, fontSize, chars, xPos, yPos, xOffset, yOffset, fgColor, bgColor, width, height, just)
        with self.lock:
            y = yOffset
            face.set_pixel_sizes(0, fontSize)
            bgMap = self.FrameBuffer.getMap(width*height*self.bitsPerPix, bgColor)
            if just == 0:   # left justified
                x = xOffset
                for char in chars:
                    face.load_char(char)
                    bitmap = face.glyph.bitmap
                    metrics = face.glyph.metrics
                    if int(x+metrics.horiAdvance/64) > width:   # truncate if too big
                        break
                    self.FrameBuffer.setGrayMap(self.frameBuffer, x, int(y-metrics.horiBearingY/64), bitmap.width, bitmap.rows,
                                        bytes(bitmap.buffer), fgColor, bgColor,
                                        bgMap, width, height)
                    x += int(metrics.horiAdvance/64)
            else:           # right justified
                x = xOffset + width
                for char in reversed(chars):
                    face.load_char(char)
                    bitmap = face.glyph.bitmap
                    metrics = face.glyph.metrics
                    x -= int(metrics.horiAdvance/64)
                    if x < 0: # truncate if too big
                        break
                    self.FrameBuffer.setGrayMap(self.frameBuffer, x, int(y-metrics.horiBearingY/64), bitmap.width, bitmap.rows,
                                        bytes(bitmap.buffer), fgColor, bgColor,
                                        bgMap, width, height)
            self.FrameBuffer.setPixMap(self.frameBuffer, xPos, yPos, width, height, bgMap)
            self.FrameBuffer.freeMap(bgMap)

# a Style contains the attributes that define the presentation of an Element
class Style(object):
    def __init__(self, name, style=None, **args):
        # set defaults
        self.width = 0
        self.height = 0
        self.padding = 0
        self.border = 0
        self.margin = 0
        self.bgColor = color("white")
        self.fgColor = color("black")
        self.just = 0
        # inherit parent style attributes
        if style:
            self.__dict__.update(style.__dict__)
        # override with specified attributes
        self.name = name
        self.__dict__.update(args)

# an Element is the basic object that is rendered on a Display
class Element(object):
    def __init__(self, name, style=None, container=None, **args):
        self.name = name
        if style:
            self.style = style
        else:
            self.style = Style("style")
        self.container = container
        self.display = None
        self.resource = None
        self.visible = True
        # set defaults
        self.xPos = 0
        self.yPos = 0
        # inherit style attributes
        self.__dict__.update(self.style.__dict__)
        # override with specified attributes
        self.name = name
        self.__dict__.update(args)

    def getSizePos(self):
        return (self.xPos, self.yPos, self.width, self.height)

    # calculate the absolute position of the element on the display
    def arrange(self, display, xPos=0, yPos=0):
        self.display = display
        self.display.addElement(self)
        self.xPos = xPos
        self.yPos = yPos

    def setVisible(self, visible):
        self.visible = visible
        debug("debugVisible", self.name, "Element.setVisible()", visible)

    def render(self):
        debug("debugDisplay", self.name, "Element.render()", printAttrs(self))

    def fill(self, color):
        if self.display:
            self.display.fill(self.xPos, self.yPos, self.width, self.height, color)

    def clear(self):
        if self.display:
            self.display.fill(self.xPos, self.yPos, self.width, self.height, self.bgColor)

# a Container is an Element that contains one or more Elements
class Container(Element):
    def __init__(self, name, style=None, elementList=[], **args):
        Element.__init__(self, name, style, **args)
        self.elementList = elementList
        for element in self.elementList:
            element.container = self

    def setVisible(self, visible):
        self.visible = visible
        debug("debugVisible", self.name, "Container.setVisible()", visible)
        for element in self.elementList:
            element.setVisible(visible)

    def render(self):
        debug("debugDisplay", self.name, "Container.render()", printAttrs(self))
        self.clear()
        for element in self.elementList:
            element.render()

# a Div is a Container that stacks its Elements vertically
class Div(Container):
    def __init__(self, name, style=None, elementList=[], **args):
        Container.__init__(self, name, style, elementList, **args)

    def arrange(self, display, xPos=0, yPos=0):
        Element.arrange(self, display, xPos, yPos)
        height = 2*self.margin
        for element in self.elementList:
            # arrange the content
            element.arrange(self.display, self.xPos + self.margin, self.yPos + self.margin + height)
            height += element.height
            self.width = max(self.width, element.width)
        # set the size of this element
        self.width += 2*self.margin
        self.height = max(self.height, height)
        debug("debugArrange", self.name, "arrange()", printAttrs(self))

# a Span is a Container that stacks its Elements horizontally
class Span(Container):
    def __init__(self, name, style=None, elementList=[], **args):
        Container.__init__(self, name, style, elementList, **args)

    def arrange(self, display, xPos=0, yPos=0):
        Element.arrange(self, display, xPos, yPos)
        width = 2*self.margin
        for element in self.elementList:
            # arrange the content
            element.arrange(self.display, self.xPos + self.margin + width, self.yPos + self.margin)
            width += element.width
            self.height = max(self.height, element.height)
        # set the size of this element
        self.height += 2*self.margin
        self.width = max(self.width, width)
        debug("debugArrange", self.name, "arrange()", printAttrs(self))

# an Overlay is a Container that overlays its Elements
class Overlay(Container):
    def __init__(self, name, style=None, elementList=[], frontElement=0, **args):
        Container.__init__(self, name, style, elementList, **args)
        self.frontElement = frontElement

    def arrange(self, display, xPos=0, yPos=0):
        Element.arrange(self, display, xPos, yPos)
        self.width = 0
        self.height = 0
        for elementIndex in range(len(self.elementList)):
            element = self.elementList[elementIndex]
            # set the visibility of the elements
            element.setVisible(elementIndex == self.frontElement)
            # arrange the content
            element.arrange(self.display, self.xPos + self.margin, self.yPos + self.margin)
            self.width = max(self.width, element.width)
            self.height = max(self.height, element.height)
        # set the size of this element
        self.width += 2*self.margin
        self.height += 2*self.margin
        debug("debugArrange", self.name, "arrange()", printAttrs(self))

    def setFront(self, frontElement):
        if frontElement in range(len(self.elementList)):
            self.elementList[self.frontElement].setVisible(False)
            self.frontElement = frontElement
            self.elementList[self.frontElement].setVisible(True)
        else:
            self.frontElement = 0

    def render(self):
        debug("debugDisplay", self.name, "Container.render()", printAttrs(self))
        self.clear()
        # only render the element designated as being in front
        self.elementList[self.frontElement].render()

# an Element containing text
# https://github.com/rougier/freetype-py/
# http://freetype-py.readthedocs.io/en/latest/glyph_slot.html
# https://www.freetype.org/freetype2/docs/tutorial/step2.html#section-4
class Text(Element):
    def __init__(self, name, style=None, value="", resource=None, **args):
        Element.__init__(self, name, style, **args)
        self.value = value
        self.resource = resource

    def setValue(self, value):
        self.value = value

    def render(self, style=None, value=None):
        if self.resource:
            resState = self.display.views.getViewState(self.resource)
            self.setValue(resState)
            if self.resource.type in tempTypes:
                self.fgColor = rgb2fb(eval(tempColor(resState).lstrip("rgb")))
            elif self.resource.type == "diagCode":
                if resState[0] != "0":
                    self.setValue(resState[0:8])
                    self.fgColor = color("OrangeRed")
            elif self.resource.type == "nSats":
                if (resState == "--") or (int(resState) < 4):
                    self.fgColor = color("Red")
                else:
                    self.fgColor = color("LightYellow")
        renderStyle = copy.copy(self)
        if style:
            renderStyle.__dict__.update(style.__dict__)
        debug("debugDisplay", self.name, "Text.render()", printAttrs(renderStyle))
        if not value:
            value = self.value
        self.display.renderChars(renderStyle.face, renderStyle.fontSize, value,
            self.xPos+self.margin, self.yPos+self.margin,
            renderStyle.margin+renderStyle.padding, 2*(renderStyle.height-2*renderStyle.margin)/3,
            renderStyle.fgColor, renderStyle.bgColor,
            renderStyle.width-2*renderStyle.margin, renderStyle.height-2*renderStyle.margin,
            renderStyle.just)
        del(renderStyle)

# an Element containing a static image
class Image(Element):
    def __init__(self, name, style=None, imageFile=None, value="", resource=None, **args):
        Element.__init__(self, name, style, **args)
        debug("debugImage", self.name, "Image()", self.name)
        self.imageFile = imageFile
        self.value = value
        self.resource = resource
        if self.imageFile:
            (self.width, self.height, self.image) = readImage(self.imageFile)
            self.width += 2*self.style.margin
            self.height += 2*self.style.margin
        else:
            self.image = None

    def setValue(self, value):
        self.value = value

    def setImage(self, image):
        self.image = image

    def render(self, style=None, image=None):
        renderStyle = copy.copy(self)
        if style:
            renderStyle.__dict__.update(style.__dict__)
        debug("debugDisplay", self.name, "Image.render()", printAttrs(renderStyle))
        if self.resource:
            self.image = self.resource.getState()
        elif image == None:
            if self.imageFile:
                (self.width, self.height, self.image) = readImage(self.imageFile)
        self.display.renderPixMap(self.xPos+self.margin, self.yPos+self.margin,
                                  self.width-2*self.margin, self.height-2*self.margin,
                                  self.image)
        del(renderStyle)

# display a compass image based on the value of a heading
class CompassImage(Element):
    def __init__(self, name, style, hdgSensor=None, compassImageDir=None, resource=None, **args):
        Element.__init__(self, name, style, **args)
        self.hdgSensor = hdgSensor
        self.compassImgs = []
        compassImgFileNames = os.listdir(compassImageDir)
        compassImgFileNames.sort()
        for compassImgFileName in compassImgFileNames:
            (self.width, self.height, image) = readImage(compassImageDir+compassImgFileName)
            self.width += 2*self.style.margin
            self.height += 2*self.style.margin
            self.compassImgs.append(image)
        self.resource = resource

    def render(self):
        incr = 360./len(self.compassImgs)
        idx = int((self.hdgSensor.getState()+incr/2)%360/incr)
        debug("debugCompass", "CompassImage.render()", idx)
        self.display.renderPixMap(self.xPos+self.margin, self.yPos+self.margin,
                                  self.width-2*self.margin, self.height-2*self.margin,
                                  self.compassImgs[idx])

# a Button is an Overlay that receives input
class Button(Overlay):
    def __init__(self, name, style=None, elementList=[], frontElement=0, onPress=None, onRelease=None, **args):
        Overlay.__init__(self, name, style, elementList, frontElement, **args)
        self.elementList = elementList
        self.onPress = onPress
        self.onRelease = onRelease
        self.resource = None

    def press(self):
        if self.onPress:
            self.onPress(self)

    def release(self):
        if self.onRelease:
            self.onRelease(self)
