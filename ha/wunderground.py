# Weather Underground update
# http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol

reportWind = False
reportRain = False

import requests
import threading
from ha import *

# Wunderground
wunderKey = keyDir+"wunderground.key"
wunderId = getValue(wunderKey, "id")
wunderPassword = getValue(wunderKey, "password")
updatePeriod = 10
wunderUrl = "http://rtupdate.wunderground.com/weatherstation/updateweatherstation.php"
wunderRequest = wunderUrl+"?action=updateraw&realtime=1&dateutc=now&rtfreq="+str(updatePeriod)+"&ID="+wunderId+"&PASSWORD="+wunderPassword

def wunderground(tempSensor, humiditySensor, dewpointSensor, barometerSensor, windSpeedSensor, windDirSensor, rainHourSensor, rainDailySensor):
    def reportWeather():
        debug('debugWunderground', "starting wunderground thread")
        while True:
            time.sleep(updatePeriod)
            try:
                temp = tempSensor.getState()
                debug('debugWunderground', "temp:", temp)
                humidity = humiditySensor.getState()
                debug('debugWunderground', "humidity:", humidity)
                dewpoint = dewpointSensor.getState()
                debug('debugWunderground', "dewpoint:", dewpoint)
                barometer = barometerSensor.getState()
                debug('debugWunderground', "barometer:", barometer)
                if reportWind:
                    windSpeed = windSpeedSensor.getState()
                    debug('debugWunderground', "windSpeed:", windSpeed)
                    windDir = windDirSensor.getState()
                    debug('debugWunderground', "windDir:", windDir)
                else:
                    windSpeed = 0
                    windDir = 0
                if reportRain:
                    rainHour = rainHourSensor.getState()
                    debug('debugWunderground', "rainHour:", rainHour)
                    rainDay = rainDailySensor.getState()
                    debug('debugWunderground', "rainDay:", rainDay)
                else:
                    rainHour = 0
                    rainDay = 0
                request = wunderRequest+"&tempf="+str(temp)+"&humidity="+str(humidity)+"&dewptf="+str(dewpoint)+"&baromin="+str(barometer)
                request += "&windspeedmph="+str(windSpeed)+"&winddir="+str(windDir)
                request += "&rainin="+str(rainHour)+"&dailyrainin="+str(rainDay)
                response = requests.get(request)
                debug('debugWunderground', "request:", request, "response:", response.text, "status:", response.status_code)
                if (response.status_code != 200) or (response.text[0:7] != "success"):
                    log("update error response:", response.text, "status:", response.status_code)
            except KeyError:
                log("wunderground", "no sensor")
            except requests.exceptions.ConnectionError:
                log("wunderground", "connection error")
            except requests.exceptions.ReadTimeout:
                log("wunderground", "read timeout")
        debug('debugWunderground', "ending wunderground thread")
    wundergroundThread = LogThread(name="wundergroundThread", target=reportWeather)
    wundergroundThread.start()
