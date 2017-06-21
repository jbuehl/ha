# Weather Underground update app

# sensors
weatherSensorServices = ["deck:7378", "pool:7378"]
tempSensor = "poolEquipTemp"
humiditySensor = "humidity"
barometerSensor = "barometer"

# Wunderground
wunderId = "KCASTUDI18"
wunderPassword = "h51hza4l"
updatePeriod = 10
wunderUrl = "http://rtupdate.wunderground.com/weatherstation/updateweatherstation.php"
wunderRequest = wunderUrl+"?action=updateraw&realtime=1&dateutc=now&rtfreq="+str(updatePeriod)+"&ID="+wunderId+"&PASSWORD="+wunderPassword

import requests
from ha import *
from ha.rest.restProxy import *

if __name__ == "__main__":
    stateChangeEvent = threading.Event()
    resources = Collection("resources")
    restCache = RestProxy("restProxy", resources, watch=weatherSensorServices, event=stateChangeEvent)
    restCache.start()
    while True:
        time.sleep(updatePeriod)
        try:
            temp = resources[tempSensor].getState()
            humidity = resources[humiditySensor].getState()
            barometer = resources[barometerSensor].getState()
            debug('debugWunderground', "temp:", temp, "humidity:", humidity, "barometer:", barometer)
            request = wunderRequest+"&tempf="+str(temp)+"&humidity="+str(humidity)+"&baromin="+str(barometer)
            response = requests.get(request)
            debug('debugWunderground', "request:", request, "response:", response.text, "status:", response.status_code)
            if (response.status_code != 200) or (response.text[0:7] != "success"):
                log("wundergroundApp", "update error response:", response.text, "status:", response.status_code)
        except KeyError:
            debug('debugWunderground', "no sensor")
    
