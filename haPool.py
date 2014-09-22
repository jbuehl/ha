from ha.HAClasses import *
from ha.serialInterface import *
from ha.aqualinkInterface import *
from ha.pentairInterface import *
from ha.powerInterface import *
from ha.restServer import *
from ha.logging import *

# Force usb serial devices to associate with specific devices based on which port they are plugged into

# cat >> /etc/udev/rules.d/91-local.rules << ^D
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.1", NAME="ttyUSB0", SYMLINK+="aqualink"
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.2", NAME="ttyUSB1", SYMLINK+="pentair"
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.3", NAME="ttyUSB2", SYMLINK+="x10"
# ^D

serial0Config = {"baudrate": 9600, 
                 "bytesize": serial.EIGHTBITS, 
                 "parity": serial.PARITY_NONE, 
                 "stopbits": serial.STOPBITS_ONE}
serial1Config = {"baudrate": 9600, 
                 "bytesize": serial.EIGHTBITS, 
                 "parity": serial.PARITY_NONE, 
                 "stopbits": serial.STOPBITS_ONE}

if __name__ == "__main__":
    resources = HACollection("resources")
    sensors = HACollection("sensors")
    schedule = HASchedule("schedule")
    resources.addRes(sensors)
    resources.addRes(schedule)

    # Interfaces
    nullInterface = HAInterface("Null", HAInterface("None"))
    serial0 = HASerialInterface("Serial0", aqualinkDevice, serial0Config)
    serial1 = HASerialInterface("Serial1", pentairDevice, serial1Config)
    aqualinkInterface = AqualinkInterface("Aqualink", serial0)
    pentairInterface = PentairInterface("Pentair", serial1)
    powerInterface = HAPowerInterface("Power", HAInterface("None"), powerTbl)
    
    sensors.addRes(HAControl("Null", nullInterface, None))
    
    # Lights
    sensors.addRes(HAControl("poolLight", aqualinkInterface, "aux4", type="light", group="Lights", label="Pool light"))
    sensors.addRes(HAControl("spaLight", aqualinkInterface, "aux5", type="light", group="Lights", label="Spa light"))
    sensors.addRes(HAScene("poolLights", [sensors["poolLight"], 
                                          sensors["spaLight"]], type="light", group="Lights", label="Pool and spa"))

    # Temperature
    sensors.addRes(HASensor("outsideAirTemp", aqualinkInterface, "airTemp", "Temperature",label="Air temp", type="tempF"))
    sensors.addRes(HASensor("poolTemp", aqualinkInterface, "poolTemp", "Temperature", label="Pool temp", type="tempF"))
    sensors.addRes(HASensor("spaTemp", aqualinkInterface, "spaTemp", "Temperature", label="Spa temp", type="tempF"))

    # Pool
#    sensors.addRes(HAControl("Pool pump", aqualinkInterface, "pump", group="Pool"))
    sensors.addRes(HAControl("poolPump", pentairInterface, 0, group="Pool", type="pump", label="Pump"))
    sensors.addRes(HASensor("poolPumpSpeed", pentairInterface, 1, group="Pool", type="pumpSpeed", label="Pump speed"))
    sensors.addRes(HASensor("poolPumpFlow", pentairInterface, 3, group="Pool", type="pumpFlow", label="Pump flow"))
    sensors.addRes(HAControl("poolCleaner", aqualinkInterface, "aux1", "Pool", label="Polaris", type="cleaner"))
    sensors.addRes(HAControl("spa", aqualinkInterface, "spa", "Pool", label="Spa"))
    sensors.addRes(HAControl("spaHeater", aqualinkInterface, "spaHtr", group="Pool", type="heater", label="Spa heater"))
    sensors.addRes(HAControl("spaBlower", aqualinkInterface, "aux2", "Pool", label="Spa blower"))
#    sensors.addRes(HAHeaterControl("Pool heater", aqualinkInterface, "poolHtr", group="Pool"))
    sensors.addRes(HASensor("model", aqualinkInterface, "model", "Pool", label="Controller model"))
    sensors.addRes(HASensor("date", aqualinkInterface, "date", "Pool", label="Controller date"))
    sensors.addRes(HASensor("time", aqualinkInterface, "time", "Pool", label="Controller time"))
    sensors.addRes(HASequence("cleanMode", [HACycle(sensors["poolPump"], duration=3600, startState=3), 
#                                              HACycle(sensors["poolCleaner"], duration=0, startState=1),
#                                              HACycle(sensors["Null"], duration=3600, startState=1, endState=0),
#                                              HACycle(sensors["poolCleaner"], duration=0, startState=0),
                                              HACycle(sensors["poolPump"], duration=0, startState=0)
                                              ], group="Pool", label="Clean mode"))
    sensors.addRes(HASequence("spaWarmup", [HACycle(sensors["spa"], duration=0, startState=1),
                                              HACycle(sensors["poolPump"], duration=0, startState=2, delay=30),
                                              HACycle(sensors["spaHeater"], duration=0, startState=1, delay=10)
                                              ], group="Pool", label="Spa warmup"))
    sensors.addRes(HASequence("spaReady", [HACycle(sensors["poolPump"], duration=0, startState=4),
                                              HACycle(sensors["spaLight"], duration=0, startState=1)
                                              ], group="Pool", label="Spa ready"))
    sensors.addRes(HASequence("spaShutdown", [HACycle(sensors["spaHeater"], duration=0, startState=0),
                                              HACycle(sensors["poolPump"], duration=0, startState=0, delay=300),
                                              HACycle(sensors["spa"], duration=0, startState=0),
                                              HACycle(sensors["spaLight"], duration=0, startState=0, delay=30)
                                              ], group="Pool", label="Spa shutdown"))

    # Power
    sensors.addRes(HASensor("poolPumpPower", pentairInterface, 2, type="power", group="Power", label="Pool pump"))
    sensors.addRes(HASensor("poolCleanerPower", powerInterface, sensors["poolCleaner"], type="power", group="Power", label="Pool cleaner"))
    sensors.addRes(HASensor("spaBlowerPower", powerInterface, sensors["spaBlower"], type="power", group="Power", label="Spa blower"))
    sensors.addRes(HASensor("poolLightPower", powerInterface, sensors["poolLight"], type="power", group="Power", label="Pool light"))
    sensors.addRes(HASensor("spaLightPower", powerInterface, sensors["spaLight"], type="power", group="Power", label="Spa light"))

    # Schedules
    schedule.addTask(HATask("Pool cleaning", HASchedTime(hour=[8], minute=[0]), sensors["cleanMode"], 1))

    # Start interfaces
    aqualinkInterface.start()
    pentairInterface.start()
    schedule.start()
    restServer = RestServer(resources, 7379)
    restServer.start()

