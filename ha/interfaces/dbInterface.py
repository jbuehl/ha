import MySQLdb
import time
import threading
from ha import *

class DbInterface(Interface):
    objectArgs = ["interface", "event"]
    def __init__(self, name, dataBase, hostName="localhost", userName="", password=""):
        Interface.__init__(self, name, None)
        self.dataBase = dataBase
        self.hostName = hostName
        self.userName = userName
        self.password = password
        self.db = None
        self.lock = threading.Lock()

    def start(self):
        while not self.db:
            try:
                self.db = MySQLdb.connect(host=self.hostName, user=self.userName, passwd=self.password, db=self.dataBase)
            except:
                log("warning", "Error opening database - retrying in", dbRetryInterval, "seconds")
                time.sleep(dbRetryInterval)

    def read(self, sql):
        debug('debugSql', "sql", sql)
        try:
            with self.lock:
                cur = self.db.cursor()
                if cur.execute(sql) > 0:
                    result = cur.fetchall()[0][0]
                else:
                    result = "-"
                self.db.commit()
                cur.close()
            return result
        except:
            return "-"

