# Classes related to schedules

from basic import *
from sunriseset import *

# day of week identifiers
Mon = 0
Tue = 1
Wed = 2
Thu = 3
Fri = 4
Sat = 5
Sun = 6
weekdayTbl = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

# month identifiers
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
monthTbl = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# return today's and tomorrow's dates
def todaysDate():
    today = datetime.datetime.now().replace(tzinfo=tz.tzlocal())
    tomorrow = today + datetime.timedelta(days=1)
    return (today, tomorrow)

# the Scheduler manages a list of Tasks and runs them at the times specified
class Schedule(Collection):
    objectArgs = ["tasks"]
    def __init__(self, name, tasks=[]):
        Collection.__init__(self, name, resources=tasks)
        self.type = "schedule"
        self.schedThread = threading.Thread(target=self.doSchedule)

    def start(self):
        self.schedThread.start()

    def getState(self):
        return 1
        
    def addRes(self, resource):
        Collection.addRes(self, resource)
        if resource.schedTime.event != "":
            # if an event is specified, add a child task with a specific date and time
            self.addRes(resource.child())
            debug('debugEvent', self.name, "adding", resource.child().__str__())
        
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
                                                if task.resources:      # control is resource name
                                                    try:
                                                        debug('debugEvent', self.name, "resolving", task.control)
                                                        control = task.resources[task.control]
                                                    except KeyError:    # can't resolve so ignore it
                                                        control = None
                                                else:                   # control is resource reference
                                                    control = task.control
                                                if control:
                                                    debug('debugEvent', self.name, "setting", control.name, "state", task.controlState)
                                                    control.setState(task.controlState)
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
class Task(Control):
    objectArgs =["interface", "event", "schedTime", "control"]
    def __init__(self, name, schedTime=None, control=None, controlState=0, resources=None, parent=None, enabled=True, interface=None, addr=None, 
                 type="task", group="Tasks", view=None, label=""):
        Control.__init__(self, name, interface, addr, group=group, type=type, view=view, label=label)
        self.schedTime = schedTime
        self.control = control
        self.controlState = controlState
        self.resources = resources
        self.parent = parent
        self.enabled = normalState(enabled)

    def getState(self):
        if self.interface.name == "None":
            return self.enabled
        else:
            return Control.getState(self)

    def setState(self, theValue):
        if self.interface.name == "None":
            self.enabled = theValue
            return True
        else:
            return Control.setState(self, theValue)

    # create a child task for the event on a specific date and time
    def child(self):
        schedTime = copy.copy(self.schedTime)
        schedTime.eventTime(latLong)
        schedTime.event = ""
        schedTime.lastTime()
        return Task(self.name+"Event", schedTime, self.control, self.controlState, resources=self.resources, parent=self)
        
    # dictionary of pertinent attributes
    def dict(self):
        if self.resources:      # control is resource name - FIXME - test list element type
            try:
                control = self.resources[self.control]
            except KeyError:    # can't resolve so ignore it
                control = "None"
        else:                   # control is resource reference
            control = self.control    
        return {"class":self.__class__.__name__, 
                "name":self.name, 
                "type": self.type, 
                "control":control.name, 
                "controlState":self.controlState, 
                "schedTime": self.schedTime.dict()}
                    
    def __str__(self, views=None):
        try:
            if self.resources:      # control is resource name - FIXME - test list element type
                control = self.resources[self.control]
                controlName = control.name
            else:                   # control is resource reference
                control = self.control
                controlName = control.name
        except (AttributeError, KeyError):    # can't resolve so use the name
            control = None
            controlName = self.control
        try:                    # try to translate state value
            value = control.setValues(views)[self.controlState]
        except AttributeError:                 # use the value
            value = str(self.controlState)
        return controlName+": "+value+","+self.schedTime.__str__()

    def __del__(self):
        del(self.schedTime)

# Schedule Time defines a date and time to perform a task.
# Year, month, day, hour, minute, and weekday may be specified as a list of zero or more values.
# Relative dates of "today" or "tomorrow" and events of "sunrise" or "sunset" may also be specified.
# If an event and a time (hours, minutes) are specified, the time is considered to be a delta from the event
# and may contain negative values.
class SchedTime(object):
    def __init__(self, year=[], month=[], day=[], hour=[], minute=[], weekday=[], date="", event="", name=""):
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

    def offsetEventTime(self, eventTime):
        # offset by delta time if hours or minutes are specified
        deltaMinutes = 0
        if self.hour != []:
            deltaMinutes += self.hour[0]*60
        if self.minute != []:
            deltaMinutes += self.minute[0]
        return eventTime + datetime.timedelta(minutes=deltaMinutes)
    
    # determine the specific time of the next occurrence of an event
    def eventTime(self, latLong):
        eventTbl = {"sunrise": sunrise,
                    "sunset": sunset}
        (today, tomorrow) = todaysDate()
        if (self.year != []) and (self.month != []) and (self.day != []):
            eventTime = self.offsetEventTime(eventTbl[self.event](datetime.date(self.year[0], self.month[0], self.day[0]), latLong))
        else:
            # use today's event time
            eventTime = self.offsetEventTime(eventTbl[self.event](today, latLong))
            if (eventTime <= today) and (self.day == []):
                # use tomorrow's time if today's time was in the past
                eventTime = self.offsetEventTime(eventTbl[self.event](tomorrow, latLong))
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
    
    # return string version of months
    def months(self):
        ms = []
        for m in self.month:
            ms += [monthTbl[m-1]]
        return ms
    
    # return the expanded list of all occurrences of the schedTime
    def enumTimes(self):
        events = [""]
        events = self.enumElem(self.year, events, "", 4, "d")
        events = self.enumElem(self.months(), events, "-", 3, "s")
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
  
