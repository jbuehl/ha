from ha.HAClasses import *

class HALoadInterface(HAInterface):
    def __init__(self, theName, theInterface):
        HAInterface.__init__(self, theName, theInterface)
        self.sql = """select loads.%s from loads,
	                    (select max(time) time from loads where date = curdate()) max
	                    where loads.date = curdate() and loads.time = max.time;	
                        """
        self.volts = {"lights":120,
	                    "plugs":120,
	                    "appl1":120,
	                    "cooking":240,
	                    "appl2":120,
	                    "ac":240,
	                    "pool":240,
	                    "back":240,
	                    }

    def read(self, theAddr):
        try:
            table = theAddr[0]
            sensor = theAddr[2].lower()
            sql = self.sql % (sensor)
            return self.interface.read(sql) * self.volts[sensor]
        except:
            return "-"

