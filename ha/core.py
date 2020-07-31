# Core class definitions

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

# create a Resource from a serialized dict
def loadResource(classDict, globalDict):
    def parseClass(classDict):
        args = classDict["args"]
        argStr = ""
        for arg in list(args.keys()):
            argStr += arg+"="
            if isinstance(args[arg], dict):     # argument is a class
                argStr += parseClass(args[arg])+", "
            elif isinstance(args[arg], str):    # arg is a string
                argStr += "'"+args[arg]+"', "
            elif not arg:                       # arg is None
                argStr += "None"
            else:                               # arg is numeric or other
                argStr += str(args[arg])+", "
        return classDict["class"]+"("+argStr[:-2]+")"
    localDict = {}
    exec("resource = "+parseClass(classDict), globalDict, localDict)
    return localDict["resource"]

# Base class for everything
class Object(object):
    # dump the resource attributes to a serialized dict
    def dump(self):
        return {"class": self.__class__.__name__,
                "args": self.dict()}

# Base class for Resources
class Resource(Object):
    def __init__(self, name, type):
        try:
            if self.name:   # init has already been called for this object - FIXME
                return
        except AttributeError:
            self.name = name
            self.type = type
            debug('debugObject', self.__class__.__name__, self.name, "created")
            self.className = self.__class__.__name__    # hack for web templates - FIXME

    def __str__(self):
        return self.name

# Base class for Interfaces
class Interface(Resource):
    def __init__(self, name, interface=None, type="interface", event=None):
        Resource.__init__(self, name, type)
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

    def write(self, addr, value):
        return True

    def dump(self):
        return None

    def addSensor(self, sensor):
        debug('debugObject', self.__class__.__name__, self.name, "addSensor", sensor.name)
        self.sensors[sensor.name] = sensor
        self.sensorAddrs[sensor.addr] = sensor
        self.states[sensor.addr] = None
        sensor.event = self.event

    # Trigger the sending of a state change notification
    def notify(self):
        if self.event:
            self.event.set()
            debug('debugInterrupt', self.name, "set", self.event)

# Resource collection
class Collection(Resource, OrderedDict):
    def __init__(self, name, resources=[], aliases={}, type="collection", event=None):
        Resource.__init__(self, name, type)
        OrderedDict.__init__(self)
        self.lock = threading.Lock()
        for resource in resources:
            self.addRes(resource)
        self.aliases = aliases
        self.event = event
        self.states = {}    # current sensor states
        self.stateTypes = {}
        debug('debugCollection', self.name, "aliases:", self.aliases)

    # Add a resource to the table
    def addRes(self, resource):
        self.__setitem__(str(resource), resource)

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
                return Sensor(name) #, Interface("None"))
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

    # return the current state of all sensors in the collection
    def getState(self, wait=False):
        self.getStates(wait)
        return self.states

    # return the current state and type of all sensors in the collection
    def getStateTypes(self, wait=False):
        self.getStates(wait)
        return self.stateTypes

    # update the current state and type of all sensors in the resource collection
    def getStates(self, wait=False):
        if self.event and wait:
            self.event.wait()
            self.event.clear()
        with self.lock:
            try:
                for sensor in list(self.values()):
                    if sensor != self:
                        sensorName = sensor.name
                        sensorType = sensor.type
                        if sensorType in ["schedule", "collection"]:   # recurse into schedules and collections
                            self.getStates(sensor)
                        else:
                            sensorState = sensor.getState()
                            self.states[sensorName] = sensorState
                            self.stateTypes[sensorName] = (sensorState, sensorType)
            except Exception as ex:
                log(self.name, "getStates", "Exception", str(ex))

    # dictionary of pertinent attributes
    def dict(self):
        return { #"class":self.__class__.__name__,
                "name":self.name,
                "type": self.type,
                "resources":list(self.keys())}

# A Sensor represents a device that has a state that is represented by a scalar value.
# The state is associated with a unique address on an interface.
# Sensors can also optionally be associated with a group and a physical location.
class Sensor(Resource):
    def __init__(self, name, interface=None, addr=None, group="", type="sensor", location=None, label=None, interrupt=None, event=None):
        try:
            if self.type:   # init has already been called for this object - FIXME
                return
        except AttributeError:
            Resource.__init__(self, name, type)
            self.interface = interface
            self.addr = addr
            if self.interface:
                self.interface.addSensor(self)
            self.group = group
            if label:
                self.label = label
            else:
                self.label = self.name.capitalize()
            self.location = location
            self.interrupt = interrupt
            if event:
                self.event = event
                debug('debugInterrupt', self.name, "sensor event", self.event)
            self.__dict__["state"] = None   # dummy class variable so hasattr() returns True
            self.__dict__["stateChange"] = None   # dummy class variable so hasattr() returns True
            # FIXME - use @property

    # Return the state of the sensor by reading the value from the address on the interface.
    def getState(self):
        return (normalState(self.interface.read(self.addr)) if self.interface else None)

    # Return the last state of the sensor that was read from the address on the interface.
    def getLastState(self):
        return self.getState()

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
        return {#"class":self.className, # FIXME __class__.__name__,
                "name":self.name,
                "type":self.type,
                "label":self.label,
                "interface":(self.interface.name if self.interface else None),
                "addr":self.addr, #.__str__(),
                "group":self.group,
                "location":self.location}

# A Control is a Sensor whose state can be set
class Control(Sensor):
    def __init__(self, name, interface=None, addr=None, group="", type="control", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.running = False

    # Set the state of the control by writing the value to the address on the interface.
    def setState(self, state, wait=False):
        debug('debugState', "Control", self.name, "setState ", state)
        self.interface.write(self.addr, state)
        self.notify()
        return True
