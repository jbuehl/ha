from ha.HAClasses import *
from ha.X10Interface import *
from ha.serialInterface import *
from ha.restServer import *

# Force usb serial devices to associate with specific devices based on which port they are plugged into

# cat >> /etc/udev/rules.d/91-local.rules << ^D
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.1", NAME="ttyUSB0", SYMLINK+="aqualink"
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.2", NAME="ttyUSB1", SYMLINK+="pentair"
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.3", NAME="ttyUSB2", SYMLINK+="x10"
# ^D

serial2Config = {"baudrate": 9600}

if __name__ == "__main__":

    # Collections
    resources = HACollection("resources")
    schedule = HASchedule("schedule")
    resources.addRes(schedule)

    # Interfaces
    serial2 = HASerialInterface("serial2", x10Device, serial2Config)
    x10Interface = X10Interface("x10", serial2)
    
    # Lights
    resources.addRes(HAControl("xmasLights", x10Interface, "A1", type="light", group="Lights", label="Xmas lights"))
    resources.addRes(HAControl("backLights", x10Interface, "A3", type="light", group="Lights", label="Back lights"))
    resources.addRes(HAControl("bedroomLight", x10Interface, "A4", type="light", group="Lights", label="Bedroom light"))
    resources.addRes(HAControl("bbqLights", x10Interface, "A6", type="light", group="Lights", label="Barbeque lights"))
    resources.addRes(HAControl("backYardLights", x10Interface, "A7", type="light", group="Lights", label="Back yard lights"))
    resources.addRes(HAScene("outsideLights", [resources["backLights"],
                                             resources["xmasLights"]], group="Lights", label="Outside"))

    # Schedules
    schedule.addTask(HATask("Bedroom light on sunset", HASchedTime(event="sunset"), resources["bedroomLight"], 1))
    schedule.addTask(HATask("Bedroom light off sunrise", HASchedTime(event="sunrise"), resources["bedroomLight"], 0))
    schedule.addTask(HATask("Outside lights on sunset", HASchedTime(event="sunset"), resources["outsideLights"], 1))
    schedule.addTask(HATask("Outside lights off midnight", HASchedTime(hour=[23,0], minute=[00]), resources["outsideLights"], 0))
    schedule.addTask(HATask("Outside lights off sunrise", HASchedTime(event="sunrise"), resources["outsideLights"], 0))
    

    # Start interfaces
    x10Interface.start()
    schedule.start()
    restServer = RestServer(resources)
    restServer.start()
    
