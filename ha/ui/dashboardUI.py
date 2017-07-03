insideTemp = "diningRoomTemp"
outsideTemp = "edisonTemp"
poolTemp = "poolTemp"

from jinja2 import FileSystemLoader
from ha import *

def dashboardUI(resources, templates, views):
    with resources.lock:
        screenWidth = 1280
        labelWidth = 180
        columnWidth = screenWidth/2
        columnWidths = [columnWidth, [labelWidth, 200, 260]]
        widths = [screenWidth, [columnWidths, columnWidths]]
        groupTemplate = templates.get_template("group.html")
        timeGroup = groupTemplate.render(templates=templates, views=views, widths=columnWidths, 
                            group=["Time", []], details=False, name=True, link=True) + \
                    templates.get_template("timeWidget.html").render(
                            widths=[columnWidth, labelWidth],
                            templates=templates,
                            date=resources["theDateDayOfWeek"],
                            time=resources["theTimeAmPm"],
                            sunrise=resources["sunrise"],
                            sunset=resources["sunset"],
                            views=views)
        weatherGroup = groupTemplate.render(templates=templates, views=views, widths=columnWidths, 
                            group=["Weather", []], details=False, name=True, link=True) + \
                    templates.get_template("weatherWidget.html").render(
                            widths=[columnWidth, labelWidth],
                            templates=templates,
                            temp=resources[outsideTemp],
                            humidity=resources["humidity"],
                            barometer=resources["barometer"],
                            views=views)
        poolGroup = groupTemplate.render(templates=templates, views=views, widths=columnWidths, 
                            group=["Pool", []], details=False, name=True, link=True) + \
                    templates.get_template("poolPumpWidget.html").render(
                            templates=templates, 
                            widths=columnWidths, 
                            poolPumpControl=resources.getRes("poolPump"),
                            poolPumpFlowSensor=resources.getRes("poolPumpFlow"),
                            nSetValues=5, 
                            views=views) + \
                    templates.get_template("spaWidget.html").render(
                            templates=templates, 
                            widths=columnWidths, 
                            spa=resources.getRes("spa"), 
                            spaTemp=resources.getRes("spaTemp"),
                            spaTempTarget=resources.getRes("spaTempTarget"),
                            nSetValues=3, 
                            views=views) + \
                    groupTemplate.render(templates=templates, views=views, widths=columnWidths, 
                            group=["Pool", resources.getResList(["poolTemp", "spaFill", "spaFlush", "spaDrain", 
                                                    "filterSequence", "cleanSequence", "flushSequence"])],
                            details=False, name=False, link=False)
        xmasGroup = groupTemplate.render(templates=templates, views=views, widths=columnWidths, 
                            group=["Xmas", resources.getResList(["xmasLights", "xmasTree"])],
                            details=False, name=True, link=True)
        lightsGroup = groupTemplate.render(templates=templates, views=views, widths=columnWidths, 
                            group=["Lights", resources.getResList(["porchLights", "frontLights", "backLights", "bedroomLights", 
                                                       "poolLight", "spaLight"])],
                            details=False, name=True, link=True)
        shadesGroup = groupTemplate.render(templates=templates, views=views, widths=columnWidths, 
                            group=["Shades", resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"])],
                            details=False, name=True, link=True)
        hvacGroup = groupTemplate.render(templates=templates, views=views, widths=columnWidths, 
                            group=["Hvac", []], details=False, name=True, link=True) + \
                    templates.get_template("hvacWidget.html").render(label="Living area",
                            widths=columnWidths,
                            templates=templates,
                            tempSensor=resources.getRes("diningRoomTemp"), 
                            heatTargetControl=resources.getRes("southHeatTempTarget"), 
                            coolTargetControl=resources.getRes("southCoolTempTarget"), 
                            thermostatControl=resources.getRes("southThermostat"), 
                            thermostatUnitSensor=resources.getRes("southThermostatUnitSensor"),
                            indent=8,
                            bullet="- ",
                            views=views) + \
                    templates.get_template("hvacWidget.html").render(label="Bedrooms",
                            widths=columnWidths,
                            templates=templates,
                            tempSensor=resources.getRes("masterBedroomTemp"), 
                            heatTargetControl=resources.getRes("northHeatTempTarget"), 
                            coolTargetControl=resources.getRes("northCoolTempTarget"), 
                            thermostatControl=resources.getRes("northThermostat"), 
                            thermostatUnitSensor=resources.getRes("northThermostatUnitSensor"),
                            indent=8,
                            bullet="- ",
                            views=views) + \
                    templates.get_template("hvacWidget.html").render(label="Back house",
                            widths=columnWidths,
                            templates=templates,
                            tempSensor=resources.getRes("backHouseTemp"), 
                            heatTargetControl=resources.getRes("backHeatTempTarget"), 
                            coolTargetControl=resources.getRes("backCoolTempTarget"), 
                            thermostatControl=resources.getRes("backThermostat"), 
                            thermostatUnitSensor=resources.getRes("backThermostatUnitSensor"),
                            indent=8,
                            bullet="- ",
                            views=views)
        sprinklersGroup = groupTemplate.render(templates=templates, views=views, widths=columnWidths, 
                            group=["Sprinklers", resources.getResList(["backLawnSequence", "gardenSequence", "sideBedSequence", "backBedSequence", "frontLawnSequence"])],
                            details=False, name=True, link=True)
        powerGroup = groupTemplate.render(templates=templates, views=views, widths=columnWidths, 
                            group=["Power", []], details=False, name=True, link=True) + \
                    templates.get_template("powerWidget.html").render(
                            widths=[columnWidth, labelWidth],
                            templates=templates,
                            power=resources["currentPower"],
                            load=resources["currentLoad"],
                            voltage=resources["currentVoltage"],
                            energy=resources["todaysEnergy"],
                            lifetime=resources["lifetimeEnergy"],
                            views=views)
        return templates.get_template("dashboard.html").render(script="",
                            templates=templates,
                            widths=widths,
                            timeGroup=timeGroup,
                            weatherGroup=weatherGroup,
                            poolGroup=poolGroup,
                            lightsGroup=lightsGroup,
                            shadesGroup=shadesGroup,
                            hvacGroup=hvacGroup,
                            sprinklersGroup=sprinklersGroup,
                            powerGroup=powerGroup,
                            views=views)

