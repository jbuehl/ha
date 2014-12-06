#!/usr/bin/python
# coding=utf-8

import time
import serial
import struct
import threading
from ha.HAClasses import *

########################################################################################################
# state of the pool and equipment
########################################################################################################
class AqualinkInterface(HAInterface):
    # constructor
    def __init__(self, theName, serialInterface):
        HAInterface.__init__(self, theName, serialInterface)
        
        self.stateChanged = True
        self.stateFileName = "root/ha/pool.state"   # FIXME

        # identity
        self.model = Device("model", "")
        self.title = Device("title", "")
        self.date = Device("date", "")
        self.time = Device("time", "")

        # configuration
        self.options = 0
        self.tempScale = ""
        
        # environment
        self.airTemp = Device("airTemp", 0)
        self.poolTemp = Device("poolTemp", 0)
        self.spaTemp = Device("spaTemp", 0)
        self.solarTemp = Device("solarTemp", 0)

        # modes
        self.opMode = "AUTO"

    def start(self):
        # restore state
        self.readState()
               
        # equipment
        self.pump = Equipment("pump", self)
        self.spa = Equipment("spa", self)
        self.aux1 = Equipment("aux1", self)
        self.aux2 = Equipment("aux2", self)
        self.aux3 = Equipment("aux3", self)
        self.aux4 = Equipment("aux4", self)
        self.aux5 = Equipment("aux5", self)
        self.aux6 = Equipment("aux6", self)
        self.aux7 = Equipment("aux7", self)
        self.poolHtr = Equipment("poolHtr", self)
        self.spaHtr = Equipment("spaHtr", self)

        self.equipList = [self.pump,
                            self.spa,
                            self.aux1,
                            self.aux2,
                            self.aux3,
                            self.aux4,
                            self.aux5,
                            self.aux6,
                            self.aux7,
                            self.poolHtr,
                            self.spaHtr,
                            self.airTemp,
                            self.poolTemp,
                            self.spaTemp,
                            self.solarTemp,
                            self.model,
                            self.title,
                            self.date,
                            self.time]

        self.equipDict = {}
        for equip in self.equipList:
            self.equipDict[equip.name] = equip

#        # Modes
#        self.cleanMode = Mode("cleanmode", self, 
#                              [self.pump, self.aux1])
#        self.spaMode = Mode("spamode", self, 
#                                [self.spa, self.spaHtr, self.aux4, self.aux5])
#        self.lightsMode = Mode("lightsmode", self, 
#                              [self.aux4, self.aux5])

        # initiate interface and panels
        self.master = Panel("Master", self)
        self.allButtonPanel = AllButtonPanel("All Button", self)
        self.panels = {allButtonPanelAddr: self.allButtonPanel}
        self.panel = self.panels.values()[0]
        self.interface = Interface("RS485", self)

        # get control sequences for equipment from the panel
        for equip in self.equipList:
            equip.action = self.panel.getAction(equip)

        # start cron thread
        if aqualinkClock:
            cronThread = threading.Thread(target=self.doCron)
            cronThread.start()

        if debugThread: log(self.name, "started")


    def read(self, theAddr):
        return self.equipDict[theAddr].state

    def write(self, theAddr, theValue):
        self.equipDict[theAddr].changeState(theValue)
        time.sleep(2)   # wait for state to change - FIXME

    # persistence of the controller state
    def readState(self):
        try:
            stateFile = open(self.stateFileName)
            for line in stateFile:
                try:
                    line = line[:line.find("#")].strip()
                    if line != "":
                        param = line.split("=")
                        setattr(self, param[0].strip(), Device(param[0].strip(), eval(param[1].strip())))
                except:
                    pass
            stateFile.close()
        except:
            pass

    def writeState(self):
        if self.stateChanged:
            stateFile = open(self.stateFileName, "w")
            stateFile.write("airTemp = "+str(self.airTemp.state)+"\n")
            stateFile.write("poolTemp = "+str(self.poolTemp.state)+"\n")
            stateFile.write("spaTemp = "+str(self.spaTemp.state)+"\n")
            stateFile.write("solarTemp = "+str(self.solarTemp.state)+"\n")
            stateFile.close()
            self.stateChanged = False
                
    def doCron(self):
        if debugThread: log("cron", "started")
        checkInterval = 10 # how often to check the time in minutes
        while True:
            self.checkTime()
            time.sleep(checkInterval*60)
        
    def checkTime(self):
        offTime = 5 # how many minutes the time has to be off by for it to get adjusted
        if (self.date.state != "") and (self.time.state != ""):
            realTime = time.localtime()
            poolTime = time.strptime(self.date.state+self.time.state, '%m/%d/%y %a%I:%M %p')
            diffTime = datetime.datetime(realTime.tm_year, realTime.tm_mon, realTime.tm_mday, realTime.tm_hour, realTime.tm_min) -\
                       datetime.datetime(poolTime.tm_year, poolTime.tm_mon, poolTime.tm_mday, poolTime.tm_hour, poolTime.tm_min)
            if debugTime: log("controller time", time.asctime(poolTime))
            if debugTime: log("local time", time.asctime(realTime))
            if debugTime: log("time difference", diffTime)
            if abs(diffTime.days*24*60 + diffTime.seconds/60) > offTime:    # time difference in minutes
                setTime = (realTime.tm_year - poolTime.tm_year,
                        realTime.tm_mon - poolTime.tm_mon,
                        realTime.tm_mday - poolTime.tm_mday,
                        realTime.tm_hour - poolTime.tm_hour,
                        realTime.tm_min - poolTime.tm_min)
                if debugTime: log("adjusting by", setTime.__str__())
                self.panel.adjustTime(setTime)

    def setModel(self, model, rev=""):
        if model != self.model.state:
            self.model.state = model+" Rev "+rev
            self.stateChanged = True
        self.writeState()        

    def setTitle(self, title):
        if title != self.title.state:
            self.title.state = title
            self.stateChanged = True
        self.writeState()        

    def setDate(self, theDate):
        if theDate != self.date.state:
            self.date.state = theDate
            self.stateChanged = True
        self.writeState()        

    def setTime(self, theTime):
        if theTime != self.time.state:
            self.time.state = theTime
            self.stateChanged = True
        self.writeState()        
        
    def setAirTemp(self, temp):
        if temp[0] != self.airTemp.state:
            self.airTemp.state = temp[0]
            self.tempScale = temp[1]
            self.stateChanged = True
        self.writeState()        
                    
    def setPoolTemp(self, temp):
        if temp[0] != self.poolTemp.state:
            self.poolTemp.state = temp[0]
            self.tempScale = temp[1]
            self.stateChanged = True
        self.writeState()        
        
    def setSpaTemp(self, temp):
        if temp[0] != self.spaTemp.state:
            self.spaTemp.state = temp[0]
            self.tempScale = temp[1]
            self.stateChanged = True
        self.writeState()        

    def printState(self, start="", end="\n"):
        msg  = start+"Title:      "+self.title.state+end
        msg += start+"Model:      "+self.model.state+end
        msg += start+"Date:       "+self.date.state+end
        msg += start+"Time:       "+self.time.state+end
        msg += start+"Air Temp:    %d°%s" %  (self.airTemp.state, self.tempScale)+end
        msg += start+"Pool Temp:   %d°%s" %  (self.poolTemp.state, self.tempScale)+end
        msg += start+"Spa Temp:    %d°%s" %  (self.spaTemp.state, self.tempScale)+end
        for equip in self.equipList:
            if equip.name != "":
                msg += start+"%-12s"%(equip.name+":")+equip.printState()+end
        return msg

class Device(HAResource):
    def __init__(self, theName, theState):
        HAResource.__init__(self, theName)
        self.state = theState
            
class Equipment(HAResource):
    # equipment states
    stateOff = 0
    stateOn = 1
    stateEna = 2
    stateEnh = 4

    def __init__(self, theName, thePool, theAction=None):
        HAResource.__init__(self, theName)
        self.pool = thePool
        self.action = theAction
        self.state = Equipment.stateOff

    def setState(self, newState):
        # sets the state of the equipment object, not the actual equipment
        self.state = newState
        self.pool.stateChanged = True
        #log(self.name, self.printState())

    def printState(self):
        if self.state == Equipment.stateOn: return "ON"
        elif self.state == Equipment.stateEna: return "ENA"
        elif self.state == Equipment.stateEnh: return "ENH"
        else: return "OFF"

    def changeState(self, newState, wait=False):
        # turns the equipment on or off
        if ((newState == Equipment.stateOn) and (self.state == Equipment.stateOff)) or\
           ((newState == Equipment.stateOff) and (self.state != Equipment.stateOff)):
            action = ActionThread(self.name+(" On" if newState else " Off"), 
                            [self.action], self.pool.panel)
            action.start()
            if wait:
                self.action.event.wait()

#class Mode(Equipment):
#    # a Mode is defined by an ordered list of Equipment that is turned on or off
#    def __init__(self, name, thePool, theEquipList):
#        Equipment.__init__(self, name, thePool)
#        self.equipList = theEquipList

#    def changeState(self, newState=None):
#        # turns the list of equipment on or off
#        if debugAction: log(self.name, self.state, newState)
#        if newState != None:
#            self.newState = newState
#        else:
#            # toggle if new state is not specified
#            self.newState = not self.state
#        # do the work in a thread so this function returns asynchronously
#        modeThread = threading.Thread(target=self.doMode)
#        modeThread.start()

#    def doMode(self):
#        if debugAction: log(self.name, "mode started", self.newState)
#        if self.newState == Equipment.stateOn:
#            # turn on equipment list in order
#            for equip in self.equipList:
#                equip.changeState(self.newState, wait=True)
#        else:
#            # turn off equipment list in reverse order
#             for equip in reversed(self.equipList):
#                equip.changeState(self.newState, wait=True)
#        if debugAction: log(self.name, "mode completed")
#        self.state = self.newState
#        #log(self.name, self.printState())
                
########################################################################################################
# Base Aqualink control panel
########################################################################################################

class Panel(HAResource):
    """
    Base Aqualink control Panel
    """
    
    # constructor
    def __init__(self, theName, thePool):
        HAResource.__init__(self, theName)
        self.pool = thePool

        # commands
        self.cmdProbe = Command("probe", 0x00, 0)
        self.cmdAck = Command("ack", 0x01, 2)
        self.cmdStatus = Command("status", 0x02, 5)
        self.cmdMsg = Command("msg", 0x03, 17)

        # buttons
        self.btnNone = Button("none", 0x00)

        # state
        self.ack = 0x00             # first byte of ack message
        self.button = self.btnNone       # current button pressed
        self.lastAck = 0x0000
        self.lastStatus = 0x0000000000

        # command parsing
        self.cmdTable = {self.cmdProbe.code: Panel.handleProbe,
                         self.cmdAck.code: Panel.handleAck,
                         self.cmdStatus.code: Panel.handleStatus,
                         self.cmdMsg.code: Panel.handleMsg}
                        
        # action events
        self.statusEvent = threading.Event()   # a status message has been received
        self.events = [self.statusEvent]
        
    # return the ack message for this panel        
    def getAckMsg(self):
        args = struct.pack("!B", self.ack)+struct.pack("!B", self.button.code)
        if self.button != self.btnNone:
            if debugAck: log(self.name, "ack", args.encode("hex"))
        self.button = self.btnNone
        return (struct.pack("!B", self.cmdAck.code), args)
        
    # parse a message and perform commands    
    def parseMsg(self, cmd, args):
        cmdCode = int(cmd.encode("hex"), 16)
        try:
            self.cmdTable[cmdCode](self, args)
        except KeyError:
            if debugMsg: log(self.name, "unknown", cmd.encode("hex"), args.encode("hex"))

    # probe command           
    def handleProbe(self, args):
        cmd = self.cmdProbe
        if debugProbe: log(self.name, cmd.name)

    # ack command
    def handleAck(self, args):
        cmd = self.cmdAck
        if args != self.lastAck:       # only display changed values
            self.lastAck = args
            if debugAck and monitorMode: log(self.name, cmd.name, args.encode("hex"))

    # status command
    def handleStatus(self, args):
        cmd = self.cmdStatus
        if args != self.lastStatus:    # only display changed values
            self.lastStatus = args
            if debugStatus: log(self.name, cmd.name, args.encode("hex"))
        self.statusEvent.set()

    # message command
    def handleMsg(self, args):
        cmd = self.cmdMsg
        if debugMsg: log(self.name, cmd.name, args.encode("hex"))
        
class Button(object):
    def __init__(self, theName, theCode):
        self.name = theName
        self.code = theCode
        
class Command(object):
    def __init__(self, theName, theCode, theArgLen):
        self.name = theName
        self.code = theCode
        self.argLen = theArgLen

########################################################################################################
# action thread
########################################################################################################
class ActionThread(threading.Thread):
    # An ActionThread executes a sequence of actions
    def __init__(self, theName, theSequence, thePanel):
        threading.Thread.__init__(self, target=self.doAction)
        self.name = theName
        self.sequence = theSequence
        self.panel = thePanel
        # Clear all the events before starting.
        for action in self.sequence:
            action.event.clear()

    def doAction(self):
        if debugAction: log(self.name, "action started")
        for action in self.sequence:
            if not running: break
            self.panel.button = action.button # set the button to be sent to start the action
            if debugAction: log(self.name, "button", action.button.name, "sent")
            action.event.wait()              # wait for the event that corresponds to the completion
            if debugAction: log(self.name, "button", action.button.name, "completed")
            time.sleep(1)
        if debugAction: log(self.name, "action completed")

class Action(object):
    # An Action consists of a command and an event.
    # When an Action is executed, the command is sent and the event is set when the command is complete.
    def __init__(self, theButton, theEvent):
        self.button = theButton
        self.event = theEvent

########################################################################################################
# All Button panel
########################################################################################################

class AllButtonPanel(Panel):
    def __init__(self, theName, thePool):
        Panel.__init__(self, theName, thePool)

        # addressing
        self.baseAddr = 0x08
        self.maxDevices = 4

        self.degSym = '\xdf'
        
        # commands
        self.cmdLongMsg = Command("longMsg", 0x04, 17)

        # buttons
        self.btnPump         = Button("pump", 0x02)
        self.btnSpa          = Button("spa", 0x01)
        self.btnAux1         = Button("aux1", 0x05)
        self.btnAux2         = Button("aux2", 0x0a)
        self.btnAux3         = Button("aux3", 0x0f)
        self.btnAux4         = Button("aux4", 0x06)
        self.btnAux5         = Button("aux5", 0x0b)
        self.btnAux6         = Button("aux6", 0x10)
        self.btnAux7         = Button("aux7", 0x15)
        self.btnPoolHtr      = Button("poolhtr", 0x12)
        self.btnSpaHtr       = Button("spahtr", 0x17)
        self.btnSolarHtr     = Button("solarhtr", 0x1c)
        self.btnMenu         = Button("menu", 0x09)
        self.btnCancel       = Button("cancel", 0x0e)
        self.btnLeft         = Button("left", 0x13)
        self.btnRight        = Button("right", 0x18)
        self.btnHold         = Button("hold", 0x19)
        self.btnOverride     = Button("override", 0x1e)
        self.btnEnter        = Button("enter", 0x1d)

        # command parsing
        del(self.cmdTable[self.cmdStatus.code])
        del(self.cmdTable[self.cmdMsg.code])
        self.cmdTable.update({self.cmdStatus.code: AllButtonPanel.handleStatus,
                              self.cmdMsg.code: AllButtonPanel.handleMsg,
                              self.cmdLongMsg.code: AllButtonPanel.handleLongMsg})
        self.firstMsg = True

        # action events
        self.msgEvent = threading.Event()

        # create the list of associations between equipment, button codes, and status masks.
        self.equipList = [PanelEquip(self.pool.aux2, self.btnAux2, 0xc000000000),
                          PanelEquip(self.pool.aux3, self.btnAux3, 0x3000000000),
                          PanelEquip(self.pool.aux7, self.btnAux7, 0x0300000000),
                          PanelEquip(self.pool.aux5, self.btnAux5, 0x00c0000000),
                          PanelEquip(self.pool.pump, self.btnPump, 0x0030000000),
                          PanelEquip(self.pool.spa, self.btnSpa, 0x000c000000),
                          PanelEquip(self.pool.aux1, self.btnAux1, 0x0003000000),
                          PanelEquip(self.pool.aux6, self.btnAux6, 0x0000c00000),
                          PanelEquip(self.pool.aux4, self.btnAux4, 0x0000030000),
                          PanelEquip(self.pool.spaHtr, self.btnSpaHtr, 0x000000000f),
                          PanelEquip(self.pool.spaHtr, self.btnPoolHtr, 0x000000f000),
                          PanelEquip(self.pool.spaHtr, self.btnSolarHtr, 0x00000000f0)]

        # add equipment events to the event list
        self.events += [self.msgEvent]
        for equip in self.equipList:
            self.events += [equip.event]
        
        # menu actions
        self.menuAction = Action(self.btnMenu, self.msgEvent)
        self.leftAction = Action(self.btnLeft, self.msgEvent)
        self.rightAction = Action(self.btnRight, self.msgEvent)
        self.cancelAction = Action(self.btnCancel, self.msgEvent)
        self.enterAction = Action(self.btnEnter, self.msgEvent)

    def dupAction(self, nTimes):
        # create a sequence containing a right or left action duplicated n times
        seq = []
        if nTimes != 0:
            action = self.rightAction if nTimes > 0 else self.leftAction
            for i in range(0, abs(nTimes)):
                seq += [action]
        return seq
            
    def adjustTime(self, timeDiff):
        # create and execute a sequence that adjusts the time on the controller by the specified difference.
        if debug: log(self.name)
        seq = [self.menuAction] + self.dupAction(3) + [self.enterAction]+\
               self.dupAction(timeDiff[0]) + [self.enterAction] +\
               self.dupAction(timeDiff[1]) + [self.enterAction] +\
               self.dupAction(timeDiff[2]) + [self.enterAction] +\
               self.dupAction(timeDiff[3]) + [self.enterAction] +\
               self.dupAction(timeDiff[4]) + [self.enterAction]
        action = ActionThread("set time", seq, self)
        action.start()

    def menu(self):
        if debug: log(self.name)
        action = ActionThread("menu", [self.menuAction], self)
        action.start()

    def left(self):
        if debug: log(self.name)
        action = ActionThread("left", [self.leftAction], self)
        action.start()

    def right(self):
        if debug: log(self.name)
        action = ActionThread("right", [self.rightAction], self)
        action.start()

    def cancel(self):
        if debug: log(self.name)
        action = ActionThread("cancel", [self.cancelAction], self)
        action.start()

    def enter(self):
        if debug: log(self.name)
        action = ActionThread("enter", [self.enterAction], self)
        action.start()

    def getAction(self, poolEquip):
        # return the action associated with the specified equipment
        for equip in self.equipList:
            if equip.equip == poolEquip:
                return equip.action
        return None
                
    # status command
    def handleStatus(self, args):
        cmd = self.cmdStatus
        status = int(args.encode("hex"), 16)
        if status != self.lastStatus:    # only process changed values
            if debugStatus: log(self.name, cmd.name, "%010x"%(status))
            for equip in self.equipList:
                shift = min(filter(lambda s: (equip.mask >> s) & 1 != 0, xrange(8*cmd.argLen)))
                newState = (status & equip.mask) >> shift
                oldState = (self.lastStatus & equip.mask) >> shift
                if newState != oldState:
                    if debugStatus: log(self.name, cmd.name, equip.equip.name, "state current", "%x"%oldState, "new", "%x"%newState)
                    # set the equipment state
                    equip.equip.setState(newState)
                    # set the event
                    equip.event.set()
            self.lastStatus = status

    # message command
    def handleMsg(self, args):
        cmd = self.cmdMsg
        self.handleMessage(cmd, args)

    # long message command
    def handleLongMsg(self, args):
        cmd = self.cmdLongMsg
#        self.handleMessage(cmd, args)

    # handle messages
    def handleMessage(self, cmd, args):
        try:
            line = struct.unpack("!B", args[0])[0]
            msg = args[1:].replace("\0", " ").strip(" ")
            if debugMsg: log(self.name, cmd.name, line, args[1:])
            msgParts = msg.split()
            if line == 0:
                self.msgEvent.set()
                if len(msgParts) > 1:
                    if self.firstMsg:
                        self.pool.setModel(msgParts[0], msgParts[2])
                        self.firstMsg = False
                        return
                    if msgParts[1] == "TEMP":
                        if msgParts[0] == "POOL":
                            self.pool.setPoolTemp(self.parseTemp(msgParts[2]))
                        elif msgParts[0] == "SPA":
                            self.pool.setSpaTemp(self.parseTemp(msgParts[2]))
                        elif msgParts[0] == "AIR":
                            self.pool.setAirTemp(self.parseTemp(msgParts[2]))
                        return
                    dateParts = msgParts[0].split("/")
                    if len(dateParts) > 1:
                        self.pool.setDate(msg)
                        return
                    timeParts = msgParts[0].split(":")
                    if len(timeParts) > 1:
                        self.pool.setTime(msg)
                        return
                if (msgParts[-1] != "OFF") and (msgParts[-1] != "ON"):
                    if self.pool.title == "":
                        self.pool.setTitle(msg)
        except:
            pass

    def parseTemp(self, msg):
        degPos = msg.find(self.degSym)
        return (int(msg[:degPos]), msg[degPos+1:])

class PanelEquip(object):
    def __init__(self, theEquip, theButton, theMask):
        self.equip = theEquip
        self.button = theButton
        self.mask = theMask
        self.event = threading.Event()
        self.action = Action(self.button, self.event)

# ASCII constants
NUL = '\x00'
DLE = '\x10'
STX = '\x02'
ETX = '\x03'

masterAddr = '\x00'          # address of Aqualink controller

class Interface(HAResource):
    """ Aqualink serial interface

    """
    def __init__(self, theName, thePool):
        """Initialization.
        Open the serial port and find the start of a message."""
        HAResource.__init__(self, theName)
        self.pool = thePool
        if debugData: log(self.name, "opening RS485 port", self.pool.interface.name)
        thePool.interface.start()
        self.port = thePool.interface.inPort
        self.msg = "\x00\x00"
        self.debugRawMsg = ""
        # skip bytes until synchronized with the start of a message
        while (self.msg[-1] != STX) or (self.msg[-2] != DLE):
            self.msg += self.port.read(1)
            if debugRaw: self.debugRaw(self.msg[-1])
        self.msg = self.msg[-2:]
        if debugData: log(self.name, "synchronized")
        # start up the read thread
        readThread = ReadThread("Read", self.pool)
        readThread.start()
        if debugThread: log(self.name, "ready")
          
    def readMsg(self):
        """ Read the next valid message from the serial port.
        Parses and returns the destination address, command, and arguments as a 
        tuple."""
        while True:                                         
            dleFound = False
            # read what is probably the DLE STX
            self.msg += self.port.read(2)                   
            if debugRaw: 
                self.debugRaw(self.msg[-2])
                self.debugRaw(self.msg[-1])
            while (self.msg[-1] != ETX) or (not dleFound):  
                # read until DLE ETX
                self.msg += self.port.read(1)
                if debugRaw: self.debugRaw(self.msg[-1])
                if self.msg[-1] == DLE:                     
                    # \x10 read, tentatively is a DLE
                    dleFound = True
                if (self.msg[-2] == DLE) and (self.msg[-1] == NUL) and dleFound: 
                    # skip a NUL following a DLE
                    self.msg = self.msg[:-1]
                    # it wasn't a DLE after all
                    dleFound = False                        
            # skip any NULs between messages
            self.msg = self.msg.lstrip('\x00')
            # parse the elements of the message              
            dlestx = self.msg[0:2]
            dest = self.msg[2:3]
            cmd = self.msg[3:4]
            args = self.msg[4:-3]
            checksum = self.msg[-3:-2]
            dleetx = self.msg[-2:]
            if debugData: debugMsg = dlestx.encode("hex")+" "+dest.encode("hex")+" "+\
                                     cmd.encode("hex")+" "+args.encode("hex")+" "+\
                                     checksum.encode("hex")+" "+dleetx.encode("hex")
            self.msg = ""
            # stop reading if a message with a valid checksum is read
            if self.checksum(dlestx+dest+cmd+args) == checksum:
                if debugData: log(self.name, "-->", debugMsg)
                return (dest, cmd, args)
            else:
                if debugData: log(self.name, "-->", debugMsg, 
                                  "*** bad checksum ***")

    def sendMsg(self, (dest, cmd, args)):
        """ Send a message.
        The destination address, command, and arguments are specified as a tuple."""
        msg = DLE+STX+dest+cmd+args
        msg = msg+self.checksum(msg)+DLE+ETX
        for i in range(2,len(msg)-2):                       
            # if a byte in the message has the value \x10 insert a NUL after it
            if msg[i] == DLE:
                msg = msg[0:i+1]+NUL+msg[i+1:]
        if debugData: log(self.name, "<--", msg[0:2].encode("hex"), 
                          msg[2:3].encode("hex"), msg[3:4].encode("hex"), 
                          msg[4:-3].encode("hex"), msg[-3:-2].encode("hex"), 
                          msg[-2:].encode("hex"))
        n = self.port.write(msg)

    def checksum(self, msg):
        """ Compute the checksum of a string of bytes."""                
        return struct.pack("!B", reduce(lambda x,y:x+y, map(ord, msg)) % 256)

    def debugRaw(self, byte):
        """ Debug raw serial data."""
        self.debugRawMsg += byte
        if len(self.debugRawMsg) == 16:
            log(self.name, self.debugRawMsg).encode("hex")
            self.debugRawMsg = ""
            
    def __del__(self):
        """ Clean up."""
        self.port.close()
                
class ReadThread(threading.Thread):
    """ Message reading thread.

    """
    def __init__(self, theName, thePool):
        """ Initialize the thread."""        
        threading.Thread.__init__(self, target=self.readData)
        self.name = theName
        self.pool = thePool
        self.lastDest = 0xff
        
    def readData(self):
        """ Message handling loop.
        Read messages from the interface and if they are addressed to one of the
        panels, send an Ack to the controller and process the command."""
        if debugThread: log(self.name, "started")
        while running:
            # read until the program state changes to not running
            if not running: break
            (dest, cmd, args) = self.pool.interface.readMsg()
            try:                         
                # handle messages that are addressed to these panels
                if not monitorMode:      
                    # send Ack if not passively monitoring
                    self.pool.interface.sendMsg((masterAddr,) + \
                                                self.pool.panels[dest].getAckMsg())
                self.pool.panels[dest].parseMsg(cmd, args)
                self.lastDest = dest
            except KeyError:                      
                # ignore other messages except...
                if (dest == masterAddr) and \
                        (self.lastDest in self.pool.panels.keys()): 
                    # parse ack messages to master that are from these panels
                    self.pool.master.parseMsg(cmd, args)
        # force all pending panel events to complete
        for panel in self.pool.panels.values():   
            for event in panel.events:
                event.set()
        if debugThread: log(self.name, "terminated")
           
