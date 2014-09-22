
from BTUtils import *
from HCClasses import *
from HCScheduler import *
from X10Interface import *
from serialInterface import *

# Force usb serial devices to associate with specific devices based on which port they are plugged into

# cat >> /etc/udev/rules.d/91-local.rules << ^D
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.1", NAME="ttyUSB0", SYMLINK+="aqualink"
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.2", NAME="ttyUSB1", SYMLINK+="pentair"
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.3", NAME="ttyUSB2", SYMLINK+="x10"
# ^D

defaultConfig = {"debug": False,
                 "serial2": "/dev/x10",
                 "httpPort": 80,
                 "latLong": (34.1486, -118.3965),
                 "tempScale": "F"}
serial2Config = {"baudrate": 9600}

if __name__ == "__main__":
    app = BTApp("hc.conf", "hc.log", defaultConfig)
    resTab = HCResTab("Resource table", app)
    scheduler = HCScheduler("Scheduler", app)

    # Interfaces
    nullInterface = HCInterface("Null", app, None)
    serial2 = HCSerialInterface("Serial2", app, app.serial2, serial2Config)
    x10Interface = X10Interface("X10", app, app.serial2)
    
    resTab.addRes(HCControl("Null", app, nullInterface, None))
    
    # Lights
    resTab.addRes(HCControl("xmasLights", app, x10Interface, "A1", type="light", group="Lights", label="Xmas lights"))
    resTab.addRes(HCControl("frontLights", app, x10Interface, "A2", type="light", group="Lights", label="Front lights"))
    resTab.addRes(HCControl("backLights", app, x10Interface, "A3", type="light", group="Lights", label="Back lights"))
    resTab.addRes(HCControl("bbqLights", app, x10Interface, "A6", type="light", group="Lights", label="Barbeque lights"))
    resTab.addRes(HCControl("backYardLights", app, x10Interface, "A7", type="light", group="Lights", label="Back yard lights"))
    resTab.addRes(HCScene("outsideLights", app, [resTab.resources["frontLights"], 
                                                  resTab.resources["backLights"],
                                                  resTab.resources["xmasLights"]], type="light", group="Lights", label="Outside"))

    # Water
    resTab.addRes(HCControl("Recirc pump", app, x10Interface, "A4", "Water"))

    # Schedules
    scheduler.addJob(HCJob("Outside lights on sunset", app, HCSchedTime(event="sunset"), resTab.resources["outsideLights"].setState, {"theState":True}))
    scheduler.addJob(HCJob("Outside lights off midnight", app, HCSchedTime(hour=[17,23,0], minute=[1]), resTab.resources["outsideLights"].setState, {"theState":False}))
    scheduler.addJob(HCJob("Front lights on test", app, HCSchedTime(year=[2014],month=[1],day=[30],hour=[16], minute=[27]), resTab.resources["frontLights"].setState, {"theState":True}))
    scheduler.addJob(HCJob("Front lights off test", app, HCSchedTime(year=[2014],month=[1],day=[30],hour=[16], minute=[28]), resTab.resources["frontLights"].setState, {"theState":False}))
    scheduler.addJob(HCJob("Outside lights off sunrise", app, HCSchedTime(event="sunrise"), resTab.resources["outsideLights"].setState, {"theState":False}))
    
    scheduler.addJob(HCJob("Hot water recirc on", app, HCSchedTime(hour=[05], minute=[02]), resTab.resources["Recirc pump"].setState, {"theState":True}))
    scheduler.addJob(HCJob("Hot water recirc off", app, HCSchedTime(hour=[23], minute=[02]), resTab.resources["Recirc pump"].setState, {"theState":False}))

    # Start interfaces
    x10Interface.start()
    
