
from jinja2 import FileSystemLoader
from ha import *

def bedroomUI(resources, templates, views):
    with resources.lock:
        widths = [[320, [296, 24]], [320, [240, 80]], [320, [152, 168]]]
        northHvac = templates.get_template("hvacWidget.html").render(label="Temperature",
                            widths=widths[2],
                            templates=templates,
                            stack=True,
                            resourceTemplate=templates.get_template("resource.html"),
                            tempSensor=resources.getRes("masterBedroomTemp"),
                            heatTargetControl=resources.getRes("northHeatTempTarget"),
                            coolTargetControl=resources.getRes("northCoolTempTarget"),
                            thermostatUnitSensor=resources.getRes("northThermostatUnitSensor"),
                            views=views)
        result = templates.get_template("bedroom.html").render(script="",
                            templates=templates,
                            widths=widths,
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            day=resources.getRes("theDay"),
                            temp=resources.getRes(outsideTemp),
                            hvac=northHvac,
                            resources=resources.getResList(["porchLights", "nightLights", 
                                                            "recircPump",
                                                            "garageDoors", "houseDoors", "backHouseDoor"]),
                            views=views)
    return result
