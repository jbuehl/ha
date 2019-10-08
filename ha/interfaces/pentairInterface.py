
import time
import serial
import struct
import threading
from ha import *
from functools import reduce

# ASCII constants
NUL = '\x00'
DLE = '\x10'
STX = '\x02'
ETX = '\x03'
SOM = '\xa5'    # start of message
FIL = '\xff'    # filler
          
# addresses
ctrlAddr  = '\x11'

# commands
writeCmd   = '\x01'
setCtrlCmd = '\x04'
setModCmd  = '\x05'
setRunCmd  = '\x06'
sendCmd    = '\x07'

# pump constants
pa = 12.50
pb = 1377.22
pc = 75.28

########################################################################################################
# state of the pool pump
########################################################################################################
class PentairInterface(Interface):
    objectArgs = ["interface", "event"]
    # constructor
    def __init__(self, name, interface=None, event=None):
        Interface.__init__(self, name, interface=interface, event=event)
        # in theory there could be multiple pumps on an interface, but assume just one for now
        self.addr = pentairAddr
        
        # The pump state consists of 4 values:
        # 0 - predefined pump speed 0..3
        # 1 - speed in rpm
        # 2 - power in watts
        # 3 - flow in gpm 
        
        self.state = [0, 0, 0, 0]
        self.manSpeed = 0           # the speed to which the pump has been manually set
        self.reqSpeed = -1          # the speed to which it is being requested to be set manually
        
    def start(self):
        debug('debugPentairData', self.name, "starting pentair interface", self.interface.name)
        self.interface.start()
        msgThread = PentairMsgThread("pentair msg", self)
        msgThread.start()

    def read(self, addr):
        return self.state[addr]

    def write(self, addr, value):
        if value in range(0, 5):
            self.reqSpeed = value

    def readState(self):
        self.sendMsg((self.addr, setCtrlCmd, '\xff'))
        (dest, cmd, reply) = self.readMsg()
        self.sendMsg((self.addr, sendCmd, ''))
        (src, cmd, stat) = self.readMsg()
        status = struct.unpack("!BBBHHBBBBBBBB", stat)
        self.sendMsg((self.addr, setCtrlCmd, '\x00'))
        (src, cmd, reply) = self.readMsg()
        self.state[1] = status[4]
        self.state[2] = status[3]
        try:
            rpmRatio = status[4]/3450.0
            self.state[3] = (status[3]-pb*rpmRatio**3-pc)/(pa*rpmRatio**2)
        except:
            self.state[3] = 0.0
        # set the speed to the index of the table entry that is next highest to the rpm value
        self.state[0] = 0
        for speed in range(len(pentairSpeeds)):
            if self.state[1] <= pentairSpeeds[speed]:
                self.state[0] = speed
                break

    def setSpeed(self, theSpeed):
        dat = struct.pack("!L",0x03210000+(theSpeed<<3))
        self.sendMsg((self.addr, setCtrlCmd, '\xff'))
        (dest, cmd, reply) = self.readMsg()
        self.sendMsg((self.addr, writeCmd, dat))
        (dest, cmd, reply) = self.readMsg()
#            self.sendMsg((pumpAddr, sendCmd, ''))
#            (src, cmd, stat) = self.readMsg()
#            status = struct.unpack("!BBBHHBBBBBBBB", stat)
        self.sendMsg((self.addr, setCtrlCmd, '\x00'))
        (src, cmd, reply) = self.readMsg()
    
    def readMsg(self):
        """ Read the next valid message from the serial port.
        Parses and returns the source address, command, and data as a tuple."""
        while True:                                         
            pmsg = PentairMsg(iface=self.interface)
            # stop reading if a message with a valid checksum is read
            if checksum16(pmsg.msg[0:-2]) == pmsg.sum:
                debug('debugPentairData', self.name, "-->", pmsg.printState())
                return (pmsg.src, pmsg.cmd, pmsg.dat)
            else:
                debug('debugPentairData', self.name, "-->", pmsg.printState(), 
                                  "*** bad checksum ***")
                return (pmsg.src, pmsg.cmd, pmsg.dat)

    def sendMsg(self, xxx_todo_changeme):
        """ Send a message.
        The destination address, command, and data are specified as a tuple."""
        (dst, cmd, dat) = xxx_todo_changeme
        pmsg = PentairMsg(dst=dst, src=ctrlAddr, cmd=cmd, dat=dat)
        debug('debugPentairData', self.name, "<--", pmsg.printState())
        self.interface.write(None, FIL+NUL+FIL+pmsg.msg)

class PentairMsg(object):
    def __init__(self, iface=None, dst="", src="", cmd="", dat=""):
        if iface != None:    # read the message from the interface and parse it
            self.msg = ""                  
            while (self.msg != SOM):            # read until \xa5 
                self.msg = iface.read(None, 1)
            self.msg += iface.read(None, 5)            # read header
            dataLen = struct.unpack("!B", self.msg[-1])[0]
            self.msg += iface.read(None, dataLen+2)    # read data and checksum
            self.som = self.msg[0]
            self.sub = self.msg[1]
            self.dst = self.msg[2]
            self.src = self.msg[3]
            self.cmd = self.msg[4]
            self.len = self.msg[5]
            self.dat = self.msg[6:-2]
            self.sum = self.msg[-2:]
        else:           # construct the message from arguments
            self.som = SOM
            self.sub = NUL
            self.dst = dst
            self.src = src
            self.cmd = cmd
            self.len = struct.pack("!B", len(dat))
            self.dat = dat
            self.msg = self.som+self.sub+self.dst+self.src+cmd+self.len+self.dat
            self.sum = checksum16(self.msg)
            self.msg = self.msg+self.sum

    def printState(self):
        return self.som.encode("hex")+self.sub.encode("hex")+" "+\
                             self.dst.encode("hex")+" "+self.src.encode("hex")+" "+\
                             self.cmd.encode("hex")+" "+self.len.encode("hex")+" "+\
                             self.dat.encode("hex")+" "+\
                             self.sum.encode("hex")

class PentairMsgThread(threading.Thread):
    """ Message handling thread.

    """
    def __init__(self, name, interface=None):
        """ Initialize the thread."""        
        threading.Thread.__init__(self, target=self.doMsg)
        self.name = name
        self.interface = interface
        
    def doMsg(self):
        """ Message handling loop.
        """
        debug('debugThread', self.name, "started")
        debug('debugPentairThread', self.name, "reading status")
        self.interface.readState()
        loopCount = 0
        refreshInterval = 25
        # wake up every second
        while running:
            # loop until the program state changes to not running
            if not running: break
            # set the speed if there was a request to change it
            if self.interface.reqSpeed >= 0:
                debug('debugPentairThread', self.name, "setting speed to", self.interface.reqSpeed)
                self.interface.setSpeed(self.interface.reqSpeed)
                self.interface.manSpeed = self.interface.reqSpeed
                self.interface.reqSpeed = -1
                loopCount = refreshInterval
            # check the status every refresh interval
            if loopCount == refreshInterval:
                # if the pump has been manually set, resend the message to maintain the speed
                if self.interface.manSpeed > 0:
                    debug('debugPentairThread', self.name, "maintaining speed", self.interface.manSpeed)
                    self.interface.setSpeed(self.interface.manSpeed)
#                debug('debugPentairThread', self.name, "reading status")
                self.interface.readState()
                loopCount = 0
            loopCount += 1
            time.sleep(1)
        debug('debugThread', self.name, "terminated")

def checksum16(msg):
    """ Compute the 16 bit checksum of a string of bytes."""                
    return struct.pack("!H", reduce(lambda x,y:x+y, list(map(ord, msg))) % 16384)


