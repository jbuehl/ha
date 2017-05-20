from ha import *
from ha.x10Interface import *
from ha.interfaces.serialInterface import *
from ha.rest.restServer import *

# Force usb serial devices to associate with specific devices based on which port they are plugged into

# cat >> /etc/udev/rules.d/91-local.rules << ^D
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.1", NAME="ttyUSB0", SYMLINK+="aqualink"
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.2", NAME="ttyUSB1", SYMLINK+="pentair"
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.3", NAME="ttyUSB2", SYMLINK+="x10"
# ^D

serial2Config = {"baudrate": 9600}

if __name__ == "__main__":
    # Resources
    resources = Collection("resources")
    schedule = Schedule("schedule")

    # Interfaces
    stateChangeEvent = threading.Event()
    serial2 = SerialInterface("serial2", device=x10Device, config=serial2Config, event=stateChangeEvent)
    x10Interface = X10Interface("x10", serial2)
    
    # Lights
    resources.addRes(Control("xmasCowTree", x10Interface, "A1", type="light", group="Lights", label="Cow tree"))
    resources.addRes(Control("bbqLights", x10Interface, "A6", type="light", group="Lights", label="Barbeque lights"))
    resources.addRes(Control("backYardLights", x10Interface, "A7", type="light", group="Lights", label="Back yard lights"))

    # Start interfaces
    x10Interface.start()
    restServer = RestServer(resources, event=stateChangeEvent, label="Back House")
    restServer.start()
    
