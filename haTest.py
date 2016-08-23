import os
import time
import json
import cherrypy

dataDir = "data/"

def convertTime(timeStr):
    # convert time to a javascript unix time relative to zero
    (hour, minute, second) = timeStr.split(":")
    # round the time to 5 minute increments
    return (int(hour)*60 + (int(minute)/5)*5)*60*1000

def sumItems(itemDict, itemType):
    itemSum = 0
    for item in itemDict.keys():
        itemSum += itemDict[item][itemType]
    return itemSum

def avgItems(itemDict, itemType):
    try:
        return sumItems(itemDict, itemType)/len(itemDict)
    except ZeroDivisionError:
        return 0
            
class WebRoot(object):
    
    # Display the graph    
    @cherrypy.expose
    def index(self, date="", type="inverters", id="", attr="Pac"):
        if date == "":
            date = time.strftime("%Y%m%d", time.localtime())
        year = int(date[0:4])
        month = int(date[4:6])
        day = int(date[6:8])
        reply = """
    <!DOCTYPE html>
    <html xmlns='http://www.w3.org/1999/xhtml' xml:lang='en'>
    <head>
        <title>Solar stats</title>
        <link rel='stylesheet' type='text/css' href='css/solar.css'> 
        <script src='js/jquery.js'></script>
        <script src="js/jquery.flot.js"></script>
        <script src="js/jquery.flot.time.js"></script>
        <script src="js/jquery.flot.stack.js"></script>
    </head>
    <body>
        <div style="width: 900px">
            <div id="graph" style="width: 900px; height: 300px">
            </div>
            <div  class="caption">
                <span class="date">
                    %s
                </span>
                <span class="summary">
                    <span class="label">Current Power</span> 
                    <span id="Pac" class="KW">0.0 KW</span>
                    <span class="label">Todays Energy</span> 
                    <span id="Eday" class="KWh">0.0 KWh</span>
                    <span class="label">Lifetime Energy</span> 
                    <span id="Etot" class="MWh">0.0 MWh</span>
                </span>
            </div>
        </div>
        <script type="text/javascript">
          (function() {
		    function wattsAxisFormatter(v, axis) {
			    return v.toFixed(axis.tickDecimals) + " W";
		        }
		    function voltsAxisFormatter(v, axis) {
			    return v.toFixed(axis.tickDecimals) + " V";
		        }
		    function tempAxisFormatter(v, axis) {
			    return v.toFixed(axis.tickDecimals) + " F";
		        }

            var options = {
                yaxes: [{
                        min: 0,
                        max: 10000,           // Watts
                        tickFormatter: wattsAxisFormatter,
                        position: "left"
                    }, {
                        min: 0,
                        max: 300,           // Volts
                        tickFormatter: voltsAxisFormatter,
                        position: "right"
//                    }, {
//                        min: 0,
//                        max: 200,           // Temp F
//                        tickFormatter: tempAxisFormatter,
//                        position: "right"
                    }],
                xaxis: {
                    ticks: 18,
                    mode: "time",
                    timeformat: "%%H:%%M",
                    min: 18000000,          // 5am
                    max: 75600000           // 9pm
                    },
                grid: {
                    color: "#ffffff",
                    markings: [{y2axis: { from: 212, to: 212 }, 
                                color: "#ff8800"}],
                    markingsLineWidth: 1
                    },
                legend:{         
                    backgroundOpacity: 0.5,
                    noColumns: 0,
                    backgroundColor: "#424242",   
                    position: "nw"
					}
                };
            var annotate = function(series, units, color, offset, axis, plot, graph) {
                var last = series.length - 1;
                var pos = plot.pointOffset({x: series[last][0], y: series[last][1]+offset, yaxis: axis});
                graph.append("<div style='color: " + color + ";position:absolute;left:" + (pos.left + 4) + "px;top:" + pos.top + "px'>" + series[last][1]  + " " + units + "</div>");
                return last;
                };
            var update = function() {
                $.getJSON('state', {"date": "%s", "type": "%s", "id": "%s", "attr": "%s"}, function(data) {
                    var plot = $.plot($("#graph"), [{data: data["7F104920"], label: "7F104920", color: "#ff0000", stack:true, lines: {show:true, fill:true}}, 
                                       {data: data["7F104A16"], label: "7F104A16", color: "#00ff00", stack:true, lines: {show:true, fill:true}}, 
                                       {data: data["Volts"], yaxis:2, label: "AC Volts", color: "#ffff00"}, 
//                                       {data: data["Temp"], yaxis:3, label: "Panel temp", color: "#ff00ff"}
                                       ], 
                                       options);
                    $('#Pac').text(data["Pac"]);
                    $('#Eday').text(data["Eday"]);
                    $('#Etot').text(data["Etot"]);
                    var graph = $("#graph");
                    var last = annotate(data["7F104920"], "W", "#ff0000", 0, 1, plot, graph);
                    var last = annotate(data["7F104A16"], "W", "#00ff00", data["7F104920"][last][1], 1, plot, graph);
                    var last = annotate(data["Volts"], "V", "#ffff00", 20, 2, plot, graph);
//                    var last = annotate(data["Temp"], "F", "#ff00ff", 10, 3, plot, graph);
                    });
                };
            $.ajaxSetup({cache: false});
            update();
            setInterval(function() {
                update()
                }, 300000);
            })();
        </script>
    </body>
    </html>
"""
        return reply % (time.strftime("%b %d %Y", (year, month, day, 0, 0, 0, 0, 0, 0)), date, type, id, attr)

    # Return the current state
    @cherrypy.expose
    def state(self, date="", type="inverters", id="", attr="Pac", _=None):
        # find all the files for the specified date
        dataFiles = []
        for dataFile in os.listdir(dataDir):
            if dataFile[0:8] == date:
                dataFiles.append(dataFile)
        dataFiles.sort()
        if dataFiles == []:
            cherrypy.response.status = "400 Error"
            return "Date not found."

        # parse the arguments
        if type not in ["inverters", "optimizers"]:
            cherrypy.response.status = "400 Error"
            return "Invalid type."
        idList = id.split(",")
        attrList = attr.split(",")
#        statDict = {}
#        for attr in attrList:
#            statDict[attr] = []
        stateDict = {"inverters": {}, "optimizers": {}}
        statDict = {"7F104920": [], "7F104A16": [], "Volts": [], "Temp": [], "Pac": "0.0 KW", "Eday": "0.0 KWh", "Etot": "0.0 MWh"}
        
        seriesDict = {"data": [], "label": "", "units": "", "color": "white", "yaxis": 1, "stack": 0, "fill": 0}
        
        for dataFile in dataFiles:
            with open(dataDir+dataFile) as inFile:
                eDay = 0.0
                jsonStr = inFile.readline()
                while jsonStr != "":
                    try:
                        inDict = json.loads(jsonStr)
                        if inDict[type] != {}:
                            # update the state values
                            stateDict["inverters"].update(inDict["inverters"])
                            stateDict["optimizers"].update(inDict["optimizers"])
                            inverters = inDict[type].keys()
                            timeStamp = convertTime(inDict[type][inverters[0]]["Time"])
                            statDict["Volts"].append([timeStamp, int(avgItems(stateDict["inverters"], "Vac"))])
                            eDay += int(sumItems(inDict["inverters"], "Eac"))
                            for inv in inverters:
                                statDict[inv].append([timeStamp, inDict[type][inv]["Pac"]])
                                statDict["Pac"] = "%7.3f KW" % (sumItems(stateDict["inverters"], "Pac") / 1000)
                                statDict["Etot"] = "%7.3f MWh" % (sumItems(stateDict["inverters"], "Etot") / 1000000)
                            statDict["Temp"].append([timeStamp, int(avgItems(stateDict["optimizers"], "Temp")*9/5+32)])
                    except:
                        print jsonStr
                        raise
                    jsonStr = inFile.readline()
        statDict["Eday"] = "%7.3f KWh" % (eDay / 1000)
        statDict["Volts"].sort()
        statDict["Temp"].sort()
        return json.dumps(statDict)
        
if __name__ == "__main__":
    # set up the web server
    baseDir = os.path.abspath(os.path.dirname(__file__))
    appConfig = {
        '/css': {
            'tools.staticdir.on': True,
            'tools.staticdir.root': os.path.join(baseDir, "static"),
            'tools.staticdir.dir': "css",
        },
        '/js': {
            'tools.staticdir.on': True,
            'tools.staticdir.root': os.path.join(baseDir, "static"),
            'tools.staticdir.dir': "js",
        },
        '/images': {
            'tools.staticdir.on': True,
            'tools.staticdir.root': os.path.join(baseDir, "static"),
            'tools.staticdir.dir': "images",
        },
        '/favicon.ico': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(baseDir, "static/favicon.ico"),
        },
    }
    root = WebRoot()
    cherrypy.tree.mount(root, "/", appConfig)
    globalConfig = {
        'server.socket_port': 81,
        'server.socket_host': "0.0.0.0",
        }
    cherrypy.config.update(globalConfig)
    cherrypy.engine.start()
    cherrypy.engine.block()

