import time
import datetime
import threading
import copy
import syslog
from collections import OrderedDict
from dateutil import tz
from ha.sunriseset import *
from ha.HAConf import *

def log(*args):
    message = args[0]+" "
    for arg in args[1:]:
        message += arg.__str__()+" "
    if sysLogging:
        syslog.syslog(message)
    else:
        print message

# normalize state values from boolean to integers
def normalState(value):
    if value == True: return 1
    elif value == False: return 0
    else: return value
    
# Base class for Resources
class HAResource(object):
    def __init__(self, theName):
        self.name = theName
        if debugObject: log(self.name, "created")
        self.className = self.__class__.__name__    # hack for web templates - FIXME

    def __str__(self, level=0):
        return self.name+" "+self.__class__.__name__

# Base class for Interfaces 
class HAInterface(HAResource):
    def __init__(self, theName, theInterface=None):
        HAResource.__init__(self, theName)
        self.interface = theInterface

    def start(self):
        return True
        
    def stop(self):
        return True
        
    def read(self, theAddr):
        return True
        
    def write(self, theAddr, theValue):
        return True

# Resource collection 

# todo
# - load tree
# - gets traverse tree
# - delete collection
# - lock
       
class HACollection(HAResource, OrderedDict):
    def __init__(self, theName):
        HAResource.__init__(self, theName)
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
            resList.append(self.__getitem__(name))
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
        if debugRest:
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
                    theInterface=interface, theAddr=path+"/state"))
            elif node["class"] == "HAScene":
                self.addRes(HAScene(node["name"], [], group=node["group"], type=node["type"], label=node["label"], 
                    theInterface=interface, theAddr=path+"/state"))
            elif node["class"] == "HATask":
                self.addRes(HATask(node["name"], theControl=self[node["control"]], theState=node["controlState"], 
                    theSchedTime=HASchedTime(**node["schedTime"]), 
                    theInterface=interface, theAddr=path+"/state",))
        except:
            pass

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
        for resource in self.values():
            msg += "\n"+"    "*(level+1)+resource.__str__(level+1)
        return msg

# A Sensor represents a device that has a state that is represented by a scalar value.
# The state is associated with a unique address on an interface.
# Sensors can also optionally be associated with a group and a physical location.
class HASensor(HAResource):
    def __init__(self, theName, theInterface, theAddr=None, group="", type="sensor", location=None, label="", view=None):
        HAResource.__init__(self, theName)
        self.type = type
        self.interface = theInterface
        self.addr = theAddr
        if self.addr == None:
            self.addr = self.name
        self.group = group
        if label == "":
            self.label = self.name
        else:
            self.label = label
        self.location = location
        if view == None:
            self.view = HAView({0:"Off", 1:"On"}, "%s")
        else:
            self.view = view
        self.__dict__["state"] = None   # dummy class variable so hasattr() returns True

    # Return the state of the sensor by reading the value from the address on the interface.
    def getState(self):
        return self.interface.read(self.addr)

    # Return the printable string value for the state of the sensor
    def getViewState(self):
        return self.view.getViewState(self)

    # Define this function for sensors even though it does nothing        
    def setState(self, theState, wait=False):
        return False

    # override to handle special case of state
    def __getattribute__(self, attr):
        if attr == "state":
            return self.getState()
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
    def __init__(self, values={0:"Off", 1:"On"}, format="%s", transform=None, setValues=None):
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
    def __init__(self, theName, theInterface, theAddr=None, group="", type="control", location=None, view=None, label=""):
        HASensor.__init__(self, theName, theInterface, theAddr, group=group, type=type, location=location, view=view, label=label)
        self.running = False

    # Set the state of the control by writing the value to the address on the interface.
    def setState(self, theState, wait=False):
        if debugState: log(self.name, "setState ", theState)
        self.interface.write(self.addr, theState)
        return True

    # Set the state of the control to the state value corresponding to the specified display value
    def setViewState(self, theValue):
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
                            
# a Sequence is a Control that consists of a set of Cycles that are run in the specified order
class HASequence(HAControl):
    def __init__(self, theName, theCycleList, theInterface=HAInterface("None"), theAddr=None, group="", type="sequence", view=None, label=""):
        HAControl.__init__(self, theName, theInterface, theAddr, group=group, type=type, view=view, label=label)
        self.cycleList = theCycleList
        self.running = False

    def getState(self):
        if self.interface.name == "None":
            return normalState(self.running)
        else:
            return HAControl.getState(self)
        
    def setState(self, theState, wait=False):
        if self.interface.name == "None":
            if debugState: log(self.name, "setState ", theState)
            if theState and not(self.running):
                self.runCycle(wait)
            elif (not theState) and self.running:
                self.stopCycle()
            return True
        else:
            return HAControl.setState(self, theState)
            
    def runCycle(self, wait=False):
    # Run the list of Cycles
        if debugState: log(self.name, "runCycle ")
        if wait:
            # Run it synchronously.
            self.doCycle()
        else:
            # Run it asynchronously in a separate thread.
            self.cycleThread = threading.Thread(target=self.doCycle)
            self.cycleThread.start()

    def stopCycle(self):
        if debugThread: log(self.name, "stopped")
        self.running = False
        for cycle in self.cycleList:
            cycle.control.setState(cycle.endState)
        
    def doCycle(self):
        if debugThread: log(self.name, "started")
        self.running = True
        for cycle in self.cycleList:
            if not self.running:
                break
            self.controlCycle(cycle)
        self.running = False
        if debugThread: log(self.name, "finished")

    # wait the specified number of seconds
    # break immediately if the sequence is stopped
    def wait(self, duration):
        for seconds in range(0, duration):
            if not self.running:
                break
            time.sleep(1)
    
    def controlCycle(self, cycle):
    # Run the specified Cycle
        if debugThread: log(self.name, cycle.control.name, "started")
        if cycle.delay > 0:
            if debugThread: log(self.name, "delaying", cycle.delay)
            self.wait(cycle.delay)
            if not self.running:
                return
        cycle.control.setState(cycle.startState)
        if cycle.duration > 0:
            self.wait(cycle.duration)
            cycle.control.setState(cycle.endState)
        if debugThread: log(self.name, cycle.control.name, "finished")

    def __str__(self):
        msg = ""
        for cycle in self.cycleList:
            msg += cycle.__str__()+"\n"
        return msg
            
# A Scene is a set of Controls whose state can be changed together
class HAScene(HAControl):
    def __init__(self, theName, theControlList, theStateList=[], theInterface=HAInterface("None"), theAddr=None, group="", type="scene", view=None, label=""):
        HAControl.__init__(self, theName, theInterface, theAddr, group=group, type=type, view=view, label=label)
        self.controlList = theControlList
        self.sceneState = 0
        if theStateList == []:
            self.stateList = [[0,1]]*(len(self.controlList))
        else:
            self.stateList = theStateList

    def setState(self, theState, wait=False):
        if self.interface.name == "None":
            if debugState: log(self.name, "setState ", theState)
            self.sceneState = theState  # use Cycle - FIXME
            # Run it asynchronously in a separate thread.
            self.sceneThread = threading.Thread(target=self.doScene)
            self.sceneThread.start()
            return True
        else:
            return HAControl.setState(self, theState)

    def getState(self):
        if self.interface.name == "None":
            return self.sceneState
        else:
            return HAControl.getState(self)

    def doScene(self):
        if debugThread: log(self.name, "started")
        self.running = True
        for controlIdx in range(len(self.controlList)):
            self.controlList[controlIdx].setState(self.stateList[controlIdx][self.sceneState])
        self.running = False
        if debugThread: log(self.name, "finished")

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
    def __init__(self, theName):
        HACollection.__init__(self, theName)
        self.type = "schedule"
        self.schedThread = threading.Thread(target=self.doSchedule)

    def start(self):
        self.schedThread.start()

    def addRes(self, resource):
        HACollection.addRes(self, resource)
        if resource.schedTime.event != "":
            # if an event is specified, add a child task with a specific date and time
            self.addRes(resource.child())
        
    # add a task to the scheduler list
    def addTask(self, theTask):
        self.addRes(theTask)
        if debugEvent: log(self.name, "adding", theTask.__str__())

    # delete a task from the scheduler list
    def delTask(self, taskName):
        self.delRes(taskName)
        if debugEvent: log(self.name, "deleting", taskName)

    # Scheduler thread
    def doSchedule(self):
        if debugThread: log(self.name, "started")
        while True:
            # wake up every minute on the 00 second
            (now, tomorrow) = todaysDate()
            sleepTime = 60 - now.second
            if debugSched: log(self.name, "sleeping ", sleepTime)
            time.sleep(sleepTime)
#            if not running:
#                break
            (now, tomorrow) = todaysDate()
            if debugSched: log(self.name, "waking up", now)
            # run through the schedule and check if any tasks should be run
            # need to handle cases where the schedule could be modified while this is running - FIXME
            for taskName in self.keys():
                if debugSched: log(self.name, "checking ", taskName)
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
                                                if debugEvent: log(self.name, "running", taskName)
                                                task.control.setState(task.controlState)
                if task.schedTime.last:
                    if task.schedTime.last <= now:
                        # delete the task from the schedule if it will never run again
                        self.delTask(taskName)
                        # reschedule the next occurrence if the task was a child of an event task
                        if task.parent:
                            self.addTask(task.parent.child())
                        del(task)
            if debugSched: log(self.name, self.__str__())

# a Task specifies a control to be set to a specified state at a specified time
class HATask(HAControl):
    def __init__(self, theName, theSchedTime, theControl, theState, theParent=None, enabled=True, theInterface=HAInterface("None"), theAddr=None, type="task", group="Tasks", view=None, label=""):
        HAControl.__init__(self, theName, theInterface, theAddr, group=group, type=type, view=view, label=label)
        self.schedTime = theSchedTime
        self.control = theControl
        self.controlState = theState
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
     
