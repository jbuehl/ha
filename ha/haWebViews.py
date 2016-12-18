# coding=utf-8

from ha.HAClasses import *

# transform functions for views
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
        return "%d F"%(value)

def secsFormat(value):
    (m, s) = divmod(value, 60)
    (h, m) = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)
            
def latFormat(value):
    return "%7.3f %s" % (abs(value), "N" if value > 0.0 else "S")
            
def longFormat(value):
    return "%7.3f %s" % (abs(value), "E" if value > 0.0 else "W")
            
def spaTempFormat(value):
    temp = int(str(value).split(" ")[0])
    try:
        state = int(str(value).split(" ")[1])
    except:
        state = 0
    if state == 0:
        return "Off"
    else:
        return "%d F %s" % (temp, {0:"Off", 1:"Ready", 2:"Starting", 3:"Warming", 4:"Standby", 5:"Stopping"}[state])

def hdgFormat(value):
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    direction = dirs[int((value+11.25)%360/22.5)]
    return "%03d %s" % (int(value), direction)
        
# set temp color based on temp value
def tempColor(tempString):
    try:
        temp = int(tempString.split(" ")[0])
    except:
        temp = 0       
    if temp > 120:                 # magenta
        red = 252
        green = 0
        blue = 252
    elif temp > 102:               # red
        red = 252
        green = 0
        blue = (temp-102)*14
    elif temp > 84:                # yellow
        red = 252
        green = (102-temp)*14
        blue = 0
    elif temp > 66:                # green
        red = (temp-66)*14
        green = 252
        blue = 0
    elif temp > 48:                # cyan
        red = 0
        green = 252
        blue = (66-temp)*14
    elif temp > 30:                # blue
        red = 0
        green = (temp-30)*14
        blue = 252
    elif temp > 0:
        red = 0
        green = 0
        blue = 252
    else:
        red = 112
        green = 128
        blue = 144
    return 'rgb('+str(red)+','+str(green)+','+str(blue)+')'

# view definitions    
views = {"power": HAView({}, "%d W"),
#         "tempC": HAView({}, "%d °", ctofFormat),
#         "tempF": HAView({}, "%d °", tempFormat),
         "tempC": HAView({}, "%d F", ctofFormat),
         "tempF": HAView({}, "%d F", tempFormat),
         "tempFControl": HAView({}, "%d F", tempFormat, OrderedDict([(-1,"v"), (+1,"^")])),
         "audioVolume": HAView({}, "%d%%", None, OrderedDict([(-5,"v"), (+5,"^")])),
         "audioMute": HAView({0:"X", 1:"*"}, "%s", None, {0:"*", 1:"X"}, True),
         "wifi": HAView({0:"Off", 1:"On"}, "%s", None, {0:"On", 1:"Off"}, True),
         "barometer": HAView({}, "%5.2f in"),
         "humidity": HAView({}, "%d %%"),
         "service": HAView({0:"Down", 1:"Up"}, "%s"),
         "light": HAView({0:"Off", 1:"On"}, "%s", None, {0:"Off", 1:"On"}),
         "nightLight": HAView({0:"Off", 1:"On", 2:"Sleep", 10:"Sleep", 100:"On"}, "%s", None, OrderedDict([(2,"Sleep"), (1,"On")])),
         "led": HAView({0:"Off", 1:"On", 2:"Flickr"}, "%s", None, OrderedDict([(0,"Off"), (1,"On"), (2,"Flickr")])),
         "dimmer": HAView(OrderedDict([(0,"Off"), (10,"Lo"), (30,"Med"), (60,"Hi"), (100,"On")]), "%s", None, OrderedDict([(0,"Off"), (10,"Lo"), (30,"Med"), (60,"Hi"), (100,"On")])),
         "hotwater": HAView({0:"Off", 1:"On"}, "%s", None, {0:"Off", 1:"On"}),
         "door": HAView({0:"Closed", 1:"Open"}, "%s"),
         "shade": HAView({None:"", 0:"Up", 1:"Down", 2:"Raising", 3:"Lowering"}, "%s", None, {0:"Up", 1:"Down"}),
         "spa": HAView({0:"Off", 1:"On", 2:"Starting", 3:"Warming", 4:"Standby", 5:"Stopping"}, "%s", None, {0:"Off", 1:"On", 4:"Stby"}),
         "spaTemp": HAView({}, "%s", spaTempFormat, {0:"Off", 1:"On"}),
         "poolValve": HAView({0:"Pool", 1:"Spa", 2:"Moving"}, "%s", None, {0:"Pool", 1:"Spa"}),
         "valveMode": HAView({0:"Pool", 1:"Spa", 2:"Drain", 3:"Fill"}, "%s", None, OrderedDict([(0,"Pool"), (1,"Spa"), (2,"Drain"), (3,"Fill")])),
         "pump": HAView({0:"Off", 1:"Lo", 2:"Med", 3:"Hi", 4:"Max"}, "%s", None, {0:"Off", 1:"Lo", 2:"Med", 3:"Hi", 4:"Max"}),
         "pumpSpeed": HAView({}, "%d RPM"),
         "pumpFlow": HAView({}, "%d GPM"),
         "cleaner": HAView({0:"Off", 1:"On", 2:"Ena"}, "%s", None, {0:"Off", 1:"On"}),
         "heater": HAView({0:"Off", 1:"On", 4:"Ena"}, "%s", None, {0:"Off", 1:"On"}),
         "thermostat": HAView({0:"Off", 1:"Heat", 2:"Cool", 3:"Fan", 4:"Auto"}, "%s", None, {0:"Off", 1:"Heat", 2:"Cool", 3:"Fan", 4:"Auto"}),
         "cameraMode": HAView({0:"Still", 1:"Time", 2:"Video", 3:"Motion"}, "%s", None, {0:"Still", 1:"Time", 2:"Video", 3:"Motion"}),
         "cameraEnable": HAView({0:"Disabled", 1:"Enabled"}, "%s", None, {0:"Dis", 1:"Ena"}),
         "cameraRecord": HAView({0:"Stopped", 1:"Recording"}, "%s", None, {0:"Stop", 1:"Rec"}),
         "Ft": HAView({}, "%d FT"),
         "MPH": HAView({}, "%d MPH"),
         "RPM": HAView({}, "%d RPM"),
         "Secs": HAView({}, "%s", secsFormat),
         "Lat": HAView({}, "%s", latFormat),
         "Long": HAView({}, "%s", longFormat),
         "Deg": HAView({}, "%s", hdgFormat),
         "KVA": HAView({}, "%7.3f KVA", kiloFormat),
         "W": HAView({}, "%7.1f W"),
         "V": HAView({}, "%4.1f V"),
         "KW": HAView({}, "%7.3f KW", kiloFormat),
         "KWh": HAView({}, "%7.3f KWh", kiloFormat),
         "MWh": HAView({}, "%7.3f MWh", megaFormat),
         "sequence": HAView({0:"Stopped", 1:"Running"}, "%s", None, {0:"Stop", 1:"Run"}),
         "task": HAView({0:"Disabled", 1:"Enabled"}, "%s", None, {0:"Dis", 1:"Ena"})
         }

# by default the UI will create a css class based on the state value
# these types are the exceptions
staticTypes = ["time", "ampm", "date", "W", "KW"]          # types whose class does not depend on their value
tempTypes = ["tempF", "tempFControl", "tempC", "spaTemp"]       # temperatures
                            
