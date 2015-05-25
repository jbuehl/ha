import time
import datetime
import threading
import copy
import syslog
import sys
import os
from collections import OrderedDict
from dateutil import tz
from ha.sunriseset import *
from ha.HAConf import *

# log a message
def log(*args):
    message = args[0]+" "   # first argument is the object doing the logging
    for arg in args[1:]:
        message += arg.__str__()+" "
    if sysLogging:
        syslog.syslog(message)
    else:
        print message

# log a debug message
def debug(*args):
    if debugEnable:   # global debug flag enables debugging
        try:
            if globals()[args[0]]:
                log(*args[1:])
        except:
            pass
            
# read configuration files
for configFileName in os.listdir(configDir):
    debug('debugConf', "config open", configFileName)
    try:
        with open(configDir+configFileName) as configFile:
            configLines = [configLine.rstrip('\n') for configLine in configFile]
        for configLine in configLines:
            if (len(configLine) > 0) and (configLine[0] != "#"):
                try:
                    exec(configLine)
                    debug('debugConf', "config read", configLine)
                except:
                    log("config", "error evaluating", configLine)
    except:
        log("config", "error reading", configDir+configFileName)
        
# normalize state values from boolean to integers
def normalState(value):
    if value == True: return 1
    elif value == False: return 0
    else: return value
    
# Base class for Resources
class HAResource(object):
    def __init__(self, name):
        self.name = name
        debug('debugObject', self.name, "created")
        self.className = self.__class__.__name__    # hack for web templates - FIXME

    def __str__(self, level=0):
        return self.name+" "+self.__class__.__name__

# Base class for Interfaces 
class HAInterface(HAResource):
    def __init__(self, name, interface=None, event=None, persistence=None):
        HAResource.__init__(self, name)
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
        debug('debugInterrupt', self.name, "event", self.event)
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
        return True
        
    def write(self, addr, theValue):
        return True

    def addSensor(self, sensor):
        debug('debugObject', self.name, "sensor", sensor.name)
        self.sensors[sensor.name] = sensor
        self.sensorAddrs[sensor.addr] = sensor
        self.states[sensor.addr] = 0
        sensor.event = self.event
        
    # return the data type of the state of the specified sensor
    def getStateType(self, sensor):
        return int
        
    # Trigger the sending of a state change notification
    def notify(self):
        if self.event:
            self.event.set()
            debug('debugInterrupt', self.name, "event set")
        
# Resource collection 

# todo
# - load tree
# - gets traverse tree
# - delete collection
# - lock
       
class HACollection(HAResource, OrderedDict):
    def __init__(self, name):
        HAResource.__init__(self, name)
        OrderedDict.__init__(self)
        self.type = "collection"
        self.lock = threading.Lock()

    # Add a resource to the table
    def addRes(self, resource):
        self.__setitem__(resource.name, resource)

    # Delete a resource from the table
    def delRes(self, name):
        self.__delitem__(name)

    # Return the list of resources that have the names specified in the list
    def getResList(self, names):
        resList = []
        for name in names:
            try:
                resList.append(self.__getitem__(name))
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

    # load resources from the specified interface
    # this does not replicate the collection hierarchy being read
    def load(self, interface, path, views={}, level=0):
        node = interface.read(path)
        if debugRestResources:
            if node != {}:
                log("    "*(level)+node["name"])
                for attr in node.keys():
                    if (attr != "name") and (attr != "resources"):
                        log("    "*(level+1)+attr+": "+node[attr].__str__())
        self.loadResource(interface, node, path)
        if "resources" in node.keys():
            # the node is a collection
            for resource in node["resources"]:
                self.load(interface, path+"/"+resource, level+1)

    # instantiate the resource from the specified node            
    def loadResource(self, interface, node, path):
        try:
            if node["class"] == "HASensor":
                self.addRes(HASensor(node["name"], interface, path+"/state", group=node["group"], type=node["type"], 
                    location=node["location"], label=node["label"]))
            elif node["class"] == "HAControl":
                self.addRes(HAControl(node["name"], interface, path+"/state", group=node["group"], type=node["type"], 
                    location=node["location"], label=node["label"]))
            elif node["class"] == "HASequence":
                self.addRes(HASequence(node["name"], [], group=node["group"], type=node["type"], label=node["label"], 
                    interface=interface, addr=path+"/state"))
            elif node["class"] == "HAScene":
                self.addRes(HAScene(node["name"], [], group=node["group"], type=node["type"], label=node["label"], 
                    interface=interface, addr=path+"/state"))
            elif node["class"] == "HATask":
                self.addRes(HATask(node["name"], control=self[node["control"]], state=node["controlState"], 
                    schedTime=HASchedTime(**node["schedTime"]), 
                    interface=interface, addr=path+"/state",))
            else:
                debug('debug', self.name, "loadResource", node["name"], "class", node["class"], "not created")
        except:
            debug('debug', self.name, "loadResource", node["name"], "class", node["class"], "not created")

    # add Views to each resource
    def addViews(self, views):            
        for resource in self.values():
            try:
                resource.view = views[resource.type]
            except:
                pass
            
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
class HASensor(HAResource):
    def __init__(self, name, interface, addr=None, group="", type="sensor", location=None, label="", view=None, interrupt=None, event=None):
        HAResource.__init__(self, name)
        self.type = type
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
            self.view = HAView()
        else:
            self.view = view
        if self.interface:
            self.interface.addSensor(self)
        self.interrupt = interrupt
        if event:
            self.event = event
        debug('debugInterrupt', self.name, "event")
        self.__dict__["state"] = None   # dummy class variable so hasattr() returns True
        self.__dict__["stateChange"] = None   # dummy class variable so hasattr() returns True

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
            debug('debugInterrupt', self.name, "event clear")
            self.event.wait()
            debug('debugInterrupt', self.name, "event wait")
        return self.getState()

    # Trigger the sending of a state change notification
    def notify(self):
        if self.event:
            self.event.set()
            debug('debugInterrupt', self.name, "event set")
        
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
            return HAResource.__getattribute__(self, attr)
            
    # override to handle special case of state
    def __setattr__(self, attr, value):
        if attr == "state":
            self.setState(value)
        else:
            HAResource.__setattr__(self, attr, value)

    # dictionary of pertinent attributes
    def dict(self):
        return {"class":self.__class__.__name__, 
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
class HAView(object):
    def __init__(self, values={None:"", 0:"Off", 1:"On"}, format="%s", transform=None, setValues={0:"Off", 1:"On"}):
        self.values = values
        self.format = format
        self.transform = transform
        if setValues == None:
            self.setValues = self.values
        else:
            self.setValues = setValues
 
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
    def setViewState(self, theControl, theValue):
        try:
            theControl.setState(self.setValues.keys()[self.setValues.values().index(theValue)])
        except:
            theControl.setState(0)

# A Control is a Sensor whose state can be set        
class HAControl(HASensor):
    def __init__(self, name, interface, addr=None, group="", type="control", location=None, view=None, label="", interrupt=None, event=None):
        HASensor.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt, event=event)
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

# A Cycle describes the process of setting a Control to a specified state, waiting a specified length of time,
# and setting the Control to another state.  This may be preceded by an optional delay.
# If the duration is zero, then the end state is not set and the Control is left in the start state.
class HACycle(object):
    def __init__(self, theControl, duration, delay=0, startState=1, endState=0):
        self.control = theControl
        self.duration = duration
        self.delay = delay
        self.startState = normalState(startState)
        self.endState = normalState(endState)

    def __str__(self):
        return self.control.name+" "+self.duration.__str__()+" "+self.delay.__str__()+" "+self.startState.__str__()+" "+self.endState.__str__()
                            
# a Sequence is a Control that consists of a list of Cycles that are run in the specified order
class HASequence(HAControl):
    def __init__(self, name, cycleList, addr=None, interface=HAInterface("None"), event=None, group="", type="sequence", view=None, label=""):
        HAControl.__init__(self, name, addr=addr, interface=interface, event=event, group=group, type=type, view=view, label=label)
        self.cycleList = cycleList
        self.running = False

    def getState(self):
        if self.interface.name == "None":
            return normalState(self.running)
        else:
            return HAControl.getState(self)
        
    def setState(self, state, wait=False):
        if self.interface.name == "None":
            debug('debugState', self.name, "setState ", state, wait)
            if state and not(self.running):
                self.runCycles(wait)
            elif (not state) and self.running:
                self.stopCycles()
            return True
        else:
            return HAControl.setState(self, state)
            
    # Run the Cycles in the list
    def runCycles(self, wait=False):
        debug('debugState', self.name, "runCycles", wait)
        # thread that runs the cycles
        def runCycles():
            debug('debugThread', self.name, "started")
            self.running = True
            for cycle in self.cycleList:
                if not self.running:
                    break
                self.runCycle(cycle)
            self.running = False
            self.notify()
            debug('debugThread', self.name, "finished")
        if wait:    # Run it synchronously
            runCycles()
        else:       # Run it asynchronously in a separate thread
            self.cycleThread = threading.Thread(target=runCycles)
            self.cycleThread.start()

    # Stop all Cycles in the list
    def stopCycles(self):
        self.running = False
        for cycle in self.cycleList:
            cycle.control.setState(cycle.endState)
        self.notify()
        debug('debugThread', self.name, "stopped")

    # state change notification to all control events since the sequence doean't have an event
    def notify(self):
        time.sleep(2)   # short delay to ensure the state change event for the sequence isn't missed
        for cycle in self.cycleList:
            cycle.control.notify()

    # Run the specified Cycle
    def runCycle(self, cycle):
        if cycle.delay > 0:
            debug('debugThread', self.name, cycle.control.name, "delaying", cycle.delay)
            self.wait(cycle.delay)
            if not self.running:
                return
        debug('debugThread', self.name, cycle.control.name, "started")
        cycle.control.setState(cycle.startState)
        if cycle.duration > 0:
            self.wait(cycle.duration)
            cycle.control.setState(cycle.endState)
        debug('debugThread', self.name, cycle.control.name, "finished")

    # wait the specified number of seconds
    # break immediately if the sequence is stopped
    def wait(self, duration):
        for seconds in range(0, duration):
            if not self.running:
                break
            time.sleep(1)
    
    def __str__(self):
        msg = ""
        for cycle in self.cycleList:
            msg += cycle.__str__()+"\n"
        return msg
            
# A Scene is a set of Controls whose state can be changed together
class HAScene(HAControl):
    def __init__(self, name, theControlList, stateList=[], interface=HAInterface("None"), addr=None, group="", type="scene", view=None, label=""):
        HAControl.__init__(self, name, interface, addr, group=group, type=type, view=view, label=label)
        self.controlList = theControlList
        self.sceneState = 0
        if stateList == []:
            self.stateList = [[0,1]]*(len(self.controlList))
        else:
            self.stateList = stateList

    def setState(self, state, wait=False):
        if self.interface.name == "None":
            debug('debugState', self.name, "setState ", state)
            self.sceneState = state  # use Cycle - FIXME
            # Run it asynchronously in a separate thread.
            self.sceneThread = threading.Thread(target=self.doScene)
            self.sceneThread.start()
            return True
        else:
            return HAControl.setState(self, state)

    def getState(self):
#        if self.interface.name == "None":
#            return self.sceneState
#        else:
#            return HAControl.getState(self)
        return None

    def doScene(self):
        debug('debugThread', self.name, "started")
        self.running = True
        for controlIdx in range(len(self.controlList)):
            self.controlList[controlIdx].setState(self.stateList[controlIdx][self.sceneState])
        self.running = False
        debug('debugThread', self.name, "finished")

Mon = 0
Tue = 1
Wed = 2
Thu = 3
Fri = 4
Sat = 5
Sun = 6

Jan = 1
Feb = 2
Mar = 3
Apr = 4
May = 5
Jun = 6
Jul = 7
Aug = 8
Sep = 9
Oct = 10
Nov = 11
Dec = 12

weekdayTbl = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

# return today's and tomorrow's dates
def todaysDate():
    today = datetime.datetime.now().replace(tzinfo=tz.tzlocal())
    tomorrow = today + datetime.timedelta(days=1)
    return (today, tomorrow)

# turn an item into a list if it is not already
def listize(x):
    return x if isinstance(x, list) else [x]
                               
# the Scheduler manages a list of Tasks and runs them at the times specified
class HASchedule(HACollection):
    def __init__(self, name):
        HACollection.__init__(self, name)
        self.type = "schedule"
        self.schedThread = threading.Thread(target=self.doSchedule)

    def start(self):
        self.schedThread.start()

    def getState(self):
        return 1
        
    def addRes(self, resource):
        HACollection.addRes(self, resource)
        if resource.schedTime.event != "":
            # if an event is specified, add a child task with a specific date and time
            self.addRes(resource.child())
        
    # add a task to the scheduler list
    def addTask(self, theTask):
        self.addRes(theTask)
        debug('debugEvent', self.name, "adding", theTask.__str__())

    # delete a task from the scheduler list
    def delTask(self, taskName):
        self.delRes(taskName)
        debug('debugEvent', self.name, "deleting", taskName)

    # Scheduler thread
    def doSchedule(self):
        debug('debugThread', self.name, "started")
        while True:
            # wake up every minute on the 00 second
            (now, tomorrow) = todaysDate()
            sleepTime = 60 - now.second
            debug('debugSched', self.name, "sleeping ", sleepTime)
            time.sleep(sleepTime)
#            if not running:
#                break
            (now, tomorrow) = todaysDate()
            debug('debugSched', self.name, "waking up", now)
            # run through the schedule and check if any tasks should be run
            # need to handle cases where the schedule could be modified while this is running - FIXME
            for taskName in self.keys():
                debug('debugSched', self.name, "checking ", taskName)
                task = self[taskName] #self.schedule[taskName]
                # the task should be run if the current date/time matches all specified fields in the SchedTime
                if (task.schedTime.event == ""): # don't run tasks that specify an event
                    if (task.schedTime.year == []) or (now.year in task.schedTime.year):
                        if (task.schedTime.month == []) or (now.month in task.schedTime.month):
                            if (task.schedTime.day == []) or (now.day in task.schedTime.day):
                                if (task.schedTime.hour == []) or (now.hour in task.schedTime.hour):
                                    if (task.schedTime.minute == []) or (now.minute in task.schedTime.minute):
                                        if (task.schedTime.weekday == []) or (now.weekday() in task.schedTime.weekday):
                                            if task.enabled:
                                                # run the task
                                                debug('debugEvent', self.name, "running", taskName)
                                                task.control.setState(task.controlState)
                if task.schedTime.last:
                    if task.schedTime.last <= now:
                        # delete the task from the schedule if it will never run again
                        self.delTask(taskName)
                        # reschedule the next occurrence if the task was a child of an event task
                        if task.parent:
                            self.addTask(task.parent.child())
                        del(task)
            debug('debugSched', self.name, self.__str__())

# a Task specifies a control to be set to a specified state at a specified time
class HATask(HAControl):
    def __init__(self, name, schedTime, control, state, theParent=None, enabled=True, interface=HAInterface("None"), addr=None, type="task", group="Tasks", view=None, label=""):
        HAControl.__init__(self, name, interface, addr, group=group, type=type, view=view, label=label)
        self.schedTime = schedTime
        self.control = control
        self.controlState = state
        self.parent = theParent
        self.enabled = normalState(enabled)

    def getState(self):
        if self.interface.name == "None":
            return self.enabled
        else:
            return HAControl.getState(self)

    def setState(self, theValue):
        if self.interface.name == "None":
            self.enabled = theValue
            return True
        else:
            return HAControl.setState(self, theValue)

    # create a child task for the event on a specific date and time
    def child(self):
        schedTime = copy.copy(self.schedTime)
        schedTime.eventTime(latLong)
        schedTime.event = ""
        schedTime.lastTime()
        return HATask(self.name+" event", schedTime, self.control, self.controlState, self)
        
    # dictionary of pertinent attributes
    def dict(self):
        return {"class":self.__class__.__name__, 
                "name":self.name, 
                "type": self.type, 
                "control":self.control.name, 
                "controlState":self.controlState, 
                "schedTime": self.schedTime.dict()}
                    
    def __str__(self):
        return self.name+" "+self.schedTime.__str__()#+" Control:"+self.control.name+" State:"+self.state.__str__()

    def __del__(self):
        del(self.schedTime)

# Schedule Time defines a time to perform a task.
# Year, month, day, hour, minute, and weekday may be specified as a list of zero or more values.
# Relative dates of "today" or "tomorrow" and events of "sunrise" or "sunset" may also be specified.
class HASchedTime(object):
    def __init__(self, year=[], month=[], day=[], hour=[], minute=[], weekday=[], date="", event=""):
        self.year = listize(year)
        self.month = listize(month)
        self.day = listize(day)
        self.hour = listize(hour)
        self.minute = listize(minute)
        self.weekday = listize(weekday)
        self.date = date
        self.event = event
        if self.date != "":
            self.specificDate()
        self.lastTime()

    # determine the last specific time this will run
    # the schedule time is considered open-ended if any date or time field is unspecified
    # doesn't account for closed-ended tasks where some fields are specified - FIXME
    def lastTime(self):
        if (self.year != []) and (self.month != []) and (self.day != []) and (self.hour != []) and (self.minute != []):
            # determine the last time a closed-ended task will run so the task can be deleted from the schedule
            self.last = datetime.datetime(max(self.year), max(self.month), max(self.day), max(self.hour), max(self.minute), 0).replace(tzinfo=tz.tzlocal())
        else:
            self.last = None

    # determine the specific date of a relative date
    def specificDate(self):
        (today, tomorrow) = todaysDate()
        if self.date == "today":
            self.year = [today.year]
            self.month = [today.month]
            self.day = [today.day]
        elif self.date == "tomorrow":
            self.year = [tomorrow.year]
            self.month = [tomorrow.month]
            self.day = [tomorrow.day]

    # determine the specific time of the next occurrence of an event
    def eventTime(self, latLong):
        eventTbl = {"sunrise": sunrise,
                    "sunset": sunset}
        (today, tomorrow) = todaysDate()
        if (self.year != []) and (self.month != []) and (self.day != []):
            eventTime = eventTbl[self.event](datetime.date(self.year[0], self.month[0], self.day[0]), latLong)
        else:
            # use today's event time
            eventTime = eventTbl[self.event](today, latLong)
            if (eventTime <= today) and (self.day == []):
                # use tomorrow's time if today's time was in the past
                eventTime = eventTbl[self.event](tomorrow, latLong)
            self.year = [eventTime.year]
            self.month = [eventTime.month]
            self.day = [eventTime.day]
        self.hour = [eventTime.hour]
        self.minute = [eventTime.minute]

    # dictionary of pertinent attributes
    def dict(self):
        return {"year":self.year, 
                "month":self.month, 
                "day":self.day, 
                "hour":self.hour, 
                "minute":self.minute, 
                "weekday":self.weekday, 
                "event":self.event}

    # return string version of weekdays
    def weekdays(self):
        wds = []
        for wd in self.weekday:
            wds += [weekdayTbl[wd]]
        return wds
    
    # return the expanded list of all occurrences of the schedTime
    def enumTimes(self):
        events = [""]
        events = self.enumElem(self.year, events, "", 4, "d")
        events = self.enumElem(self.month, events, "-", 2, "d")
        events = self.enumElem(self.day, events, "-", 2, "d")
        events = self.enumElem(self.hour, events, " ", 2, "d")
        events = self.enumElem(self.minute, events, ":", 2, "d")
        events = self.enumElem(self.weekdays(), events, " ", 3, "s")
        events = self.enumElem([self.date], events, " ", 0, "s")
        events = self.enumElem([self.event], events, " ", 0, "s")
        return events

    # append a value to the element list for each occurrence of the specified element
    def enumElem(self, elems, events, delim, length, fmt):
        newEvents = []
        format = "%0"+str(length)+fmt
        if elems == []:
            for event in events:
                newEvents += [event+delim+"*"*(length)]
        else:
            for elem in elems:
                for event in events:
                    newEvents += [event+delim+format%elem]
        return newEvents
                    
    def __str__(self):
        events = self.enumTimes()
        msg = ""
        for event in events:
            msg += event+","
        return msg.rstrip(",")
     
