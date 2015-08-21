# coding=utf-8

from ha.HAClasses import *

# transform functions for views
def ctofFormat(value):
    return value*9/5+32

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
        
def spaTempFormat(value):
    temp = int(str(value).split(" ")[0])
    try:
        state = int(str(value).split(" ")[1])
    except:
        state = 0
    if temp == 0:
        return "Off"
    else:
        return "%d F %s" % (temp, {0:"Off", 1:"Ready", 2:"Starting", 3:"Warming", 4:"Standby", 5:"Stopping"}[state])
        
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
         "barometer": HAView({}, "%5.2f in"),
         "humidity": HAView({}, "%d %%"),
         "service": HAView({0:"Down", 1:"Up"}, "%s"),
         "light": HAView({0:"Off", 1:"On"}, "%s", None, OrderedDict([(1,"On"), (0,"Off")])),
         "nightLight": HAView({0:"Off", 1:"On", 2:"Sleep"}, "%s", None, OrderedDict([(1,"On"), (2,"Sleep")])),
         "dimmer": HAView(OrderedDict([(0,"Off"), (10,"Lo"), (30,"Med"), (60,"Hi"), (100,"On")]), "%s", None, OrderedDict([(0,"Off"), (10,"Lo"), (30,"Med"), (60,"Hi"), (100,"On")])),
         "hotwater": HAView({0:"Off", 1:"On"}, "%s", None, OrderedDict([(1,"On"), (0,"Off")])),
         "door": HAView({0:"Closed", 1:"Open"}, "%s"),
         "shade": HAView({None:"", 0:"Up", 1:"Down", 2:"Raising", 3:"Lowering"}, "%s", None, {0:"Up", 1:"Down"}),
         "spa": HAView({0:"Off", 1:"On", 2:"Starting", 3:"Warming", 4:"Standby", 5:"Stopping"}, "%s", None, {0:"Off", 1:"On", 4:"Stby"}),
         "spaTemp": HAView({}, "%s", spaTempFormat, {0:"Off", 1:"On"}),
         "poolValves": HAView({0:"Pool", 1:"Spa"}, "%s", None, {0:"Pool", 1:"Spa"}),
         "valveMode": HAView({0:"Pool", 1:"Spa", 2:"Drain", 3:"Fill"}, "%s", None, OrderedDict([(0,"Pool"), (1,"Spa"), (2,"Drain"), (3,"Fill")])),
         "pump": HAView({0:"Off", 1:"Lo", 2:"Med", 3:"Hi", 4:"Max"}, "%s", None, {0:"Off", 1:"Lo", 2:"Med", 3:"Hi", 4:"Max"}),
         "pumpSpeed": HAView({}, "%d RPM"),
         "pumpFlow": HAView({}, "%d GPM"),
         "cleaner": HAView({0:"Off", 1:"On", 2:"Ena"}, "%s", None, {0:"Off", 1:"On"}),
         "heater": HAView({0:"Off", 1:"On", 4:"Ena"}, "%s", None, {0:"Off", 1:"On"}),
         "cameraMode": HAView({0:"Still", 1:"Video", 2:"Motion"}, "%s", None, {0:"Still", 1:"Video", 2:"Motion"}),
         "cameraEnable": HAView({0:"Disabled", 1:"Enabled"}, "%s", None, {0:"Dis", 1:"Ena"}),
         "cameraRecord": HAView({0:"Stopped", 1:"Recording"}, "%s", None, {0:"Stop", 1:"Rec"}),
         "KVA": HAView({}, "%7.3f KVA", kiloFormat),
         "KW": HAView({}, "%7.3f KW", kiloFormat),
         "KWh": HAView({}, "%7.3f KWh", kiloFormat),
         "MWh": HAView({}, "%7.3f MWh", megaFormat),
         "sequence": HAView({0:"Stopped", 1:"Running"}, "%s", None, {0:"Stop", 1:"Run"}),
         "task": HAView({0:"Disabled", 1:"Enabled"}, "%s", None, {0:"Dis", 1:"Ena"})
         }
                            
