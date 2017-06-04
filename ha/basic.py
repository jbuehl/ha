# Basic class definitions

stateChangeInterval = 10
running = True  # FIXME - get rid of this

import time
import threading
import copy
import sys
from collections import OrderedDict
from config import *
from environment import *
from logging import *
from debugging import *

# normalize state values from boolean to integers
def normalState(value):
    if value == True: return 1
    elif value == False: return 0
    else: return value
    
# Base class for Resources
class Resource(object):
    def __init__(self, name):
        try:
            if self.name:   # init has already been called for this object
                return
        except AttributeError:
            self.name = name
            debug('debugObject', self.name, "created")
            self.className = self.__class__.__name__    # hack for web templates - FIXME

    def __str__(self, level=0):
        return self.name+" "+self.__class__.__name__

# Base class for Interfaces 
class Interface(Resource):
    objectArgs = ["interface", "event"]
    def __init__(self, name, interface=None, event=None, persistence=None):
        Resource.__init__(self, name)
        self.interface = interface
        # optional sensor state persistence layer
        self.persistence = persistence
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
        if self.persistence:
            self.persistence.start()
        return True
        
    def stop(self):
        if self.persistence:
            self.persistence.stop()
        return True
        
    def read(self, addr):
        return False
        
    def write(self, addr, theValue):
        return True

    def addSensor(self, sensor):
        debug('debugObject', self.name, "sensor", sensor.name)
        self.sensors[sensor.name] = sensor
        self.sensorAddrs[sensor.addr] = sensor
        self.states[sensor.addr] = 0 # None - FIXME
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
# - lock
       
class Collection(Resource, OrderedDict):
    objectArgs = ["resources"]
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
    def getGroup(self, theGroup):
        resourceList = []
        for resourceName in self.keys():
            resource = self.__getitem__(resourceName)
            if resource.group == theGroup:
                resourceList.append(resource)
        return resourceList

    # dictionary of pertinent attributes
    def dict(self):
        return {"class":self.__class__.__name__, 
                "name":self.name, 
                "type": self.type, 
                "resources":self.keys()}
                    
    def __str__(self, level=0):
        msg = self.name+" "+self.__class__.__name__
#        for resource in self.values():
#            msg += "\n"+"    "*(level+1)+resource.__str__(level+1)
        return msg

# A Sensor represents a device that has a state that is represented by a scalar value.
# The state is associated with a unique address on an interface.
# Sensors can also optionally be associated with a group and a physical location.
class Sensor(Resource):
    objectArgs = ["interface", "event"]
    def __init__(self, name, interface=None, addr=None, group="", type="sensor", location=None, label="", view=None, interrupt=None, event=None):
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
            if view == None:
                self.view = View()
            else:
                self.view = view
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
        return self.interface.read(self.addr)

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
        
    # Return the printable string value for the state of the sensor
    def getViewState(self, views=None):
        try:
            return views[self.type].getViewState(self)
        except:
            return self.view.getViewState(self)

    # Return the printable string values for the states that can be set on the sensor
    def setValues(self, views=None):
        try:
            return views[self.type].setValues
        except:
            return self.view.setValues

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
                    
# A View describes how the value of a sensor's state should be displayed.  It contains a mapping of
# state values to display values, an optional format string, and an optional transform function.
# Reverse mappings of display values to state values may also be specified.
class View(object):
    def __init__(self, values={None:"", 0:"Off", 1:"On"}, format="%s", transform=None, setValues=None, toggle=False):
        self.values = values
        self.format = format
        self.transform = transform
        if setValues == None:
            self.setValues = {0:"Off", 1:"On"}
        else:
            self.setValues = OrderedDict(setValues) # preserve the order of set values for display purposes
        self.toggle = toggle
 
    # Return the printable string value for the state of the sensor
    def getViewState(self, theSensor):
        state = theSensor.getState()
        try:    # run it through the transformation function
            state = self.transform(state)
        except:
            pass
        try:    # look it up in the values table
            return self.format % (self.values[state])
        except:
            try:    # apply the format
                return self.format % (state)
            except: # worst case, return the string of the state
                return str(state)

    # Set the state of the control to the state value corresponding to the specified display value
    def setViewState(self, control, dispValue):
        try:
            value = self.setValues.keys()[self.setValues.values().index(dispValue)]
            if dispValue in ["-", "v", "+", "^"]:   # increment or decrement current state by the value
                control.setState(control.getState() + value)
            else:                                   # set it to the value
                control.setState(value)
        except:
            control.setState(0)

# A Control is a Sensor whose state can be set        
class Control(Sensor):
    objectArgs = ["interface", "event"]
    def __init__(self, name, interface, addr=None, group="", type="control", location=None, view=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt, event=event)
        self.running = False

    # Set the state of the control by writing the value to the address on the interface.
    def setState(self, state, wait=False):
        debug('debugState', self.name, "setState ", state)
        self.interface.write(self.addr, state)
        self.notify()
        return True

    # Set the state of the control to the state value corresponding to the specified display value
    def setViewState(self, theValue, views=None):
        try:
            return views[self.type].setViewState(self, theValue)
        except:
            return self.view.setViewState(self, theValue)
 
