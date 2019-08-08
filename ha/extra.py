# Extra class definitions derived from basic classes

from basic import *

# A Cycle describes the process of setting a Control to a specified state, waiting a specified length of time,
# and setting the Control to another state.  This may be preceded by an optional delay.
# If the duration is zero, then the end state is not set and the Control is left in the start state.
class Cycle(object):
    objectArgs = ["control"]
    def __init__(self, control=None, duration=0, delay=0, startState=1, endState=0, name=None):
        self.control = control
        self.duration = duration
        self.delay = delay
        self.startState = normalState(startState)
        self.endState = normalState(endState)

    def __str__(self):
        return self.control.name+" "+self.duration.__str__()+" "+self.delay.__str__()+" "+self.startState.__str__()+" "+self.endState.__str__()

# a Sequence is a Control that consists of a list of Cycles or Sequences that are run in the specified order

sequenceStop = 0
sequenceStart = 1
sequenceStopped = 0
sequenceRunning = 1

class Sequence(Control):
    objectArgs = ["interface", "event", "cycleList"]
    def __init__(self, name, cycleList=[], addr=None, interface=None, event=None, group="", type="sequence", label="", location=None):
        Control.__init__(self, name, addr=addr, interface=interface, event=event, group=group, type=type, label=label, location=location)
        self.cycleList = cycleList
        self.cycleList = self.getCycles()   # convert possible Sequences to Cycles
        self.running = False

    # if the list of Cycles contains Sequences, convert to Cycles
    def getCycles(self):
        cycleList = []
        for obj in self.cycleList:
            if isinstance(obj, Cycle):
                cycleList.append(obj)
            elif isinstance(obj, Sequence):
                cycleList += obj.getCycles()
        return cycleList

    def getState(self):
        if self.interface.name == "None":
            return normalState(self.running)
        else:
            return Control.getState(self)

    def setState(self, state, wait=False):
        if self.interface.name == "None":
            debug('debugState', self.name, "setState ", state, wait)
            if state and not(self.running):
                self.runCycles(wait)
            elif (not state) and self.running:
                self.stopCycles()
            return True
        else:
            return Control.setState(self, state)

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
        if isinstance(cycle.duration, int):         # duration is specified directly
            duration = cycle.duration
        elif isinstance(cycle.duration, Sensor):    # duration is a sensor
            duration = cycle.duration.getState()
        if duration > 0:
            self.wait(duration)
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

# A collection of sensors whose state is on if any one of them is on
class SensorGroup(Sensor):
    objectArgs = ["interface", "event", "sensorList", "resources"]
    def __init__(self, name, sensorList, resources=None, interface=None, addr=None, group="", type="sensor", label=""):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, label=label)
        self.sensorList = sensorList
        self.resources = resources  # if specified, sensorList contains resource names, otherwise references
        self.className = "Sensor"

    def getState(self):
        groupState = 0
        for sensorIdx in range(len(self.sensorList)):
            if self.resources:      # sensors are resource names - FIXME - test list element type
                sensorName = self.sensorList[sensorIdx]
                try:
                    sensorState = self.resources.getRes(self.sensorList[sensorIdx]).getState()
                except KeyError:    # can't resolve so ignore it
                    sensorState = 0
            else:                   # sensors are resource references
                try:
                    sensorName = self.sensorList[sensorIdx].name
                    sensorState = self.sensorList[sensorIdx].getState()
                except AttributeError:
                    sensorName = ""
                    sensorState = 0
            debug("debugSensorGroup", self.name, "sensor:", sensorName, "state:", sensorState)
            if sensorState:
                groupState = groupState or sensorState    # group is on if any one sensor is on
        return groupState

# A set of Controls whose state can be changed together
class ControlGroup(SensorGroup, Control):
    objectArgs = ["interface", "event", "controlList", "resources"]
    def __init__(self, name, controlList, stateList=[], resources=None, stateMode=False, interface=None, addr=None,
                 group="", type="controlGroup", label=""):
        SensorGroup.__init__(self, name, controlList, resources, interface, addr, group=group, type=type, label=label)
        Control.__init__(self, name, interface, addr, group=group, type=type, label=label)
        self.stateMode = stateMode  # which state to return: False = SensorGroup, True = groupState
        self.groupState = 0
        if stateList == []:
            self.stateList = [[0,1]]*(len(self.sensorList))
        else:
            self.stateList = stateList
        self.className = "Control"

    def setState(self, state, wait=False):
        if self.interface.name == "None":
            debug('debugState', self.name, "setState ", state)
            self.groupState = state  # use Cycle - FIXME
            # Run it asynchronously in a separate thread.
            def setGroup():
                debug('debugThread', self.name, "started")
                self.running = True
                for controlIdx in range(len(self.sensorList)):
                    if self.resources:      # controls are resource names - FIXME - test list element type
                        try:
                            debug("debugControlGroup", self.name, "looking up:", self.sensorList[controlIdx])
                            control = self.resources[self.sensorList[controlIdx]]
                        except KeyError:    # can't resolve so ignore it
                            debug("debugControlGroup", self.name, "can't find:", self.sensorList[controlIdx])
                            control = None
                    else:                   # controls are resource references
                        control = self.sensorList[controlIdx]
                    if control:
                        debug("debugControlGroup", self.name, "control:", control.name, "state:", self.groupState)
                        control.setState(self.stateList[controlIdx][self.groupState])
                self.running = False
                debug('debugThread', self.name, "finished")
            self.sceneThread = threading.Thread(target=setGroup)
            self.sceneThread.start()
            return True
        else:
            return Control.setState(self, state)

    def getState(self):
        if self.stateMode:
            return self.groupState
        else:
            return SensorGroup.getState(self)

# Calculate a function of a list of sensor states
class CalcSensor(Sensor):
    objectArgs = ["interface", "event", "sensors"]
    def __init__(self, name, sensors=[], function="", interface=None, addr=None, group="", type="sensor", label="", location=None):
        Sensor.__init__(self, name, interface=interface, addr=addr, group=group, type=type, label=label, location=location)
        self.sensors = sensors
        self.function = function.lower()
        self.className = "Sensor"

    def getState(self):
        value = 0
        if (self.function == "sum") or (self.function == "avg"):
            for sensor in self.sensors:
                value += sensor.getState()
            if self.function == "avg":
                value /+ len(self.sensors)
        return value

# Sensor that contains the states of all sensors in a list of resources
class ResourceStateSensor(Sensor):
    objectArgs = ["interface", "event", "resources"]
    def __init__(self, name, interface, resources, event=None, addr=None, group="", type="sensor", location=None, label="", interrupt=None):
        Sensor.__init__(self, name, interface, addr, event=event, group=group, type=type, location=location, label=label, interrupt=interrupt)
        self.resources = resources
        self.states = {}        # dictionary of current sensor states
        self.stateTypes = {}    # dictionary of (state, type)

    # return the current state of all sensors in the collection
    def getState(self):
        self.getStates()
        return self.states

    # return the current state and type of all sensors in the collection
    def getStateTypes(self):
        self.getStates()
        return self.stateTypes

    # update the current state and type of all sensors in theresource collection
    def getStates(self):
        self.states = {}    # current sensor states
        self.stateTypes = {}
        for sensor in self.resources.values():
            if sensor != self:
                sensorName = sensor.name
                sensorType = sensor.type
                if sensorType in ["schedule", "collection"]:   # recurse into schedules and collections
                    self.getStates(sensor)
                elif sensor.getStateType() != dict:     # sensor has a scalar state
                    sensorState = sensor.getState()
                else:                                   # sensor has a complex state
                    sensorState = sensor.getState()["contentType"]
            self.states[sensorName] = sensorState
            self.stateTypes[sensorName] = (sensorState, sensorType)

    # wait for a sensor state to change
    def waitStateChange(self):
        if self.event:
            debug('debugInterrupt', self.name, "wait", self.event)
            self.event.wait()
            debug('debugInterrupt', self.name, "clear", self.event)
            self.event.clear()
        else:               # no event specified, return periodically
            time.sleep(stateChangeInterval)

    # return the current state of all sensors when at least one of them changes
    def getStateChange(self):
        debug('debugInterrupt', self.name, "getStateChange")
        self.waitStateChange()
        return self.getState()

    # return the current state and type of all sensors when at least one of them changes
    def getStateChangeTypes(self):
        debug('debugInterrupt', self.name, "getStateChange")
        self.waitStateChange()
        return self.getStateTypes()

# Control that can only be turned on if all the specified resources are in the specified states
class DependentControl(Control):
    def __init__(self, name, interface, control, conditions, addr=None, group="", type="control", location=None, label="", interrupt=None):
        Control.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt)
        self.className = "Control"
        self.control = control
        self.conditions = conditions

    def setState(self, state, wait=False):
        debug('debugState', self.name, "setState ", state)
        for (sensor, condition, value) in self.conditions:
            sensorState = sensor.getState()
            debug('debugDependentControl', self.name, sensor.name, sensorState, condition, value)
            if not eval(str(sensorState)+condition+str(value)):
                return
        self.control.setState(state)

# Control that can be set on but reverts to off after a specified time
class OneShotControl(Control):
    def __init__(self, name, interface, addr=None, duration=1, group="", type="control", location=None, label="", event=None, interrupt=None):
        Control.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, event=event, interrupt=interrupt)
        self.className = "Control"
        self.duration = duration
        self.timedState = 0
        self.timer = None

    def setState(self, state, wait=False):
        # timeout is the length of time the control will stay on
        debug("debugState", "OneShotControl", self.name, "setState", state)
        if not self.timedState:
            self.timedState = state
            self.timer = threading.Timer(self.duration, self.timeout)
            self.timer.start()
            debug("debugState", "OneShotControl", self.name, "timer", self.timedState)
            self.notify()

    def timeout(self):
        self.timedState = 0
        debug("debugState", "OneShotControl", self.name, "timeout", self.timedState)
        self.notify()

    def getState(self):
        return self.timedState

# Control that has specified numeric limits on the values it can be set to
class MinMaxControl(Control):
    def __init__(self, name, interface, addr=None, minValue=0, maxValue=1, group="", type="control", location=None, label="", interrupt=None):
        Control.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt)
        self.className = "Control"
        self.setMinMax(minValue, maxValue)

    def setState(self, state, wait=False):
        state = int(state)
        debug("debugState", "MinMaxControl", self.name, "setState", state, self.minValue, self.maxValue)
        if state < self.minValue:
            value = self.minValue
        elif state > self.maxValue:
            value = self.maxValue
        else:
            value = state
        Control.setState(self, value)

    def setMinMax(self, minValue, maxValue):
        self.minValue = minValue
        self.maxValue = maxValue

# Sensor that captures the minimum state value of the specified sensor
class MinSensor(Sensor):
    def __init__(self, name, interface, sensor, event=None, addr=None, group="", type="sensor", location=None, label="", interrupt=None):
        Sensor.__init__(self, name, interface, addr, event=event, group=group, type=type, location=location, label=label, interrupt=interrupt)
        self.className = "Sensor"
        self.sensor = sensor
        try:
            self.minState = self.interface.read(self.name)
        except:
            self.minState = 999

    def getState(self):
        sensorState = self.sensor.getState()
        if sensorState < self.minState:
            if sensorState != 0:    # FIXME
                self.minState = sensorState
                if self.interface:
                    self.interface.write(self.name, self.minState)
        return self.minState

    # reset the min value
    def setState(self, value):
        self.minState = value
        if self.interface:
            self.interface.write(self.name, self.minState)

# Sensor that captures the maximum state value of the specified sensor
class MaxSensor(Sensor):
    def __init__(self, name, interface, sensor, event=None, addr=None, group="", type="sensor", location=None, label="", interrupt=None):
        Sensor.__init__(self, name, interface, addr, event=event, group=group, type=type, location=location, label=label, interrupt=interrupt)
        self.className = "Sensor"
        self.sensor = sensor
        try:
            self.maxState = self.interface.read(self.name)
        except:
            self.maxState = 0

    def getState(self):
        sensorState = self.sensor.getState()
        if sensorState > self.maxState:
            self.maxState = sensorState
            if self.interface:
                self.interface.write(self.name, self.maxState)
        return self.maxState

    # reset the max value
    def setState(self, value):
        self.maxState = value
        if self.interface:
            self.interface.write(self.name, self.maxState)

# Sensor that captures the accumulated state values of the specified sensor
class AccumSensor(Sensor):
    def __init__(self, name, interface, sensor, multiplier=1, event=None, addr=None, group="", type="sensor", location=None, label="", interrupt=None):
        Sensor.__init__(self, name, interface, addr, event=event, group=group, type=type, location=location, label=label, interrupt=interrupt)
        self.className = "Sensor"
        self.sensor = sensor
        self.multiplier = multiplier
        try:
            self.accumValue = self.interface.read(self.name)
        except:
            self.accumValue = 0

    def getState(self):
        self.accumValue = self.sensor.getState() * self.multiplier
        if self.interface:
            self.interface.write(self.name, self.accumValue)
        return self.accumValue

    # reset the accumulated value
    def setState(self, value):
        self.accumValue = value
        if self.interface:
            self.interface.write(self.name, self.accumValue)

# sensor that returns the value of an attribute of a specified sensor
class AttributeSensor(Sensor):
    def __init__(self, name, interface, addr, sensor, attr, group="", type="sensor", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.sensor = sensor
        self.attr = attr

    def getState(self):
        return getattr(self.sensor, self.attr)
