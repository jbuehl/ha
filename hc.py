
from BTUtils import *
from HCClasses import *
from HCScheduler import *
#from HCInterfaces import *
from X10Interface import *
from GPIOInterface import *
from serialInterface import *
from I2CInterface import *
#from weatherInterface import *
#from socketInterface import *
#from restInterface import *
#from dbInterface import *
from solarInterface import *
from aqualinkInterface import *
from pentairInterface import *
from powerInterface import *
from commandUI import *
from webUI import *

# Force usb serial devices to associate with specific devices based on which port they are plugged into

# cat >> /etc/udev/rules.d/91-local.rules << ^D
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.1", NAME="ttyUSB0", SYMLINK+="aqualink"
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.2", NAME="ttyUSB1", SYMLINK+="pentair"
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.3", NAME="ttyUSB2", SYMLINK+="x10"
# ^D

defaultConfig = {"debug": False,
                 "serial0": "/dev/aqualink",
                 "serial1": "/dev/pentair",
                 "serial2": "/dev/x10",
                 "httpPort": 80,
                 "latLong": (34.1486, -118.3965),
                 "tempScale": "F"}
serial0Config = {"baudrate": 9600, 
                 "bytesize": serial.EIGHTBITS, 
                 "parity": serial.PARITY_NONE, 
                 "stopbits": serial.STOPBITS_ONE}
serial1Config = {"baudrate": 9600, 
                 "bytesize": serial.EIGHTBITS, 
                 "parity": serial.PARITY_NONE, 
                 "stopbits": serial.STOPBITS_ONE}
serial2Config = {"baudrate": 9600}

def ctof(tempc):
    return tempc*9/5+23

def kilo(value):
    return value/1000.0
    
def mega(value):
    return value/1000000.0
    
if __name__ == "__main__":
    app = BTApp("hc.conf", "hc.log", defaultConfig)
    resTab = HCResTab("Resource table", app)
    scheduler = HCScheduler("Scheduler", app)

    # Interfaces
    nullInterface = HCInterface("Null", app, None)
    serial0 = HCSerialInterface("Serial0", app, app.serial0, serial0Config)
    serial1 = HCSerialInterface("Serial1", app, app.serial1, serial1Config)
    serial2 = HCSerialInterface("Serial2", app, app.serial2, serial2Config)
    i2c1 = HCI2CInterface("I2C1", app, 1)
    x10Interface = X10Interface("X10", app, app.serial2)
    gpioInterface = GPIOInterface("GPIO", app, i2c1)
    aqualinkInterface = AqualinkInterface("Aqualink", app, serial0)
    pentairInterface = PentairInterface("Pentair", app, serial1)
#    weatherInterface = WeatherInterface("Weather", app, i2c1)
    powerInterface = HCPowerInterface("Power", app, None, powerTbl)
    solarInterface = HCSolarInterface("Solar", app, None, app.solarIp)
    
    resTab.addRes(HCControl("Null", app, nullInterface, None))
    
    # Lights
    resTab.addRes(HCControl("xmasLights", app, x10Interface, "A1", type="light", group="Lights", label="Xmas lights"))
    resTab.addRes(HCControl("frontLights", app, x10Interface, "A2", type="light", group="Lights", label="Front lights"))
    resTab.addRes(HCControl("backLights", app, x10Interface, "A3", type="light", group="Lights", label="Back lights"))
    resTab.addRes(HCControl("bbqLights", app, x10Interface, "A6", type="light", group="Lights", label="Barbeque lights"))
    resTab.addRes(HCControl("backYardLights", app, x10Interface, "A7", type="light", group="Lights", label="Back yard lights"))
    resTab.addRes(HCControl("poolLight", app, aqualinkInterface, "aux4", type="light", group="Lights", label="Pool light"))
    resTab.addRes(HCControl("spaLight", app, aqualinkInterface, "aux5", type="light", group="Lights", label="Spa light"))
    resTab.addRes(HCScene("outsideLights", app, [resTab.resources["frontLights"], 
                                                  resTab.resources["backLights"],
                                                  resTab.resources["xmasLights"]], type="light", group="Lights", label="Outside"))
    resTab.addRes(HCScene("poolLights", app, [resTab.resources["poolLight"], 
                                               resTab.resources["spaLight"]], type="light", group="Lights", label="Pool and spa"))

    # Water
    resTab.addRes(HCControl("Recirc pump", app, x10Interface, "A4", "Water"))

    # Doors
    doorView = HCView({0:"Closed", 1:"Open"}, "%s")
    resTab.addRes(HCSensor("frontDoor", app, gpioInterface, GPIOAddr(0,0,2,1), type="door", group="Doors", label="Front", view=doorView))
    resTab.addRes(HCSensor("familyRoomDoor", app, gpioInterface, GPIOAddr(0,0,1,1), type="door", group="Doors", label="Family room", view=doorView))
    resTab.addRes(HCSensor("masterBedDoor", app, gpioInterface, GPIOAddr(0,0,0,1), type="door", group="Doors", label="Master bedroom", view=doorView))
    resTab.addRes(HCSensor("garageBackDoor", app, gpioInterface, GPIOAddr(0,0,3,1), type="door", group="Doors", label="Garage back", view=doorView))
#    resTab.addRes(HCDoorSensor("Garage door", app, gpioInterface, GPIOAddr(0,0,5,1), type="door", group="Doors", view=doorView))
#    resTab.addRes(HCDoorSensor("Garage door house", app, gpioInterface, GPIOAddr(0,0,4,1), type="door", group="Doors", view=doorView))

    # Windows

    # HVAC
#    resTab.addRes(HCControl("Living hvac", app, gpioInterface, GPIOAddr(1,1,0,3), "HVAC"))
#    resTab.addRes(HCControl("Bedroom hvac", app, gpioInterface, GPIOAddr(1,1,4,3), "HVAC"))

    # Sprinklers
#    resTab.addRes(HCControl("Front lawn", app, gpioInterface, GPIOAddr(0,1,0,1), "Sprinklers"))
#    resTab.addRes(HCControl("Parkway", app, gpioInterface, GPIOAddr(0,1,1,1), "Sprinklers"))
    resTab.addRes(HCControl("Front beds", app, gpioInterface, GPIOAddr(0,1,0,1), "Sprinklers"))
    resTab.addRes(HCControl("Back lawn", app, gpioInterface, GPIOAddr(0,1,1,1), "Sprinklers"))
    resTab.addRes(HCControl("Back beds", app, gpioInterface, GPIOAddr(0,1,2,1), "Sprinklers"))
    resTab.addRes(HCControl("Side beds", app, gpioInterface, GPIOAddr(0,1,3,1), "Sprinklers"))

    # Weather
#    resTab.addRes(HCSensor("Weather", app, weatherInterface))

    # Temperature

    tempViewC = HCView({}, "%d F", ctof)
    tempViewF = HCView({}, "%d F")
    resTab.addRes(HCSensor("insideTemp", app, i2c1, (0x48, 0x00), "Temperature", label="Inside temp", view=tempViewC))
    resTab.addRes(HCSensor("outsideAirTemp", app, aqualinkInterface, "airTemp", "Temperature",label="Air temp", view=tempViewF))
    resTab.addRes(HCSensor("poolTemp", app, aqualinkInterface, "poolTemp", "Temperature", label="Pool temp", view=tempViewF))
    resTab.addRes(HCSensor("spaTemp", app, aqualinkInterface, "spaTemp", "Temperature", label="Spa temp", view=tempViewF))
    resTab.addRes(HCSensor("inverterTemp", app, solarInterface, ("stats", "", "Tinv"), "Temperature", label="Inverter temp", view=tempViewC))
    resTab.addRes(HCSensor("roofTemp", app, solarInterface, ("stats", "", "Topt"), "Temperature", label="Roof temp", view=tempViewC))

    # Pool
#    resTab.addRes(HCControl("Pool pump", app, aqualinkInterface, "pump", "Pool"))
    resTab.addRes(HCControl("poolPump", app, pentairInterface, 0, group="Pool", type="pump", label="Pump", view=HCView({0:"Off", 1:"Lo", 2:"Med", 3:"Hi", 4:"Max"}, "%s")))
    resTab.addRes(HCSensor("poolPumpSpeed", app, pentairInterface, 1, group="Pool", label="Pump speed", view=HCView({}, "%d RPM")))
    resTab.addRes(HCSensor("poolPumpFlow", app, pentairInterface, 3, group="Pool", label="Pump flow", view=HCView({}, "%d GPM")))
    resTab.addRes(HCControl("poolCleaner", app, aqualinkInterface, "aux1", "Pool", label="Polaris", type="cleaner", view=HCView({0:"Off", 1:"On", 2:"Ena"}, "%s", None, {0:"Off", 1:"On"})))
    resTab.addRes(HCControl("spa", app, aqualinkInterface, "spa", "Pool", label="Spa"))
    resTab.addRes(HCControl("spaHeater", app, aqualinkInterface, "spaHtr", group="Pool", type="heater", label="Spa heater", view=HCView({0:"Off", 1:"On", 4:"Ena"}, "%s", None, {0:"Off", 1:"On"})))
    resTab.addRes(HCControl("spaBlower", app, aqualinkInterface, "aux2", "Pool", label="Spa blower"))
#    resTab.addRes(HCHeaterControl("Pool heater", app, aqualinkInterface, "poolHtr", "Pool"))
#    resTab.addRes(HCSequence("Cleaner delay", app, [HCCycle(resTab.resources["Null"], 1),
#                                                    HCCycle(resTab.resources["Elmo"], -1)], "Pool"))
#    resTab.addRes(HCScene("Clean mode", app, [resTab.resources["Pump"], 
#                                              resTab.resources["Cleaner"]], "Pool"))
#    resTab.addRes(HCScene("Spa mode", app, [resTab.resources["Spa"], 
#                                            resTab.resources["Spa heater"]], "Pool"))

    # Power
    powerView = HCView({}, "%d W")
    resTab.addRes(HCSensor("poolPumpPower", app, pentairInterface, 2, "Power", label="Pool pump", view=powerView))
    resTab.addRes(HCSensor("poolCleanerPower", app, powerInterface, resTab.resources["poolCleaner"], type="power", group="Power", label="Pool cleaner", view=powerView))
    resTab.addRes(HCSensor("spaBlowerPower", app, powerInterface, resTab.resources["spaBlower"], type="power", group="Power", label="Spa blower", view=powerView))
    resTab.addRes(HCSensor("poolLightPower", app, powerInterface, resTab.resources["poolLight"], type="power", group="Power", label="Pool light", view=powerView))
    resTab.addRes(HCSensor("spaLightPower", app, powerInterface, resTab.resources["spaLight"], type="power", group="Power", label="Spa light", view=powerView))

    # Solar
    resTab.addRes(HCSensor("currentPower", app, solarInterface, ("inverters", "total", "Pac"), "Solar", label="Current power", view=HCView({}, "%7.3f KW", kilo)))
    resTab.addRes(HCSensor("todaysEnergy", app, solarInterface, ("stats", "", "Eday"), "Solar", label="Energy today", view=HCView({}, "%7.3f KWh", kilo)))
    resTab.addRes(HCSensor("monthlyEnergy", app, solarInterface, ("stats", "", "Emonth"), "Solar", label="Energy this month", view=HCView({}, "%7.3f KWh", kilo)))
    resTab.addRes(HCSensor("yearlyEnergy", app, solarInterface, ("stats", "", "Eyear"), "Solar", label="Energy this year", view=HCView({}, "%7.3f KWh", kilo)))
    resTab.addRes(HCSensor("lifetimeEnergy", app, solarInterface, ("stats", "", "Elifetime"), "Solar", label="Lifetime energy", view=HCView({}, "%7.3f MWh", mega)))
        
    # Schedules
    scheduler.addJob(HCJob("Outside lights on sunset", app, HCSchedTime(event="sunset"), resTab.resources["outsideLights"].setState, {"theState":True}))
    scheduler.addJob(HCJob("Outside lights off midnight", app, HCSchedTime(hour=[23,0], minute=[1]), resTab.resources["outsideLights"].setState, {"theState":False}))
#    scheduler.addJob(HCJob("Front lights on 2013-8-9", app, HCSchedTime(year=[2013],month=[8],day=[9],hour=[23], minute=[2]), resTab.resources["frontLights"].setState, {"theState":True}))
    scheduler.addJob(HCJob("Outside lights off sunrise", app, HCSchedTime(event="sunrise"), resTab.resources["outsideLights"].setState, {"theState":False}))
    
    scheduler.addJob(HCJob("Hot water recirc on", app, HCSchedTime(hour=[05], minute=[02]), resTab.resources["Recirc pump"].setState, {"theState":True}))
    scheduler.addJob(HCJob("Hot water recirc off", app, HCSchedTime(hour=[23], minute=[02]), resTab.resources["Recirc pump"].setState, {"theState":False}))

    resTab.addRes(HCSequence("Garden sequence", app, [HCCycle(resTab.resources["Back beds"], 10)], "Sprinklers"))
    resTab.addRes(HCSequence("Sprinkler sequence", app, [HCCycle(resTab.resources["Back lawn"], 20),
                                                         HCCycle(resTab.resources["Side beds"], 10)], "Sprinklers"))
#    scheduler.addJob(HCJob("Garden", app, HCSchedTime(hour=[7], minute=[00], weekday=[Tue, Thu, Sat]), resTab.resources["Garden sequence"].setState, {"theState":True}))
#    scheduler.addJob(HCJob("Sprinklers", app, HCSchedTime(hour=[7], minute=[10], weekday=[Tue, Thu, Sat]), resTab.resources["Sprinkler sequence"].setState, {"theState":True}))

    # Start interfaces
    x10Interface.start()
    aqualinkInterface.start()
    pentairInterface.start()
    gpioInterface.start()
    solarInterface.start()
    web = WebUI("WebUI", app, None, resTab, scheduler)
    web.start()
    web.block()
#    cli = CommandUI("CLI", app, HCSerialInterface("Stdin", app, "/dev/stdin", {}), resTab)
#    cli.start()

    
