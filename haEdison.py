
tempType = "tc74"
tempAddr = 0x4b

import sys
from ha import *
from ha.i2cCmdInterface import *
from ha.tc74Interface import *
from ha.mcp9803Interface import *
from ha.tempInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    i2c1 = I2CCmdInterface("I2C1", bus=1, event=stateChangeEvent)
    tc74 = TC74Interface("TC74", i2c1)
    mcp9803 = MCP9803Interface("MCP9803", i2c1)
    if tempType.upper() == "TC74":
        temp = TempInterface("Temp", tc74, sample=tempSample)
    elif tempType.upper() == "MCP9803":
        temp = TempInterface("Temp", mcp9803, sample=tempSample)
    else:
        log("error", "unknown tempType", tempType)
        sys.exit(1)
    
    # Temperature
    resources.addRes(HASensor("edisonTemp", temp, tempAddr, group="Temperature", label="Edison temp", type="tempF"))
    
    # Start interfaces
    temp.start()
    restServer = RestServer(resources, event=stateChangeEvent, label="Edison")
    restServer.start()

