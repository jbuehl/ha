
from jinja2 import FileSystemLoader
from ha import *

def ipadUI(location, resources, templates, views):
    with resources.lock:
        screenWidth = 1024
        labelWidth = 194
        columnWidth = screenWidth/2
        columnWidths = [columnWidth, [labelWidth, 120, 190]]
        headerWidths = [screenWidth, [432, 180, 180, 180]]
        widths = [screenWidth, [columnWidths, columnWidths]]
        widths = [headerWidths, [screenWidth, [columnWidths, columnWidths]]]
        if location == "backhouse":
            location = "Back house"
            lightsGroup=["Lights", resources.getResList(["backLights", "poolLight", "spaLight"])]
            hvac = templates.get_template("hvacWidget.html").render(label="Inside temp",
                    widths=columnWidths,
                    templates=templates,
                    tempSensor=resources.getRes("backHouseTemp"),
                    heatTargetControl=resources.getRes("backHeatTempTarget"),
                    coolTargetControl=resources.getRes("backCoolTempTarget"),
                    fanControl=resources.getRes("backFan"),
                    thermostatUnitSensor=resources.getRes("backThermostatUnitSensor"),
                    views=views)
            shadesGroup = []
        elif location == "bedroom":
            location = "Bedroom"
            lightsGroup=["Lights", resources.getResList(["porchLights", "bedroomLights", "recircPump", "garageDoors", "houseDoors", "backHouseDoor"])]
            hvac = templates.get_template("hvacWidget.html").render(label="Inside temp",
                    widths=columnWidths,
                    templates=templates,
                    tempSensor=resources.getRes("masterBedroomTemp"),
                    heatTargetControl=resources.getRes("northHeatTempTarget"),
                    coolTargetControl=resources.getRes("northCoolTempTarget"),
                    thermostatUnitSensor=resources.getRes("northThermostatUnitSensor"),
                    views=views)
            shadesGroup=["Shades", resources.getResList(["shade1", "shade2", "shade3", "shade4"])]
        else:   # default is kitchen
            location = "Kitchen"
            lightsGroup=["Lights", resources.getResList(["porchLights", "poolLight", "spaLight"])]
            hvac = templates.get_template("hvacWidget.html").render(label="Inside temp",
                    widths=columnWidths,
                    templates=templates,
                    tempSensor=resources.getRes("diningRoomTemp"),
                    heatTargetControl=resources.getRes("southHeatTempTarget"),
                    coolTargetControl=resources.getRes("southCoolTempTarget"),
                    thermostatUnitSensor=resources.getRes("southThermostatUnitSensor"),
                    views=views)
            shadesGroup=["Shades", resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"])]
        reply = templates.get_template("ipad.html").render(script="",
                            templates=templates,
                            widths=widths,
                            location=location,
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            day=resources.getRes("theDay"),
                            pooltemp=resources.getRes("poolTemp"),
                            outtemp=resources.getRes(outsideTemp),
                            humidity=resources.getRes("humidity"),
                            spa=resources.getRes("spa"),
                            spaTemp=resources.getRes("spaTemp"),
                            spaTempTarget=resources.getRes("spaTempTarget"),
                            poolPumpControl=resources.getRes("poolPump"),
                            poolPumpFlowSensor=resources.getRes("poolPumpFlow"),
                            lightsGroup=lightsGroup,
#                           xmasGroup=["Lights", resources.getResList(["porchLights", "xmasLights", "xmasTree"])],
#                                      ["Lights", resources.getResList(["bbqLights", "backYardLights"])],
#                                      ["Lights", resources.getResList(["xmasTree", "xmasCowTree", "xmasLights"])],
                            shadesGroup=shadesGroup,
                            hvac=hvac,
                            sprinklersGroup=["Sprinklers", resources.getResList(["backLawnSequence", "gardenSequence", "backBedSequence",
                                                                                 "sideBedSequence", "frontLawnSequence", "frontBedSequence"])],
                            views=views)
    return reply
