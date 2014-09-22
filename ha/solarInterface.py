from ha.HAClasses import *
from ha.HAConf import *

class HASolarInterface(HAInterface):
    def __init__(self, theName, theInterface):
        HAInterface.__init__(self, theName, theInterface)
        self.sql = """select %s(inverters.%s) from inverters,
	            (select date, max(time) time, id from inverters
		            where date = curdate()
		            group by id) max
	            where inverters.date = max.date and inverters.time = max.time and inverters.id = max.id;	
	            """

    def read(self, theAddr):
        try:
            sql = self.sql % (theAddr[1], theAddr[2])
            return self.interface.read(sql)
        except:
            return "-"

