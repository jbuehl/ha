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

# Compare two state dictionaries and return a dictionary containing the items
# whose values don't match or aren't in the old dict.
# If an item is in the old but not in the new, optionally include the item with value None.
def diffStates(old, new, deleted=True):
    diff = copy.copy(new)
    for key in list(old.keys()):
        try:
            if new[key] == old[key]:
                del diff[key]   # values match
        except KeyError:        # item is missing from the new dict
            if deleted:         # include deleted item in output
                diff[key] = None
    return diff

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
    def __init__(self):
        self.className = self.__class__.__name__    # Used to optionally override the real class name in dump()

    # dump the resource attributes to a serialized dict
    def dump(self, expand=False):
        return {"class": self.className,
                "args": self.dict(expand)}

# Base class for Resources
class Resource(Object):
    def __init__(self, name, type):
        Object.__init__(self)
        try:
            if self.name:   # init has already been called for this object - FIXME
                return
        except AttributeError:
            self.name = name
            self.type = type
            self.collections = {}   # list of collections that include this resource
            debug('debugObject', self.__class__.__name__, self.name, "created")

    # add this resource to the specified collection
    def addCollection(self, collection):
        self.collections[collection.name] = collection

    # remove this resource from the specified collection
    def delCollection(self, collection):
        del self.collections[collection.name]

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
        self.sensors = {}       # sensors using this instance of the interface by name
        self.sensorAddrs = {}   # sensors using this instance of the interface by addr
        self.states = {}        # sensor state cache
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

    # add a sensor to this interface
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

# Resource collection
class Collection(Resource, OrderedDict):
    def __init__(self, name, resources=[], aliases={}, type="collection", event=None):
        Resource.__init__(self, name, type)
        OrderedDict.__init__(self)
        self.lock = threading.Lock()
        self.states = {}    # cache of current sensor states
        for resource in resources:
            self.addRes(resource)
        self.aliases = aliases
        if event:
            self.event = event
        else:
            self.event = threading.Event()
        debug('debugCollection', self.name, "aliases:", self.aliases)

    def start(self):
        # thread to periodically poll the state of the resources in the collection
        def pollStates():
            debug('debugCollection', self.name, "starting resource polling")
            resourcePollCounts = {resource.name: resource.pollInterval for resource in list(self.values())}
            while True:
                stateChanged = False
                with self.lock:
                    for resource in list(self.values()):
                        try:
                            if not resource.event:    # don't poll resources with events
                                if resource.type not in ["schedule", "collection"]:   # skip resources that don't have a state
                                    if resourcePollCounts[resource.name] == 0:          # count has decremented to zero
                                        resourceState = resource.getState()
                                        debug('debugCollection', self.name, resource.name, self.states[resource.name], resourceState)
                                        if resourceState != self.states[resource.name]: # save the state if it has changed
                                            self.states[resource.name] = resourceState
                                            stateChanged = True
                                        resourcePollCounts[resource.name] = resource.pollInterval
                                    else:   # decrement the count
                                        resourcePollCounts[resource.name] -= 1
                        except Exception as ex:
                            log(self.name, "pollStates", "Exception", str(ex))
                if stateChanged:    # at least one resource state changed
                    self.event.set()
                    stateChanged = False
                time.sleep(1)
            debug('debugCollection', self.name, "ending resource polling")
        # initialize the resource state cache
        for resource in list(self.values()):
            if resource.type not in ["schedule", "collection"]:   # skip resources that don't have a state
                try:
                    self.states[resource.name] = resource.getState()    # load the initial state
                except Exception as ex:
                    log(self.name, "start", "Exception", str(ex))
        pollStatesThread = threading.Thread(target=pollStates)
        pollStatesThread.start()

    # Add a resource to this collection
    def addRes(self, resource):
        with self.lock:
            self.__setitem__(str(resource), resource)
            resource.addCollection(self)
            self.states[resource.name] = None

    # Delete a resource from this collection
    def delRes(self, name):
        with self.lock:
            del self.states[name]
            resource.delCollection(self)
            self.__delitem__(name)

    # Get a resource from the collection
    # Return dummy sensor if not found
    def getRes(self, name, dummy=True):
        try:
            return self.__getitem__(name)
        except KeyError:
            if dummy:
                return Sensor(name)
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

    # get the current state of all sensors in the resource collection
    def getStates(self, wait=False):
        if self.event and wait:
            self.event.clear()
            self.event.wait()
        return copy.copy(self.states)

    # set the state of the specified sensor in the cache
    def setState(self, sensor, state):
        self.states[sensor.name] = state

    # set state values of all sensors into the cache
    def setStates(self, states):
        for sensor in list(states.keys()):
            self.states[sensor] = states[sensor]

    # Trigger the sending of a state change notification
    def notify(self):
        if self.event:
            self.event.set()

    # dictionary of pertinent attributes
    def dict(self, expand=False):
        return {"name":self.name,
                "type": self.type,
                "resources":([attr.dump(expand) for attr in list(self.values())] if expand else list(self.keys()))}

# A Sensor represents a device that has a state that is represented by a scalar value.
# The state is associated with a unique address on an interface.
# Sensors can also optionally be associated with a group and a physical location.
class Sensor(Resource):
    def __init__(self, name, interface=None, addr=None, type="sensor",
                 resolution=0, pollInterval=1, event=None, persistence=None,
                 location=None, group="", label=None):
        try:
            if self.type:   # init has already been called for this object - FIXME
                return
        except AttributeError:
            Resource.__init__(self, name, type)
            self.interface = interface
            self.addr = addr
            if self.interface:
                self.interface.addSensor(self)
            self.resolution = resolution
            self.pollInterval = pollInterval
            if event:
                self.event = event
            elif self.interface:       # inherit the event from the interface if not specified
                self.event = self.interface.event
            else:
                self.event = None
            self.persistence = persistence
            self.location = location
            self.group = listize(group)
            if label:
                self.label = label
            else:
                self.label = self.name.capitalize()
            self.__dict__["state"] = None   # dummy class variable so hasattr() returns True
            # FIXME - use @property

    # Return the state of the sensor by reading the value from the address on the interface.
    def getState(self):
        state = (normalState(self.interface.read(self.addr)) if self.interface else None)
        try:
            return round(state, self.resolution)
        except TypeError:
            return state

    # Return the last state of the sensor that was read from the address on the interface.
    # def getLastState(self):
    #     return self.getState()

    # Trigger the sending of a state change notification
    def notify(self, state=None):
        log("notify", self.name, self.state)
        if not state:
            state = self.getState()
        for collection in list(self.collections.keys()):
            self.collections[collection].setState(self, state)
        if self.event:
            self.event.set()

    # Define this function for sensors even though it does nothing
    def setState(self, state, wait=False):
        return False

    # override to handle special cases of state
    def __getattribute__(self, attr):
        if attr == "state":
            return self.getState()
        else:
            return Resource.__getattribute__(self, attr)

    # override to handle special case of state
    def __setattr__(self, attr, value):
        if attr == "state":
            self.setState(value)
        else:
            Resource.__setattr__(self, attr, value)

    # dictionary of pertinent attributes
    def dict(self, expand=False):
        return {"name":self.name,
                "interface":(self.interface.name if self.interface else None),
                "addr":self.addr,
                "type":self.type,
                "resolution": self.resolution,
                "pollInterval": self.pollInterval,
                "persistence": (self.persistence.name if self.persistence else None),
                "location":self.location,
                "group":self.group,
                "label":self.label}

# A Control is a Sensor whose state can be set
class Control(Sensor):
    def __init__(self, name, interface=None, addr=None, type="control",
                 resolution=0, pollInterval=1, event=None, persistence=None,
                 location=None, group="", label=None):
        Sensor.__init__(self, name, interface=interface, addr=addr, type=type,
                        resolution=resolution, pollInterval=pollInterval, event=event, persistence=persistence,
                        location=location, group=group, label=label)

    # Set the state of the control by writing the value to the address on the interface.
    def setState(self, state, wait=False):
        debug('debugState', "Control", self.name, "setState ", state)
        self.interface.write(self.addr, state)
        self.notify(state)
        return True
