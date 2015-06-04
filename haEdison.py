from ha.HAClasses import *
from ha.I2CCmdInterface import *
from ha.MCP9803Interface import *
from ha.tempInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    i2c1 = I2CCmdInterface("I2C1", bus=1, event=stateChangeEvent)
    mcp9803 = MCP9803Interface("MCP9803", i2c1)
    temp = TempInterface("Temp", mcp9803, sample=tempSample)
    
    # Temperature
    resources.addRes(HASensor("edisonTemp", temp, 0x49, group="Temperature", label="Edison temp", type="tempF"))
    
    # Schedules

    # Start interfaces
    temp.start()
    restServer = RestServer(resources, event=stateChangeEvent, label="Edison")
    restServer.start()

