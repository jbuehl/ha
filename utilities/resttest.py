from ha import *
from ha.restServer import *

if __name__ == "__main__":
    int1 = Interface("int1")
    sensors = Collection("sensors")
    sensors.addRes(Sensor("sensor1", int1, "addr1"))
    sensors.addRes(Sensor("sensor2", int1, "addr2"))
    sensors.addRes(Control("control3", int1, "addr3"))
    schedule = Schedule("schedule")
    resources = Collection("resources")
    resources.addRes(sensors)
    resources.addRes(schedule)
    server = RestServer(resources)
    server.start()
