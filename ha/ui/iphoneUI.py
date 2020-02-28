
from jinja2 import FileSystemLoader
from ha import *

def iphoneUI(resources, templates, views):
    with resources.lock:
        widths = [[320, [60, 100, 60]], [320, [120, 72, 128]]]
        reply = templates.get_template("iphone.html").render(script="",
                            templates=templates,
                            widths=widths,
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            temp=resources.getRes(outsideTemp),
                            dayOfWeek=resources.getRes("theDayOfWeek"),
                            date=resources.getRes("theDate"),
                            dashResources=resources.getResList(["sunrise", "sunset"]),
                            spaControls = templates.get_template("spaWidget.html").render(templates=templates, widths=widths[1],
                                    spa=resources.getRes("spa"), spaTemp=resources.getRes("spaTemp"), spaTempTarget=resources.getRes("spaTempTarget"), nSetValues=3, views=views),
                            poolControls = templates.get_template("poolPumpWidget.html").render(templates=templates, widths=widths[1],
                                    poolPumpControl=resources.getRes("poolPump"), poolPumpFlowSensor=resources.getRes("poolPumpFlow"), nSetValues=5, views=views),
                            poolResources=resources.getResList(["valveMode", "spaBlower", "spaFill", "spaFlush", "spaDrain", "cleanSequence"]),
                            lightResources=resources.getResList(["frontLights", "backLights", "deckLights", "trashLights", "garageLights", "garageBackDoorLight",
                                                                 "poolLight", "spaLight", "sculptureLights", "nightLights"]),
                            shadeResources=resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"]),
                            sprinklerResources=resources.getResList(["backLawnSequence", "backBedSequence", "gardenSequence",
                                                                     "sideBedSequence", "frontLawnSequence", "frontBedSequence",
                                                                     "dailySequence", "weeklySequence"]),
                            hvacLiving = templates.get_template("hvacWidget.html").render(label="Living area",
                                    widths=widths[1],
                                    templates=templates,
                                    tempSensor=resources.getRes("diningRoomTemp"),
                                    heatTargetControl=resources.getRes("southHeatTempTarget"),
                                    coolTargetControl=resources.getRes("southCoolTempTarget"),
                                    fanControl=resources.getRes("southFan"),
                                    thermostatUnitSensor=resources.getRes("southThermostatUnitSensor"),
                                    views=views),
                            hvacBedrooms = templates.get_template("hvacWidget.html").render(label="Bedrooms",
                                    widths=widths[1],
                                    templates=templates,
                                    tempSensor=resources.getRes("masterBedroomTemp"),
                                    heatTargetControl=resources.getRes("northHeatTempTarget"),
                                    coolTargetControl=resources.getRes("northCoolTempTarget"),
                                    fanControl=resources.getRes("northFan"),
                                    thermostatUnitSensor=resources.getRes("northThermostatUnitSensor"),
                                    views=views),
                            hvacBackHouse = templates.get_template("hvacWidget.html").render(label="Back house",
                                    widths=widths[1],
                                    templates=templates,
                                    tempSensor=resources.getRes("backHouseTemp"),
                                    heatTargetControl=resources.getRes("backHeatTempTarget"),
                                    coolTargetControl=resources.getRes("backCoolTempTarget"),
                                    fanControl=resources.getRes("backFan"),
                                    thermostatUnitSensor=resources.getRes("backThermostatUnitSensor"),
                                    views=views),
                            modeResources=resources.getResList(["vacationMode", "guestMode",]),
                            alertResources=resources.getResList(["alertServices", "alertDoorbell", "alertSpa", "alertDoors", "alertMotion"]),
                            sendResources=resources.getResList(["smsAlerts", "appAlerts", "iftttAlerts",]),
                            powerNowResources=resources.getResList(["solar.inverters.stats.power", "loads.stats.power", "solar.stats.netPower",
                                                                    "solar.inverters.stats.avgVoltage",]),
                            powerStatsResources=resources.getResList(["solar.inverters.stats.dailyEnergy", "loads.stats.dailyEnergy", "solar.stats.netDailyEnergy",
                                                                      "solar.inverters.stats.lifetimeEnergy",]),
                            loadResources=resources.getResList(["loads.lights.power", "loads.plugs.power", "loads.appliance1.power", "loads.appliance2.power",
                                                                 "loads.ac.power",
                                                                 "loads.cooking.power", "loads.pool.power", "loads.backhouse.power", "loads.carcharger.power",
                                                                 ]),
                            tempResources=resources.getResList(["poolEquipTemp", "atticTemp", "garageTemp",
                                                                "solar.inverters.stats.avgTemp", "solar.optimizers.stats.avgTemp", "maxTemp", "minTemp",
                                                                "dewpoint", ]),
                            weatherResources=resources.getResList(["humidity", "barometer",]),
                            windResources=resources.getResList(["windSpeed", "windDir", ]),
                            rainResources=resources.getResList(["rainDay", "rainHour", "rainMinute",]),
                            doorResources=resources.getResList(["frontDoor", "familyRoomDoor", "masterBedroomDoor",
                                                                "garageDoor", "garageBackDoor", "garageHouseDoor", "backHouseDoor",
                                                                "drivewayMotionSensor", "frontPorchMotionSensor", "deckMotionSensor", "backHouseMotionSensor"]),
                            garageResources=resources.getResList(["recircPump", "charger", "loads.carcharger.power"]),
                            familyRoomResources=resources.getResList(["familyRoomLamp", "fireplace", "fireplaceVideo"]),
                            holidayResources=resources.getResList(["holidayLights", "holiday",
                                                                   # "halloween", "halloweenVideo",
                                                                   "xmasTree", "xmasTreePattern", "xmasWindowLights",
                                                                   "xmasFireplaceLights", "xmasBeamLights", "xmasBackLights"]),
                            views=views)
    return reply
