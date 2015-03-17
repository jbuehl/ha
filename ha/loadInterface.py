from ha.HAClasses import *

class LoadInterface(HAInterface):
    def __init__(self, name, interface):
        HAInterface.__init__(self, name, interface)
#        self.sql = """select loads.%s from loads,
#	                    (select max(time) time from loads where date = curdate()) max
#	                    where loads.date = curdate() and loads.time = max.time;	
#                        """
        self.volts = {"Lights":120,
	                  "Plugs":120,
	                  "Appl1":120,
	                  "Cooking":240,
	                  "Appl2":120,
	                  "Ac":240,
	                  "Pool":240,
	                  "Back":240,
	                   }

    def read(self, addr):
        try:
#            table = theAddr[0]
#            sensor = theAddr[2].lower()
#            sql = self.sql % (sensor)
#            return self.interface.read(sql) * self.volts[sensor]
            return self.interface.read(addr) * self.volts[addr]
        except:
            return "-"

