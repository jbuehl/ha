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

fbLib = "/root/ha/ha/libfb.so"

from ctypes import cdll
import freetype
import evdev
import time
import threading
import copy
import webcolors
import png
from ha import *
from ha.haWebViews import *

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

def rgb2fb(rgbPixMap):
    fbPixMap = ""
    for pix in range(0, len(rgbPixMap), 3):
        fbPixMap += chr(rgbPixMap[pix+2]) + chr(rgbPixMap[pix+1]) + chr(rgbPixMap[pix]) + "\xff"
    return fbPixMap

def color(colorName):
    return rgb2fb(webcolors.name_to_rgb(colorName))

def printAttrs(style):
    return ["%s: %s"%(attr, style.__dict__[attr]) for attr in ["name", "xPos", "yPos", "width", "height", "margin"]]
        
class Display(object):
    def __init__(self, displayDevice="/dev/fb0", inputDevice="/dev/input/event0", views=None):
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
        
        def UpdateThread():
            while True:
                for resourceElement in self.resourceElements:
                    resource = resourceElement[0]
                    element = resourceElement[1]
                    resState = resource.getViewState(self.views)
                    element.setValue(resState)
                    if resource.type in tempTypes:
                        element.fgColor = rgb2fb(eval(tempColor(resState).lstrip("rgb")))
                    resourceElement[1].render(self)
                time.sleep(10)
        updateThread = threading.Thread(target=UpdateThread)
        updateThread.start()
        
        if block:
            while True:
                time.sleep(1)

    def addResource(self, resource, element):
        self.resourceElements.append((resource, element))

    def findButton(self, xPos, yPos):
        for resourceElement in self.resourceElements:
            if resourceElement[1].__class__.__name__ == "Button":
                button = resourceElement[1]
                if (xPos >= button.xPos) and (xPos <= button.xPos+button.width) and \
                   (yPos >= button.yPos) and (yPos <= button.yPos+button.height):
                    return resourceElement
        return None
    
    def clear(self, color):
        with self.lock:
            self.FrameBuffer.fill(self.frameBuffer, color)

    def fill(self, xPos, yPos, width, height, color):
        with self.lock:
            self.FrameBuffer.setPixMap(self.frameBuffer, xPos, yPos, width, height, color*width*height)

    def renderPixMap(self, xPos, yPos, width, height, pixMap):
        with self.lock:
            self.FrameBuffer.setPixMap(self.frameBuffer, xPos, yPos, width, height, pixMap)
    
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
                
class Container(Element):
    def __init__(self, name, style=None, itemList=[], **args):
        Element.__init__(self, name, style, **args)
        self.itemList = itemList
        
    def render(self, display):
        debug("debugDisplay", self.name, "Container.render()", printAttrs(self))
        display.fill(self.xPos, self.yPos, self.width, self.height, self.bgColor)
        for item in self.itemList:
            item.render(display)
        
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

# https://github.com/rougier/freetype-py/
# http://freetype-py.readthedocs.io/en/latest/glyph_slot.html
# https://www.freetype.org/freetype2/docs/tutorial/step2.html#section-4
class Text(Element):
    def __init__(self, name, style=None, value="", display=None, resource=None, **args):
        Element.__init__(self, name, style, **args)
        self.value = value
        if display and resource:
            display.addResource(resource, self)
        
    def setValue(self, value):
        self.value = value

    def render(self, display, style=None, value=""):
        renderStyle = copy.copy(self)
        if style:
            renderStyle.__dict__.update(style.__dict__)
        debug("debugDisplay", self.name, "Text.render()", printAttrs(renderStyle))
        if value == "":
            value = self.value
        display.renderChars(renderStyle.face, renderStyle.fontSize, value, 
            self.xPos+self.margin, self.yPos+self.margin, 
            renderStyle.margin+renderStyle.padding, 2*(renderStyle.height-2*renderStyle.margin)/3, 
            renderStyle.fgColor, renderStyle.bgColor,
            renderStyle.width-2*renderStyle.margin, renderStyle.height-2*renderStyle.margin)
        del(renderStyle)
        
class Image(Element):
    def __init__(self, name, style=None, imageFile="", value="", **args):
        Element.__init__(self, name, style, **args)
        pngReader = png.Reader(imageFile)
        pngImage = pngReader.read()
        self.width = pngImage[0] + 2*self.style.margin
        self.height = pngImage[1] + 2*self.style.margin
        print "Image", self.name, self.width, self.height
        self.image = png2fb(pngImage)
        self.value=value
        
    def setImage(self, image):
        self.image = image

    def render(self, display, style=None, image=None):
        renderStyle = copy.copy(self)
        if style:
            renderStyle.__dict__.update(style.__dict__)
        debug("debugDisplay", self.name, "Image.render()", printAttrs(renderStyle))
        if image == None:
            image = self.image
        display.renderPixMap(self.xPos+self.margin, self.yPos+self.margin, 
                                  self.width-2*self.margin, self.height-2*self.margin, 
                                  self.image)
        del(renderStyle)
        
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

        
