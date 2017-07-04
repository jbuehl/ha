# Weather Underground update app
# http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol

# sensors
weatherSensorServices = []
tempSensor = "outsideTemp"
humiditySensor = "humidity"
barometerSensor = "barometer"
windSpeedSensor = "windSpeed"
windDirSensor = "windDir"
dewpointSensor = "dewpoint"

import requests
from ha import *
from ha.rest.restProxy import *

# Wunderground
wunderKey = keyDir+"wunderground.key"
wunderId = getValue(wunderKey, "id")
wunderPassword = getValue(wunderKey, "password")
updatePeriod = 10
wunderUrl = "http://rtupdate.wunderground.com/weatherstation/updateweatherstation.php"
wunderRequest = wunderUrl+"?action=updateraw&realtime=1&dateutc=now&rtfreq="+str(updatePeriod)+"&ID="+wunderId+"&PASSWORD="+wunderPassword

if __name__ == "__main__":
    stateChangeEvent = threading.Event()
    resources = Collection("resources")
    restCache = RestProxy("restProxy", resources, watch=weatherSensorServices, event=stateChangeEvent)
    restCache.start()
    while True:
        time.sleep(updatePeriod)
        try:
            temp = resources[tempSensor].getState()
            debug('debugWunderground', "temp:", temp)
            humidity = resources[humiditySensor].getState()
            debug('debugWunderground', "humidity:", humidity)
            dewpoint = resources[dewpointSensor].getState()
            debug('debugWunderground', "dewpoint:", dewpoint)
            barometer = resources[barometerSensor].getState()
            debug('debugWunderground', "barometer:", barometer)
            windSpeed = resources[windSpeedSensor].getState()
            debug('debugWunderground', "windSpeed:", windSpeed)
            windDir = resources[windDirSensor].getState()
            debug('debugWunderground', "windDir:", windDir)
            request = wunderRequest+"&tempf="+str(temp)+"&humidity="+str(humidity)+"&dewptf="+str(dewpoint)+"&baromin="+str(barometer)
            request += "&windspeedmph="+str(windSpeed)+"&winddir="+str(windDir)
            response = requests.get(request)
            debug('debugWunderground', "request:", request, "response:", response.text, "status:", response.status_code)
            if (response.status_code != 200) or (response.text[0:7] != "success"):
                log("update error response:", response.text, "status:", response.status_code)
        except KeyError:
            log("no sensor")
        except requests.exceptions.ConnectionError:
            log("connection error")
    
