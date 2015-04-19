from ha.HAClasses import *
from ha.I2CCmdInterface import *
from ha.TC74Interface import *
from ha.tempInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    i2c1 = I2CCmdInterface("I2C1", bus=1, event=stateChangeEvent)
    tc74 = TC74Interface("TC74", i2c1)
    temp = TempInterface("Temp", tc74)
    
    # Temperature
    resources.addRes(HASensor("edisonTemp", temp, 0x4b, group="Temperature", label="Edison temp", type="tempF"))
    
    # Schedules

    # Start interfaces
    temp.start()
    restServer = RestServer(resources, event=stateChangeEvent)
    restServer.start()

