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

updateInterval = 10

fbLib = "/root/ha/ha/ui/fb/libfb.so"

from ctypes import cdll
import freetype
import evdev
import time
import threading
import copy
import webcolors
import png
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
    fbPixMap = ""
    pngArrayList = list(pngImage[2])
    pngDict = pngImage[3]
    planes = pngDict["planes"]
    for row in pngArrayList:
        rowList = list(row)
        try:
            for pix in range(0, len(rowList), planes):
                fbPixMap += chr(rowList[pix+2]) + chr(rowList[pix+1]) + chr(rowList[pix])
                if planes == 4:
                    fbPixMap += chr(rowList[pix+3])
                elif planes == 3:
                    fbPixMap += "\xff"
        except IndexError:
            pass
    return fbPixMap

# convert RGB pixmp to frame buffer
def rgb2fb(rgbPixMap):
    fbPixMap = ""
    for pix in range(0, len(rgbPixMap), 3):
        fbPixMap += chr(rgbPixMap[pix+2]) + chr(rgbPixMap[pix+1]) + chr(rgbPixMap[pix]) + "\xff"
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
        self.frameBuffer = self.FrameBuffer.init(displayDeviceName)
        self.xRes = self.FrameBuffer.getXres(self.frameBuffer)
        self.yRes = self.FrameBuffer.getYres(self.frameBuffer)
        self.bitsPerPix = self.FrameBuffer.getBitsPerPix(self.frameBuffer)
        self.lock = threading.Lock()
        self.buttons = []
        self.resourceElements = []

    def initInput(self, inputDeviceName):
        self.inputDevice = evdev.InputDevice(inputDeviceName)
        self.curXpos = 0
        self.curYpos = 0

    def start(self, block=False):
        # thread to handle Button inputs
        def InputThread():
            for event in self.inputDevice.read_loop():
#                print event.__str__()
#                print evdev.util.categorize(event)
                if event.type == 1:         # BTN_TOUCH
                    if event.code == 330:     
                        resourceElement = self.findButton(self.curXpos, self.curYpos)
                        if event.value == 0:    # up
                            if resourceElement:
                                resourceElement[1].release(self, resourceElement[0])
                        elif event.value == 1:   # down
                            if resourceElement:
                                resourceElement[1].press(self, resourceElement[0])
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
                for element in self.resourceElements:
                    debug("debugUpdate", self.name, "Display.update()", element.name)
                    element.render(self)
                time.sleep(updateInterval)
        updateThread = threading.Thread(target=UpdateThread)
        updateThread.start()
        
        if block:
            while True:
                time.sleep(1)

    def addElement(self, element):
        debug("debugUpdate", self.name, "Display.addElement()", element.name)
        self.resourceElements.append((element))

    def findButton(self, xPos, yPos):
        for resourceElement in self.resourceElements:
            if resourceElement[1].__class__.__name__ == "Button":
                button = resourceElement[1]
                if (xPos >= button.xPos) and (xPos <= button.xPos+button.width) and \
                   (yPos >= button.yPos) and (yPos <= button.yPos+button.height):
                    return resourceElement
        return None

    # clear the display
    def clear(self, color):
        with self.lock:
            self.FrameBuffer.fill(self.frameBuffer, color)

    # fill an area of the display with a solid color
    def fill(self, xPos, yPos, width, height, color):
        with self.lock:
            self.FrameBuffer.setPixMap(self.frameBuffer, xPos, yPos, width, height, color*width*height)

    # render a pixmap on the display
    def renderPixMap(self, xPos, yPos, width, height, pixMap):
        with self.lock:
            self.FrameBuffer.setPixMap(self.frameBuffer, xPos, yPos, width, height, pixMap)

    # render text on the display
    def renderChars(self, face, fontSize, chars, xPos, yPos, xOffset, yOffset, fgColor, bgColor, width, height):
        with self.lock:
            x = xOffset
            y = yOffset
            face.set_pixel_sizes(0, fontSize)
            bgMap = self.FrameBuffer.getMap(width*height*self.bitsPerPix, bgColor)
            for char in chars:
                face.load_char(char)
                bitmap = face.glyph.bitmap
                metrics = face.glyph.metrics
                self.FrameBuffer.setGrayMap(self.frameBuffer, x, y-metrics.horiBearingY/64, bitmap.width, bitmap.rows, 
                                    "".join(chr(c) for c in bitmap.buffer), fgColor, bgColor, 
                                    bgMap, width, height)
                x += metrics.horiAdvance/64
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
        # inherit parent style attributes
        if style:
            self.__dict__.update(style.__dict__)
        # override with specified attributes
        self.name = name
        self.__dict__.update(args)

# an Element is the basic object that is rendered on a Display        
class Element(object):
    def __init__(self, name, style=None, **args):
        self.name = name
        if style:
            self.style = style
        else:
            self.style = Style("style")
        # set defaults
        self.xPos = 0
        self.yPos = 0
        # inherit style attributes
        self.__dict__.update(self.style.__dict__)
        # override with specified attributes
        self.name = name
        self.__dict__.update(args)

    def setPos(self, xPos, yPos):
        self.xPos = xPos
        self.yPos = yPos

    def getSizePos(self):
        return (self.xPos, self.yPos, self.width, self.height)

    def render(self, display, style=None):
        debug("debugDisplay", self.name, "Element.render()", printAttrs(self))
        if not style:
            style = self.style
        display.renderPixMap(self.xPos+self.margin, self.yPos+self.margin, 
                                  self.width-2*self.margin, self.height-2*self.margin, 
                                  self.bgColor*(self.width-2*self.margin)*(self.height-2*self.margin))

    def fill(self, display, color):
        display.fill(self.xPos, self.yPos, self.width, self.height, color)
        
    def clear(self, display):
        display.fill(self.xPos, self.yPos, self.width, self.height, self.bgColor)
        
    def arrange(self):
        debug("debugArrange", self.name, "arrange()", printAttrs(self))

# a Container is an Element that contains one or more Elements                
class Container(Element):
    def __init__(self, name, style=None, itemList=[], **args):
        Element.__init__(self, name, style, **args)
        self.itemList = itemList
        
    def render(self, display):
        debug("debugDisplay", self.name, "Container.render()", printAttrs(self))
        display.fill(self.xPos, self.yPos, self.width, self.height, self.bgColor)
        for item in self.itemList:
            item.render(display)

# a Div is a Container that stacks its Elements vertically      
class Div(Container):
    def __init__(self, name, style=None, itemList=[], **args):
        Container.__init__(self, name, style, itemList, **args)

    def arrange(self):
        height = 2*self.margin
        for item in self.itemList:
            # set the position of the content
            item.xPos = self.xPos + self.margin
            item.yPos = self.yPos + self.margin + height
            # compute the size of the content
            item.arrange()
            height += item.height
            self.width = max(self.width, item.width)
        # set the size of this element
        self.width += 2*self.margin
        self.height = max(self.height, height)
        debug("debugArrange", self.name, "arrange()", printAttrs(self))

# a Span is a Container that stacks its Elements horizontally      
class Span(Container):
    def __init__(self, name, style=None, itemList=[], **args):
        Container.__init__(self, name, style, itemList, **args)

    def arrange(self):
        width = 2*self.margin
        for item in self.itemList:
            # set the position of the content
            item.yPos = self.yPos + self.margin
            item.xPos = self.xPos + self.margin + width
            # compute the size of the content
            item.arrange()
            width += item.width
            self.height = max(self.height, item.height)
        # set the size of this element
        self.height += 2*self.margin
        self.width = max(self.width, width)
        debug("debugArrange", self.name, "arrange()", printAttrs(self))

# an Element containing text
# https://github.com/rougier/freetype-py/
# http://freetype-py.readthedocs.io/en/latest/glyph_slot.html
# https://www.freetype.org/freetype2/docs/tutorial/step2.html#section-4
class Text(Element):
    def __init__(self, name, style=None, value="", display=None, resource=None, **args):
        Element.__init__(self, name, style, **args)
        self.value = value
        self.display = display
        self.resource = resource
        if display and resource:
            display.addElement(self)
        
    def setValue(self, value):
        self.value = value

    def render(self, display, style=None, value=None):
        if self.resource:
            resState = display.views.getViewState(self.resource)
            self.setValue(resState)
            if self.resource.type in tempTypes:
                self.fgColor = rgb2fb(eval(tempColor(resState).lstrip("rgb")))
            elif self.resource.type == "diagCode":
                if resState[0] != "0":
                    self.setValue(resState[0:8])
                    self.fgColor = color("OrangeRed")
        renderStyle = copy.copy(self)
        if style:
            renderStyle.__dict__.update(style.__dict__)
        debug("debugDisplay", self.name, "Text.render()", printAttrs(renderStyle))
        if not value:
            value = self.value
        display.renderChars(renderStyle.face, renderStyle.fontSize, value, 
            self.xPos+self.margin, self.yPos+self.margin, 
            renderStyle.margin+renderStyle.padding, 2*(renderStyle.height-2*renderStyle.margin)/3, 
            renderStyle.fgColor, renderStyle.bgColor,
            renderStyle.width-2*renderStyle.margin, renderStyle.height-2*renderStyle.margin)
        del(renderStyle)

# an Element containing a static image        
class Image(Element):
    def __init__(self, name, style=None, imageFile=None, value="", display=None, resource=None, **args):
        Element.__init__(self, name, style, **args)
        debug("debugImage", self.name, "Image()", self.name, display.name, resource.name)
        self.imageFile = imageFile
        self.value = value
        self.display = display
        self.resource = resource
        if display and resource:
            display.addElement(self)
        if self.imageFile:
            self.readImage()
        else:
            self.image = None
        
    def readImage(self):
        debug("debugImage", self.name, "Image.readImage()", self.imageFile)
        pngReader = png.Reader(self.imageFile)
        pngImage = pngReader.read()
        self.width = pngImage[0] + 2*self.style.margin
        self.height = pngImage[1] + 2*self.style.margin
        self.image = png2fb(pngImage)
           
    def setValue(self, value):
        self.value = value

    def setImage(self, image):
        self.image = image

    def render(self, display, style=None, image=None):
        renderStyle = copy.copy(self)
        if style:
            renderStyle.__dict__.update(style.__dict__)
        debug("debugDisplay", self.name, "Image.render()", printAttrs(renderStyle))
        if self.resource:
            self.image = self.resource.getState()
        elif image == None:
            if self.imageFile:
                self.readImage()
        display.renderPixMap(self.xPos+self.margin, self.yPos+self.margin, 
                                  self.width-2*self.margin, self.height-2*self.margin, 
                                  self.image)
        del(renderStyle)

# display a compass image based on the value of a heading
class CompassImage(Element):
    def __init__(self, name, style, hdgSensor=None, compassImgFileNames=None, display=None, resource=None, **args):
        Element.__init__(self, name, style, **args)
        self.hdgSensor = hdgSensor
        self.compassImgs = []
        for compassImgFileName in compassImgFileNames:
            debug("debugCompass", "reading", compassImgFileName)
            with open(compassImgFileName) as compassImgFile:
                pngReader = png.Reader(compassImgFileName)
                pngImage = pngReader.read()
                self.width = pngImage[0] + 2*self.style.margin
                self.height = pngImage[1] + 2*self.style.margin
                self.compassImgs.append(png2fb(pngImage))
        self.display = display
        self.resource = resource
        if display and resource:
            display.addElement(self)

    def render(self, display):
        idx = int((self.hdgSensor.getState()+11.25)%360/22.5)
        debug("debugCompass", "CompassImage.render()", idx)
        display.renderPixMap(self.xPos+self.margin, self.yPos+self.margin, 
                                  self.width-2*self.margin, self.height-2*self.margin, 
                                  self.compassImgs[idx])
            
# a Button is a Container that receives input        
class Button(Container):
    def __init__(self, name, style=None, content=None, onPress=None, onRelease=None, altContent=None, **args):
        Container.__init__(self, name, style, [content, altContent], **args)
        self.content = content
        self.onPress = onPress
        self.onRelease = onRelease
        self.altContent = altContent

    def arrange(self):
        # set the position of the content
        self.content.xPos = self.xPos + self.margin
        self.content.yPos = self.yPos + self.margin
        self.content.arrange()
        if self.altContent:
            self.altContent.xPos = self.xPos + self.margin
            self.altContent.yPos = self.yPos + self.margin
            self.altContent.arrange()
        # set the size of this element
        if self.altContent:
            self.width = max(self.content.width, self.altContent.width) + 2*self.margin
            self.height = max(self.content.height, self.altContent.height) + 2*self.margin
        else:
            self.width = self.content.width + 2*self.margin
            self.height = self.content.height + 2*self.margin
        debug("debugArrange", self.name, "arrange()", printAttrs(self))
        
    def render(self, display):
        debug("debugDisplay", self.name, "Button.render()", printAttrs(self))
        self.clear(display)
        self.content.render(display)

    def press(self, display, resource):
        if self.onPress:
            self.onPress(self, display)
        elif self.altContent:
            resource.setViewState(self.value, display.views)
            self.altContent.render(display)
            
    def release(self, display, resource):
        if self.onRelease:
            self.onRelease(self, display)
        else:
            self.render(display)

        
