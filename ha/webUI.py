#!/usr/bin/env python
# coding=utf-8

import os
import cherrypy
import json
from jinja2 import Environment, FileSystemLoader

from HCClasses import *
from htmlUtils import *

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class WebUI(HCUI):
    def __init__(self, theName, theApp, theInterface, theResources, theSchedule):
        HCUI.__init__(self, theName, theApp, theInterface, theResources)
        self.schedule = theSchedule

        globalConfig = {
            'server.socket_port': self.app.httpPort,
            'server.socket_host': "0.0.0.0",
            }
        appConfig = {
            '/css': {
                'tools.staticdir.on': True,
                'tools.staticdir.root': os.path.join(BASE_DIR, "static"),
                'tools.staticdir.dir': "css",
            },
            '/js': {
                'tools.staticdir.on': True,
                'tools.staticdir.root': os.path.join(BASE_DIR, "static"),
                'tools.staticdir.dir': "js",
            },
            '/favicon.ico': {
                'tools.staticfile.on': True,
                'tools.staticfile.filename': os.path.join(BASE_DIR, "static/favicon.ico"),
            },
        }    
        cherrypy.config.update(globalConfig)
        root = WebRoot(self.name, self.app, self.resources, self.schedule)
        cherrypy.tree.mount(root, "/", appConfig)

    def start(self):
        cherrypy.engine.start()

    def block(self):
        cherrypy.engine.block()

class WebRoot(object):
    def __init__(self, theName, theApp, theResources, theSchedule):
        self.name = theName
        self.app = theApp
        self.resources = theResources
        self.schedule = theSchedule

        self.env = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR, 'templates')))

    # Solar
    
    @cherrypy.expose
    def solar(self, details="Hide", history="Hide"):
        html = ""
        html += htmlScript(src="js/jquery.js")
        html += updateScript(60)
        html += self.solarSummary(details, history)
        solarInterface = self.resources.resources["currentPower"].interface
        if details == "Show":
            html += self.solarDetails(solarInterface)
        if history == "Show":
            html += self.solarHistory(solarInterface)
        html = htmlDiv(html, _class="container")
        html = htmlDocument(htmlBody(html, ["Solar"]), css="/css/solar.css")
        return html        

    def solarSummary(self, details, history):
        names = ""
        names += htmlDiv("Current power", _class="label")
        names += htmlDiv("Energy today", _class="label")
        names += htmlDiv("Lifetime energy", _class="label")
        names += htmlDiv("Details", _class="label")
        names += htmlDiv("History", _class="label")
        values = ""
        resource = self.resources.resources["currentPower"]
        state = resource.getViewState()
        values += htmlDiv(state, _class=resource.type+"_"+state, _id=resource.name)
        resource = self.resources.resources["todaysEnergy"]
        state = resource.getViewState()
        values += htmlDiv(state, _class=resource.type+"_"+state, _id=resource.name)
        resource = self.resources.resources["totalEnergy"]
        state = resource.getViewState()
        values += htmlDiv(state, _class=resource.type+"_"+state, _id=resource.name)
        values += htmlForm(htmlInput("submit", name="details", value=("Show" if details == "Hide" else "Hide")), name="control", action="", method="get")
        values += htmlForm(htmlInput("submit", name="history", value=("Show" if history == "Hide" else "Hide")), name="control", action="", method="get")
        summary = htmlDiv(htmlDiv(names, _class="names")+htmlDiv(values, _class="values"), _class="section")
        return summary
    
    def solarHistory(self, solarInterface):
        history = HCSensor("history", self.app, solarInterface, ("history")).getState()
        names = ""
        for day in sorted(history.keys()):
            names += htmlDiv(day, _class="label")
        values = ""
        for day in sorted(history.keys()):
            values += htmlDiv("%7.3f"%history[day], _class="label")
        html = htmlDiv(htmlDiv(names, _class="names")+htmlDiv(values, _class="values"), _class="section")
        return html
    
    def solarDetails(self, solarInterface):
        inverters = HCSensor("inverters", self.app, solarInterface, ("inverters")).getState()
        solarTbl = []
        for inverter in inverters:
            invData = HCSensor("inverter", self.app, solarInterface, ("inverters", inverter)).getState()
            solarTbl.append([htmlDiv(inverter, "data"),
                             "", 
                             htmlDiv(invData["serial"], "data"), 
                             htmlDiv("%5.1f"%invData["Vac"], "data"), 
                             htmlDiv("%5.1f"%invData["Iac"], "data"), 
                             htmlDiv("%7.1f"%invData["Pac"], "data"), 
                             htmlDiv("%7.1f"%invData["Eday"], "data"), 
                             htmlDiv("%d"%(invData["Temp"]+.5), "data")])
            for string in invData["strings"]:
                strData = HCSensor("string", self.app, solarInterface, ("strings", string)).getState()
                solarTbl.append(["", htmlDiv(string, "data")])
                for optimizer in strData["optimizers"]:
                    optData = HCSensor("optimizer", self.app, solarInterface, ("optimizers", optimizer)).getState()
                    arrayData = HCSensor("array", self.app, solarInterface, ("arrays", optData["array"])).getState()
                    modData = HCSensor("module", self.app, solarInterface, ("modules", optData["module"])).getState()
                    solarTbl.append(["",
                                     htmlDiv(optimizer, "data"), 
                                     htmlDiv(optData["serial"], "data"), 
                                     htmlDiv("%5.1f"%optData["Vmod"], "data"), 
                                     htmlDiv("%5.1f"%optData["Imod"], "data"), 
                                     htmlDiv("%7.1f"%(optData["Vmod"]*optData["Imod"]), "data"), 
                                     htmlDiv("%7.1f"%optData["Eday"], "data"), 
                                     htmlDiv("%d"%(optData["Temp"]+.5), "data"),
                                     htmlDiv("%d"%arrayData["azimuth"], "data"), 
                                     htmlDiv("%5.1f"%arrayData["tilt"], "data"), 
                                     htmlDiv("%d"%modData["Pmpp"], "data"), 
                                     ])
        html = htmlBreak()+htmlHeading(["Solar details"], 2)+htmlTable(solarTbl, ["Inverter", "Optimizer", "Serial", "Volts", "Amps", "Power", "Energy", "Temp", "Azimuth", "Tilt", "Pmpp"], 
                                       [100, 100, 100, 80, 80, 80, 80, 80, 80, 80, 80], border=1)
        html = htmlDiv(html, _class="section")
        return html

    # Schedule
        
    @cherrypy.expose
    def sched(self):
        html = htmlDocument(htmlBody(self.schedule.__str__(delim=htmlBreak()), ["Schedule"]), css="/css/default.css")
        return html        

    # Pool
    
    @cherrypy.expose
    def pool(self, action=None, resource=None):
        template = self.env.get_template("pool2.html")
        if resource:
            self.resources.resources[resource].setViewState(action)
        resources = self.resources.getResList(["poolTemp", "spaTemp", "outsideAirTemp", "poolPump", "spa", "spaHeater", "spaBlower", "poolCleaner", "poolLight", "spaLight"])
        return template.render(resources=resources)

    # Everything
    
    @cherrypy.expose
    def index(self, action=None, resource=None):
        if resource:
            self.resources.resources[resource].setViewState(action)
        html = ""
        html += htmlScript(src="js/jquery.js")
        html += updateScript(30)
        html += self.group("Temperature")
        html += self.group("Solar")
        html += self.group("Power")
        html += self.group("Pool")
        html += self.group("Lights")
        html += self.group("Doors")
        html += self.group("Sprinklers")
#        html += self.solarDetails(self.resources.resources["currentPower"].interface)
        html = htmlDocument(htmlBody(html, ["Home Control"]), css="/css/default.css")
        return html        

    def group(self, theGroup, details=True):
        resources = self.resources.getGroup(theGroup)
        html = htmlBreak()+htmlHeading([theGroup], 2)+htmlTable(self.groupTbl(resources, details), [], [200, 120, 320, 80, 80, 240, 80], border=0)
        return html

    def groupTbl(self, resources, details):
        resTbl = []
        for resource in resources:
            if resource.view:
                state = resource.getViewState()
            else:
                state = resource.printState()
            resTblLine = [htmlDiv(resource.label, _class="label"), 
                           htmlDiv(state, _class=resource.type+"_"+state, _id=resource.name),
                           htmlDiv(self.form(resource), _class="invisible")]
            if details:
                resTblLine += [htmlDiv(resource.type.__str__(), _class="data"), 
                               htmlDiv(resource.interface.name if (resource.interface) else "", _class="data"), 
                               htmlDiv(resource.addr.__str__() if (resource.interface) else "", _class="data"), 
                               htmlDiv(resource.location.__str__() if (resource.interface) else "", _class="data")]
            resTbl.append(resTblLine)
        return resTbl
        
    def form(self, resource):
        if isinstance(resource, HCControl):
            inputs = ""
            for value in resource.view.setValues.values():
                inputs += htmlInput("submit", name="action", value=value)
#            inputs += htmlSelect(resource.view.values.values())
            inputs += htmlInput("hidden", name="resource", value=resource.name)
            return htmlForm(inputs, name="control", action="", method="get")
        else:
            return "."
    
    @cherrypy.expose
    def value(self, resource=None):
        if resource:
            return self.resources.resources[resource].getViewState()        

    @cherrypy.expose
    def update(self, _=None):
        updates = {}
        for resource in self.resources.resources:
            updates[resource] = (self.resources.resources[resource].type, self.resources.resources[resource].getViewState())
        return json.dumps(updates)        


