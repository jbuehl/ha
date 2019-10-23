
from jinja2 import FileSystemLoader
from ha import *

def solarUI(resources, templates, views):
    with resources.lock:
        optimizers = []
        opts = resources.getGroup("Optimizers")
        for opt in opts:
            if opt.name[-5:] == "power":
                if opt.name[-14:-6] in ["100F71E5", "100F7255"]:
                    panel = ["ppanel", opt.location[0]+18, opt.location[1]-17]
                else:
                    panel = ["lpanel", opt.location[0]+1, opt.location[1]+1]
                optimizers.append([opt, resources.getRes(opt.name[0:-5]+"temp"), panel])
        return templates.get_template("solar.html").render(script="",
                            dayOfWeek=resources.getRes("theDayOfWeek"),
                            date=resources.getRes("theDate"),
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            sunrise=resources.getRes("sunrise"),
                            sunset=resources.getRes("sunset"),
                            latitude="%7.3f "%(abs(latLong[0])+.0005)+("N" if latLong[0]>0 else "S"),
                            longitude="%7.3f "%(abs(latLong[1])+.0005)+("E" if latLong[1]>0 else "W"),
                            elevation="%d ft"%(elevation),
                            airTemp=resources.getRes(outsideTemp),
                            inverterTemp=resources.getRes("solar.inverters.stats.avgTemp"),
                            roofTemp=resources.getRes("solar.optimizers.stats.avgTemp"),
                            voltage=resources.getRes("solar.inverters.stats.avgVoltage"),
                            solar=resources.getRes("solar.inverters.stats.power"),
                            load=resources.getRes("loads.stats.power"),
                            net=resources.getRes("solar.stats.netPower"),
                            dailySolar=resources.getRes("solar.inverters.stats.dailyEnergy"),
                            dailyLoad=resources.getRes("loads.stats.dailyEnergy"),
                            dailyNet=resources.getRes("solar.stats.netDailyEnergy"),
                            lifetimeSolar=resources.getRes("solar.inverters.stats.lifetimeEnergy"),
                            inverters=resources.getGroup("Inverters"),
                            optimizers=optimizers,
                            views=views)
