# Basic class definitions

stateChangeInterval = 10
running = True  # FIXME - get rid of this

import time
import threading
import copy
import sys
import json
from collections import OrderedDict
from .config import *
from .environment import *
from .logging import *
from .debugging import *

# states
off = 0
Off = 0
on = 1
On = 1

### general utility functions ###

# get the value of a variable from a file
def getValue(fileName, item):
    return json.load(open(fileName))[item]

# turn an item into a list if it is not already
def listize(x):
    return x if isinstance(x, list) else [x]

# normalize state values from boolean to integers
def normalState(value):
    if value == True: return On
    elif value == False: return Off
    else: return value

# Base class for Resources
class Resource(object):
    def __init__(self, name, persistence=None, defaultAttrs={}):
        try:
            if self.name:   # init has already been called for this object
                return
        except AttributeError:
            self.name = name
            debug('debugObject', self.__class__.__name__, self.name, "created")
            self.className = self.__class__.__name__    # hack for web templates - FIXME
        # optional state persistence interface
        if persistence:
            self.persistence = persistence
            self.defaultAttrs = defaultAttrs
            try:
                self.__dict__.update(defaultAttrs.update(self.persistence.read(self.name)))
            except:
                pass

    def __str__(self):
        return self.name

# Base class for Interfaces
class Interface(Resource):
    def __init__(self, name, interface=None, event=None):
        Resource.__init__(self, name)
        self.interface = interface
        # sensor state change event
        if event != None:                   # use the specified one
            self.event = event
        elif self.interface:
            self.event = interface.event    # otherwise inherit event from this interface's interface
        else:
            self.event = None
        debug('debugInterrupt', self.name, "interface event", self.event)
        self.sensors = {}   # sensors using this instance of the interface by name
        self.sensorAddrs = {}   # sensors using this instance of the interface by addr
        self.states = {}    # state cache
        self.enabled = True

    def start(self):
        return True

    def stop(self):
        return True

    def read(self, addr):
        return None

    def write(self, addr, theValue):
        return True

    def addSensor(self, sensor):
        debug('debugObject', self.__class__.__name__, self.name, "addSensor", sensor.name)
        self.sensors[sensor.name] = sensor
        self.sensorAddrs[sensor.addr] = sensor
        self.states[sensor.addr] = None
        sensor.event = self.event

    # return the data type of the state of the specified sensor
    def getStateType(self, sensor):
        return int

    # Trigger the sending of a state change notification
    def notify(self):
        if self.event:
            self.event.set()
            debug('debugInterrupt', self.name, "set", self.event)

# Resource collection

# todo
# - load tree
# - gets traverse tree
# - delete collection

class Collection(Resource, OrderedDict):
    def __init__(self, name, resources=[], aliases={}):
        Resource.__init__(self, name)
        OrderedDict.__init__(self)
        self.type = "collection"
        self.lock = threading.Lock()
        for resource in resources:
            self.addRes(resource)
        self.aliases = aliases
        debug('debugCollection', self.name, "aliases:", self.aliases)

    # Add a resource to the table
    def addRes(self, resource):
        self.__setitem__(resource.name, resource)

    # Delete a resource from the table
    def delRes(self, name):
        self.__delitem__(name)

    # Get a resource from the table
    # Return dummy sensor if not found
    def getRes(self, name, dummy=True):
        try:
            return self.__getitem__(name)
        except KeyError:
            if dummy:
                return Sensor(name, Interface("None"))
            else:
                raise

    # Return the list of resources that have the names specified in the list
    def getResList(self, names):
        resList = []
        for name in names:
            try:
                resList.append(self.getRes(name))
            except:
                pass
        return resList

    # Return a list of resource references that are members of the specified group
    # in order of addition to the table
    def getGroup(self, group):
        resourceList = []
        for resourceName in list(self.keys()):
            resource = self.__getitem__(resourceName)
            if group in listize(resource.group):
                resourceList.append(resource)
        return resourceList

    # dictionary of pertinent attributes
    def dict(self):
        return {"class":self.__class__.__name__,
                "name":self.name,
                "type": self.type,
                "resources":list(self.keys())}

# A Sensor represents a device that has a state that is represented by a scalar value.
# The state is associated with a unique address on an interface.
# Sensors can also optionally be associated with a group and a physical location.
class Sensor(Resource):
    def __init__(self, name, interface=None, addr=None, group="", type="sensor", location=None, label="", interrupt=None, event=None):
        Resource.__init__(self, name)
        try:
            if self.type:   # init has already been called for this object
                return
        except AttributeError:
            self.type = type
            if interface == None:
                self.interface = Interface("None", event=event)
            else:
                self.interface = interface
            self.addr = addr
            if self.addr == None:
                self.addr = self.name
            self.group = group
            if label == "":
                self.label = self.name
            else:
                self.label = label
            self.location = location
            if self.interface:
                self.interface.addSensor(self)
            self.interrupt = interrupt
            if event:
                self.event = event
                debug('debugInterrupt', self.name, "sensor event", self.event)
            self.__dict__["state"] = None   # dummy class variable so hasattr() returns True
            self.__dict__["stateChange"] = None   # dummy class variable so hasattr() returns True
            # FIXME - use @property

    # Return the state of the sensor by reading the value from the address on the interface.
    def getState(self):
        return normalState(self.interface.read(self.addr))

    # Return the last state of the sensor that was read from the address on the interface.
    def getLastState(self):
        return self.getState()

    # return the data type of the state
    def getStateType(self):
        return self.interface.getStateType(self)

    # Wait for the state of the sensor to change if an interrupt routine was specified
    def getStateChange(self):
        if self.event:
            # the routine that changes state must call notify() after the state is changed
            self.event.clear()
            debug('debugInterrupt', self.name, "clear", self.event)
            self.event.wait()
            debug('debugInterrupt', self.name, "wait", self.event)
        return self.getState()

    # Trigger the sending of a state change notification
    def notify(self):
        if self.event:
            self.event.set()
            debug('debugInterrupt', self.name, "set", self.event)

    # Define this function for sensors even though it does nothing
    def setState(self, state, wait=False):
        return False

    # override to handle special cases of state and stateChange
    def __getattribute__(self, attr):
        if attr == "state":
            return self.getState()
        elif attr == "stateChange":
            return self.getStateChange()
        else:
            return Resource.__getattribute__(self, attr)

    # override to handle special case of state
    def __setattr__(self, attr, value):
        if attr == "state":
            self.setState(value)
        else:
            Resource.__setattr__(self, attr, value)

    # dictionary of pertinent attributes
    def dict(self):
        return {"class":self.className, # FIXME __class__.__name__,
                "name":self.name,
                "type":self.type,
                "label":self.label,
                "interface":self.interface.name,
                "addr":self.addr.__str__(),
                "group":self.group,
                "location":self.location}

# A Control is a Sensor whose state can be set
class Control(Sensor):
    def __init__(self, name, interface, addr=None, group="", type="control", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.running = False

    # Set the state of the control by writing the value to the address on the interface.
    def setState(self, state, wait=False):
        debug('debugState', "Control", self.name, "setState ", state)
        self.interface.write(self.addr, state)
        self.notify()
        return True
