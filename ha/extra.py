# Extra class definitions derived from basic classes

from .core import *

# A collection of sensors whose state is on if any one of them is on
class SensorGroup(Sensor):
    def __init__(self, name, sensorList, resources=None, **kwargs):
        Sensor.__init__(self, name, **kwargs)
        self.sensorList = sensorList
        self.resources = resources  # if specified, sensorList contains resource names, otherwise references
        # self.className = "Sensor"

    def getState(self):
        if self.interface:
            # This is a cached resource
            return Sensor.getState(self)
        else:
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

    # dictionary of pertinent attributes
    def dict(self, expand=False):
        attrs = Sensor.dict(self)
        attrs.update({"sensorList": [sensor.__str__() for sensor in self.sensorList]})
        return attrs

    def __repr__(self):
        return "\n".join([sensor.__str__() for sensor in self.sensorList])

# A set of Controls whose state can be changed together
class ControlGroup(SensorGroup, Control):
    def __init__(self, name, controlList, stateList=[], resources=None, stateMode=False, type="controlGroup", **kwargs):
        SensorGroup.__init__(self, name, controlList, resources, type=type, **kwargs)
        Control.__init__(self, name, type=type, **kwargs)
        self.stateMode = stateMode  # which state to return: False = SensorGroup, True = groupState
        self.groupState = 0
        if stateList == []:
            self.stateList = [[0,1]]*(len(self.sensorList))
        else:
            self.stateList = stateList

    def getState(self):
        if self.interface:
            # This is a cached resource
            return Sensor.getState(self)
        else:
            if self.stateMode:
                return self.groupState
            else:
                return SensorGroup.getState(self)

    def setState(self, state, wait=False):
        if self.interface:
            # This is a cached resource
            return Control.setState(self, state)
        else:
            debug('debugState', self.name, "setState ", state)
            self.groupState = int(state)  # use Cycle - FIXME
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
            self.notify(state)
            return True

    # dictionary of pertinent attributes
    def dict(self, expand=False):
        attrs = Control.dict(self)
        attrs.update({"controlList": [sensor.__str__() for sensor in self.sensorList]})
        return attrs

# A Control whose state depends on the states of a group of Sensors
class SensorGroupControl(SensorGroup, Control):
    def __init__(self, name, sensorList, control, resources=None, **kwargs):
        Control.__init__(self, name, **kwargs)
        SensorGroup.__init__(self, name, sensorList, resources, **kwargs)
        self.type = "sensorGroupControl"
        self.control = control

    def getState(self):
        if self.interface:
            # This is a cached resource
            return Sensor.getState(self)
        else:
            return self.control.getState()

    def setState(self, state):
        # set the control on if any of the sensors is on
        # set the control off only if all the sensors are off
        controlState = state
        for sensor in self.sensorList:
            controlState = controlState or sensor.getState()
        if self.interface:
            # This is a cached resource
            return Control.setState(self, controlState)
        else:
            debug("debugSensorGroupControl", self.name, "control:", self.control.name, "state:", state, "controlState:", controlState)
            self.control.setState(controlState)

    # dictionary of pertinent attributes
    def dict(self, expand=False):
        attrs = Control.dict(self)
        attrs.update({"sensorList": [sensor.__str__() for sensor in self.sensorList],
                      "control": self.control.__str__()})
        return attrs

# Calculate a function of a list of sensor states
class CalcSensor(Sensor):
    def __init__(self, name, sensors=[], function="", resources=None, **kwargs):
        Sensor.__init__(self, name, **kwargs)
        type = "sensor"
        self.sensors = sensors
        self.function = function.lower()
        self.resources = resources
        self.className = "Sensor"

    def getState(self):
        value = 0
        if self.function in ["sum", "avg", "+"]:
            for sensor in self.sensors:
                if isinstance(sensor, str):
                    if self.resources:
                        try:
                            value += self.resources[sensor].getState()
                        except KeyError:
                            pass
                else:
                    value += sensor.getState()
            if self.function == "avg":
                value /+ len(self.sensors)
        elif self.function in ["*"]:
            for sensor in self.sensors:
                if isinstance(sensor, str):
                    if self.resources:
                        try:
                            value *= self.resources[sensor].getState()
                        except KeyError:
                            pass
                else:
                    value *= sensor.getState()
        elif self.function in ["diff", "-"]:
            value = self.sensors[0].getState() - self.sensors[1].getState()
        return value * self.factor

# Control that can only be turned on if all the specified resources are in the specified states
class DependentControl(Control):
    def __init__(self, name, interface, control, conditions, resources=None, **kwargs):
        Control.__init__(self, name, **kwargs)
        type = "control"
        self.className = "Control"
        self.control = control
        self.conditions = conditions
        self.resources = resources

    def getState(self):
        return self.control.getState()

    def setState(self, state, wait=False):
        debug('debugState', self.name, "setState ", state)
        for (sensor, condition, value) in self.conditions:
            if isinstance(sensor, str):
                sensorName = sensor
                if self.resources:
                    try:
                        sensorState = self.resources[sensor].getState()
                    except KeyError:
                        sensorState = None
            else:
                sensorState = sensor.getState()
                sensorName = sensor.name
            if isinstance(value, Sensor):
                value = value.getState()
            debug('debugDependentControl', self.name, sensorName, sensorState, condition, value)
            try:
                if eval(str(sensorState)+condition+str(value)):
                    self.control.setState(state)
            except Exception as ex:
                log(self.name, "exception eveluating condition", str(ex))

# Control that can be set on but reverts to off after a specified time
class MomentaryControl(Control):
    def __init__(self, name, interface, addr=None, duration=1, group="", type="control", location=None, label="", event=None):
        Control.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, event=event)
        self.className = "Control"
        self.duration = duration
        self.timedState = 0
        self.timer = None

    def setState(self, state, wait=False):
        # timeout is the length of time the control will stay on
        debug("debugState", "OneShotControl", self.name, "setState", state)
        if not self.timedState:
            self.timedState = state
            self.interface.write(self.addr, self.timedState)
            self.timer = threading.Timer(self.duration, self.timeout)
            self.timer.start()
            debug("debugState", "OneShotControl", self.name, "timer", self.timedState)
            self.notify()

    def timeout(self):
        self.timedState = 0
        debug("debugState", "OneShotControl", self.name, "timeout", self.duration)
        debug("debugState", "OneShotControl", self.name, "setState", self.timedState)
        self.interface.write(self.addr, self.timedState)
        self.notify()

    def getState(self):
        return self.timedState

# Control that has a specified list of values it can be set to
class MultiControl(Control):
    def __init__(self, name, values=[], **kwargs):
        Control.__init__(self, name, **kwargs)
        type = "control"
        self.className = "MultiControl"
        self.values = values

    def setState(self, state, wait=False):
        debug("debugState", "MultiControl", self.name, "setState", state, self.values)
        if state in self.values:
            return Control.setState(self, state)
        else:
            return False

    # dictionary of pertinent attributes
    def dict(self, expand=False):
        attrs = Control.dict(self)
        attrs.update({"values": self.values})
        return attrs

# Control that has specified numeric limits on the values it can be set to
class MinMaxControl(Control):
    def __init__(self, name, interface, addr=None, minValue=0, maxValue=1, **kwargs):
        Control.__init__(self, name, interface, addr, **kwargs)
        type = "control"
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
    def __init__(self, name, interface, addr, sensor, **kwargs):
        Sensor.__init__(self, name, interface, addr, **kwargs)
        type = "sensor"
        self.className = "Sensor"
        self.sensor = sensor
        try:
            self.minState = self.interface.read(self.addr)
        except:
            self.minState = 999

    def getState(self):
        if self.interface:
            if self.interface.__class__.__name__ == "RestInterface":
                return self.interface.read(self.addr)
            else:
                self.minState = self.interface.read(self.addr)
        sensorState = self.sensor.getState()
        if sensorState < self.minState:
            if sensorState != 0:    # FIXME
                self.minState = sensorState
                if self.interface:
                    self.interface.write(self.addr, self.minState)
        return self.minState

    # reset the min value
    def setState(self, value):
        self.minState = value
        if self.interface:
            self.interface.write(self.addr, self.minState)

    # dictionary of pertinent attributes
    # def dict(self, expand=False):
    #     attrs = Control.dict(self)
    #     attrs.update({"sensor": str(self.sensor)})
    #     return attrs

# Sensor that captures the maximum state value of the specified sensor
class MaxSensor(Sensor):
    def __init__(self, name, interface, addr, sensor, **kwargs):
        Sensor.__init__(self, name, interface, addr, **kwargs)
        type = "sensor"
        self.className = "Sensor"
        self.sensor = sensor
        try:
            self.maxState = self.interface.read(self.addr)
        except:
            self.maxState = 0

    def getState(self):
        if self.interface:
            if self.interface.__class__.__name__ == "RestInterface":
                return self.interface.read(self.addr)
            else:
                self.maxState = self.interface.read(self.addr)
        sensorState = self.sensor.getState()
        if sensorState > self.maxState:
            self.maxState = sensorState
            if self.interface:
                self.interface.write(self.addr, self.maxState)
        return self.maxState

    # reset the max value
    def setState(self, value):
        self.maxState = value
        if self.interface:
            self.interface.write(self.addr, self.maxState)

    # dictionary of pertinent attributes
    # def dict(self, expand=False):
    #     attrs = Control.dict(self)
    #     attrs.update({"sensor": str(self.sensor)})
    #     return attrs

# Sensor that captures the accumulated state values of the specified sensor
class AccumSensor(Sensor):
    def __init__(self, name, interface, sensor, multiplier=1, **kwargs):
        Sensor.__init__(self, name, interface, addr, **kwargs)
        type = "sensor"
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
    def __init__(self, name, interface, addr, sensor, attr, **kwargs):
        Sensor.__init__(self, name, interface, addr, **kwargs)
        type = "sensor"
        self.sensor = sensor
        self.attr = attr

    def getState(self):
        return getattr(self.sensor, self.attr)

    # dictionary of pertinent attributes
    def dict(self, expand=False):
        attrs = Sensor.dict(self)
        attrs.update({"sensor": str(self.sensor),
                      "attr": self.attr})
        return attrs
