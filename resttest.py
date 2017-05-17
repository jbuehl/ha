from ha import *
from ha.restServer import *

if __name__ == "__main__":
    int1 = HAInterface("int1")
    sensors = HACollection("sensors")
    sensors.addRes(HASensor("sensor1", int1, "addr1"))
    sensors.addRes(HASensor("sensor2", int1, "addr2"))
    sensors.addRes(HAControl("control3", int1, "addr3"))
    schedule = HASchedule("schedule")
    resources = HACollection("resources")
    resources.addRes(sensors)
    resources.addRes(schedule)
    server = RestServer(resources)
    server.start()
