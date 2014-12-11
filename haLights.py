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
    sensors = HACollection("sensors")
    schedule = HASchedule("schedule")
    resources.addRes(sensors)
    resources.addRes(schedule)

    # Interfaces
    serial2 = HASerialInterface("serial2", x10Device, serial2Config)
    x10Interface = X10Interface("x10", serial2)
    
    # Lights
    sensors.addRes(HAControl("xmasLights", x10Interface, "A1", type="light", group="Lights", label="Xmas lights"))
    sensors.addRes(HAControl("frontLights", x10Interface, "A2", type="light", group="Lights", label="Front lights"))
    sensors.addRes(HAControl("backLights", x10Interface, "A3", type="light", group="Lights", label="Back lights"))
    sensors.addRes(HAControl("bedroomLight", x10Interface, "A4", type="light", group="Lights", label="Bedroom light"))
    sensors.addRes(HAControl("bbqLights", x10Interface, "A6", type="light", group="Lights", label="Barbeque lights"))
    sensors.addRes(HAControl("backYardLights", x10Interface, "A7", type="light", group="Lights", label="Back yard lights"))
    sensors.addRes(HAScene("outsideLights", [sensors["frontLights"], 
                                             sensors["backLights"],
                                             sensors["bedroomLight"],
                                             sensors["xmasLights"]], [[0,1], [0,1], [0,1], [0,1]], group="Lights", label="Outside"))

    # Water
    sensors.addRes(HAControl("recircPump", x10Interface, "A8", "Water", label="Hot water"))

    # Schedules
    schedule.addTask(HATask("Outside lights on sunset", HASchedTime(event="sunset"), sensors["outsideLights"], 1))
    schedule.addTask(HATask("Outside lights off midnight", HASchedTime(hour=[23,0], minute=[00]), sensors["outsideLights"], 0))
#    schedule.addTask(HATask("Outside lights off 5pm", HASchedTime(hour=[17], minute=[01], month=[May, Jun, Jul, Aug, Sep, Oct]), sensors["outsideLights"], 0))
    schedule.addTask(HATask("Outside lights off sunrise", HASchedTime(event="sunrise"), sensors["outsideLights"], 0))
    
    schedule.addTask(HATask("Hot water recirc on", HASchedTime(hour=[05], minute=[02]), sensors["recircPump"], 1))
    schedule.addTask(HATask("Hot water recirc off", HASchedTime(hour=[23], minute=[02]), sensors["recircPump"], 0))

#    schedule.addTask(HATask("test on", HASchedTime(year=2014,month=2,day=3,hour=15,minute=58), sensors["frontLights"], 1))
#    schedule.addTask(HATask("test off", HASchedTime(year=2014,month=2,day=3,hour=15,minute=59), sensors["frontLights"], 0))

    # Start interfaces
    x10Interface.start()
    schedule.start()
    restServer = RestServer(resources)
    restServer.start()
    
