# coding=utf-8

from ha import *

# A View describes how the value of a sensor's state should be displayed.  It contains a mapping of
# state values to display values, an optional format string, and an optional transform function.
# Reverse mappings of display values to state values may also be specified.
class View(object):
    def __init__(self, values={None:"--", 0:"Off", 1:"On"}, format="%s", transform=None, setValues=None, toggle=False):
        self.values = values
        self.format = format
        self.transform = transform
        if setValues == None:
            self.setValues = {0:"Off", 1:"On"}
        else:
            self.setValues = OrderedDict(setValues) # preserve the order of set values for display purposes
        self.toggle = toggle
 
    # Return the printable string value for the state of the sensor
    def getViewState(self, sensor):
        state = sensor.getState()
        try:    # run it through the transformation function
            state = self.transform(state)
        except:
            pass
        try:    # look it up in the values table
            return self.format % (self.values[state])
        except:
            if state:
                try:    # apply the format
                    return self.format % (state)
                except: # worst case, return the string of the state
                        return str(state)
            else:   # None means sensor isn't reporting
                return "--"

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

# Dictionary of views keyed by sensor type
class ViewDict(dict):
    def __init__(self, views):
        dict.__init__(self, views)
        self.__setitem__("", View())    # default View
                
    # Return the printable string value for the state of the sensor
    def getViewState(self, sensor):
        try:
            return self.__getitem__(sensor.type).getViewState(sensor)
        except KeyError:
            return self.__getitem__("").getViewState(sensor)

    # Return the printable string values for the states that can be set on the control
    def getSetValues(self, control):
        try:
            return self.__getitem__(control.type).setValues
        except KeyError:
            return self.__getitem__("").setValues

    # Set the state of the control to the state value corresponding to the specified display value
    def setViewState(self, control, value):
        try:
            return self.__getitem__(control.type).setViewState(control, value)
        except KeyError:
            return self.__getitem__("").setViewState(control, value)
         
# transform functions
def intFormat(value):
    return int(value+.5)
    
def ctofFormat(value):
    return tempFormat(value*9/5+32)

def kiloFormat(value):
    return value/1000.0
    
def megaFormat(value):
    return value/1000000.0

def seqCountdownFormat(resource):
    pass

def tempFormat(value):
    if value == 0:
        return "--"
    else:
        return "%d F"%(int(value+.5))

def secsFormat(value):
    (m, s) = divmod(value, 60)
    (h, m) = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)
            
def latFormat(value):
    return "%7.3f %s" % (abs(value), "N" if value > 0.0 else "S")
            
def longFormat(value):
    return "%7.3f %s" % (abs(value), "E" if value > 0.0 else "W")
            
def hdgFormat(value):
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    direction = dirs[int((value+11.25)%360/22.5)]
    return "%03d %s" % (int(value), direction)
        
# view definitions    
views = ViewDict(  {"none": View(),
#         "tempC": View({}, "%d °", ctofFormat),
#         "tempF": View({}, "%d °", tempFormat),
         "tempC": View({}, "%d F", ctofFormat),
         "tempF": View({}, "%d F", tempFormat),
         "tempFControl": View({}, "%d F", tempFormat, OrderedDict([(-1,"v"), (+1,"^")])),
         "audioVolume": View({}, "%d%%", None, OrderedDict([(-5,"v"), (+5,"^")])),
         "audioMute": View({0:"X", 1:"*"}, "%s", None, {0:"*", 1:"X"}, True),
         "wifi": View({0:"Off", 1:"On"}, "%s", None, {0:"On", 1:"Off"}, True),
         "in": View({}, "%5.2f in"),
         "barometer": View({}, "%5.2f in"),
         "humidity": View({}, "%d %%"),
         "service": View({0:"Down", 1:"Up"}, "%s"),
         "light": View({0:"Off", 1:"On"}, "%s", None, {0:"Off", 1:"On"}),
         "nightLight": View({0:"Off", 1:"On", 2:"Sleep", 10:"Sleep", 100:"On"}, "%s", None, OrderedDict([(2,"Sleep"), (1,"On")])),
         "led": View({0:"Off", 1:"On", 2:"Flickr"}, "%s", None, OrderedDict([(0,"Off"), (1,"On"), (2,"Flickr")])),
         "dimmer": View(OrderedDict([(0,"Off"), (10,"Lo"), (30,"Med"), (60,"Hi"), (100,"On")]), "%s", None, OrderedDict([(0,"Off"), (10,"Lo"), (30,"Med"), (60,"Hi"), (100,"On")])),
         "hotwater": View({0:"Off", 1:"On"}, "%s", None, {0:"Off", 1:"On"}),
         "door": View({0:"Closed", 1:"Open"}, "%s"),
         "shade": View({None:"", 0:"Up", 1:"Down", 2:"Raising", 3:"Lowering"}, "%s", None, {0:"Up", 1:"Down"}),
         "spa": View({0:"Off", 1:"On", 2:"Starting", 3:"Warming", 4:"Standby", 5:"Stopping"}, "%s", None, {0:"Off", 1:"On", 4:"Stby"}),
         "poolValve": View({0:"Pool", 1:"Spa", 4:"Moving"}, "%s", None, {0:"Pool", 1:"Spa"}),
         "valveMode": View({0:"Pool", 1:"Spa", 2:"Drain", 3:"Fill", 4:"Moving"}, "%s", None, OrderedDict([(0,"Pool"), (1,"Spa"), (2,"Drain"), (3,"Fill")])),
         "pump": View({0:"Off", 1:"Lo", 2:"Med", 3:"Hi", 4:"Max"}, "%s", None, {0:"Off", 1:"Lo", 2:"Med", 3:"Hi", 4:"Max"}),
         "pumpSpeed": View({}, "%d RPM"),
         "pumpFlow": View({}, "%d GPM"),
         "cleaner": View({0:"Off", 1:"On", 2:"Ena"}, "%s", None, {0:"Off", 1:"On"}),
         "tempControl": View({0:"Off", 1:"Ena"}, "%s", None, {0:"Off", 1:"Ena"}),
         "thermostat": View({0:"Off", 1:"Heat", 2:"Cool", 3:"Fan", 4:"Auto"}, "%s", None, {0:"Off", 1:"Heat", 2:"Cool", 3:"Fan", 4:"Auto"}),
         "thermostatSensor": View({0:"Off", 1:"Heating", 2:"Cooling", 3:"Fan", 5:"Hold"}, "%s"),
         "cameraMode": View({0:"Still", 1:"Time", 2:"Video", 3:"Motion"}, "%s", None, {0:"Still", 1:"Time", 2:"Video", 3:"Motion"}),
         "cameraEnable": View({0:"Disabled", 1:"Enabled"}, "%s", None, {0:"Dis", 1:"Ena"}),
         "cameraRecord": View({0:"Stopped", 1:"Recording"}, "%s", None, {0:"Stop", 1:"Rec"}),
         "diagCode": View({}, "%d"),
         "Ft": View({}, "%d FT", intFormat),
         "MPH": View({}, "%d MPH", intFormat),
         "RPM": View({}, "%d RPM", intFormat),
         "Secs": View({}, "%s", secsFormat),
         "Lat": View({}, "%s", latFormat),
         "Long": View({}, "%s", longFormat),
         "Deg": View({}, "%s", hdgFormat),
         "power": View({}, "%d W"),
         "KVA": View({}, "%7.3f KVA", kiloFormat),
         "W": View({}, "%7.1f W"),
         "V": View({}, "%4.1f V"),
         "KW": View({}, "%7.3f KW", kiloFormat),
         "KWh": View({}, "%7.3f KWh", kiloFormat),
         "MWh": View({}, "%7.3f MWh", megaFormat),
         "dBm": View({}, "%4.1f dBm"),
         "int": View({}, "%d", intFormat),
         "int2": View({}, "%02d", intFormat),
         "int3": View({}, "%03d", intFormat),
         "sequence": View({0:"Stopped", 1:"Running"}, "%s", None, {0:"Stop", 1:"Run"}),
         "task": View({0:"Disabled", 1:"Enabled"}, "%s", None, {0:"Dis", 1:"Ena"})
         })

# by default the UI will create a css class based on the state value
# these types are the exceptions
staticTypes = ["time", "ampm", "date", "KVA", "W", "V", "KW", "MW", "KWh"]          # types whose class does not depend on their value
tempTypes = ["tempF", "tempFControl", "tempC", "spaTemp"]       # temperatures
                            
