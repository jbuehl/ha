rootDir = "/root/"
stateDir = rootDir+"state/"
dataDir = rootDir+"data/"
stateFileName = stateDir+"state.json"
gpsFileName = dataDir+"gps.json"
diagFileName = dataDir+"diags.json"
imuFileName = dataDir+"9dof.json"

displayDevice = "/dev/fb0"
inputDevice = "/dev/input/event0"
wlan = "wlan0"
uploadServer = "shadyglade.thebuehls.com"
uploadDir = "/backups/carputer/data/"
fontName = "FreeSansBold.ttf"
fontPath = "/root/.fonts/"
imageDir = "/root/images/"
compassImageDir = "/root/compass/"
dashCamImageDir = dataDir+"photos/"
dashCamVideoDir = dataDir+"videos/"
dashCamInterval = 10
# dashCamStillResolution = (2592, 1944)    # V1
dashCamStillResolution = (3280, 2464)    # V2
dashCamVideoResolution = (1920, 1080)

import time
import threading
import picamera
import os
import subprocess
from ha import *
from ha.ui.displayUI import *
from ha.interfaces.fileInterface import *
from ha.interfaces.timeInterface import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.tc74Interface import *
from ha.interfaces.tempInterface import *
from ha.interfaces.audioInterface import *

# global variables
resources = None
stateChangeEvent = threading.Event()
resourceLock = threading.Lock()
display = Display("display", displayDevice, inputDevice, views)
try:
    dashCam=picamera.PiCamera()
except:
    dashCam = None
recording = False
state = {
    "wifiOn": True,
    "elevationMode": "gps",
    }
gpsAltitude = None
strmAltitude = None

def readState():
    try:
        with open(stateFileName) as stateFile:
            state = json.load(stateFile)
    except:
        pass

def writeState():
    with open(stateFileName, "w") as stateFile:
        json.dump(state, stateFile)

# dash cam preview
def dashCamPreview(container):
    if dashCam:
        dashCam.resolution = dashCamStillResolution
        dashCam.start_preview(fullscreen=False, window = container.getSizePos())

# dash cam capture
def dashCamCapture(button):
    if dashCam:
        button.setFront(1)
        button.render()
        dashCam.capture(dashCamImageDir+time.strftime("%Y%m%d%H%M%S")+".jpg")
        button.setFront(0)
        button.render()

# dash cam recording
def dashCamRecord(button):
    global recording
    if dashCam:
        if recording:
            dashCam.stop_recording()
            dashCam.resolution = dashCamStillResolution
            button.setFront(0)
            button.render()
            recording = False
#    dashCam.annotate_text = ""
        else:
            dashCam.resolution = dashCamVideoResolution
            dashCam.start_recording(dashCamVideoDir+time.strftime("%Y%m%d%H%M%S")+".h264")
            button.setFront(1)
            button.render()
            recording = True
#    dashCam.annotate_size = 120
#    dashCam.annotate_foreground = picamera.Color('red')
#    dashCam.annotate_text = time.strftime("%Y %m %d %H:%M:%S")

# change the type of elevation that is displayed
def toggleElevation(button):
    if state["elevationMode"] == "gps":
        with resourceLock:
            elevation.sensor = srtmAltitude
        state["elevationMode"] = "srtm"
        button.setFront(1)
    else:
        with resourceLock:
            elevation.sensor = gpsAltitude
        state["elevationMode"] = "gps"
        button.setFront(0)
    button.elementList[button.frontElement].render()
    writeState()

# upload data
def uploadData(button):
    button.setFront(1)
    button.render()
    cmd = "rsync -av "+dataDir+"* "+uploadServer+":"+uploadDir
    uplog = subprocess.check_output(cmd, shell=True)
    button.setFront(0)
    button.render()

def wifiOn():
    os.system("ifconfig "+wlan+" up")
    state["wifiOn"] = True
    writeState()

def wifiOff():
    os.system("ifconfig "+wlan+" down")
    state["wifiOn"] = False
    writeState()

# return the current wifi SSID
def getSSID():
    try:
        return subprocess.check_output("iwconfig "+wlan+"|grep ESSID", shell=True).strip("\n").split(":")[-1].split("/")[0].strip().strip('"')
    except:
        return ""

# return the current wifi IP addr
def getIPAddr():
    try:
        return subprocess.check_output("ifconfig "+wlan+"|grep inet\ ", shell=True).strip("\n").split()[1]
    except:
        return ""

# return the up time
def getUptime():
    try:
        return " ".join(c for c in subprocess.check_output("uptime", shell=True).strip("\n").split(",")[0].split()[2:])
    except:
        return ""

def watchWifi(button):
    def checkWifi():
        while True:
            if state["wifiOn"]:
                ssid = getSSID()
                if ssid == "off":
                    button.setFront(2)
                else:
                    button.setFront(1)
            else:
                button.setFront(0)
            button.elementList[button.frontElement].render()
            time.sleep(1)
    wifiThread = threading.Thread(target=checkWifi)
    wifiThread.start()

# turn wifi on and off
def toggleWifi(button):
    if state["wifiOn"]:
        wifiOff()
    else:
        wifiOn()

# sensor that is a link to another sensor
class LinkSensor(Sensor):
    def __init__(self, name, interface, addr, sensor, group="", type="sensor", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.sensor = sensor

    def getState(self):
        return self.sensor.getState()

# sensor that returns an OS stat
class OSSensor(Sensor):
    def __init__(self, name, interface, addr, group="", type="sensor", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)

    def getState(self):
        if self.addr == "ssid":
            return getSSID()
        elif self.addr == "ipAddr":
            return getIPAddr()
        elif self.addr == "uptime":
            return getUptime()
        else:
            return ""

if __name__ == "__main__":
    # get the persistent state
    readState()

    # interfaces
    gpsInterface = FileInterface("gpsInterface", fileName=gpsFileName, readOnly=True, event=stateChangeEvent, defaultValue=0.0)
    timeInterface = TimeInterface("timeInterface", gpsInterface, clock="utc")
    diagInterface = FileInterface("diagInterface", fileName=diagFileName, readOnly=True, event=stateChangeEvent)
    i2cInterface = I2CInterface("i2cInterface", bus=1, event=stateChangeEvent)
    tc74Interface = TC74Interface("tc74Interface", i2cInterface)
    tempInterface = TempInterface("tempInterface", tc74Interface, sample=1)
#    dashCamInterface = FileInterface("dashCamInterface", fileName=dashCamFile, event=stateChangeEvent)

    # time sensors
    timeResource = Sensor("time", timeInterface, "%-I:%M", type="time", label="Time")
    ampmResource = Sensor("ampm", timeInterface, "%p", type="time", label="AmPm")
    dateResource = Sensor("date", timeInterface, "%B %-d %Y", type="date", label="Date")
    dayOfWeekResource = Sensor("dayOfWeek", timeInterface, "%A", type="date", label="Day of week")
    timeZoneResource = Sensor("timeZone", timeInterface, "timeZoneName", label="Time zone")

    # GPS sensors
    headingSensor = Sensor("heading", gpsInterface, "Hdg", label="Heading", type="int3")
    velocitySensors = [
        Sensor("speed", gpsInterface, "Speed", label="Speed", type="MPH"),
        headingSensor,
    ]
    gpsAltitude = Sensor("gpsAltitude", gpsInterface, "GPSAlt")
    srtmAltitude = Sensor("srtmAltitude", gpsInterface, "Alt")
    elevation = LinkSensor("elevation", None, None, None, label="Elevation", type="Ft")
    if state["elevationMode"] == "gps":
        elevation.sensor = gpsAltitude
    else:
        elevation.sensor = srtmAltitude
    positionSensors = [
        Sensor("latitude", gpsInterface, "Lat", label="Latitude", type="Lat"),
        Sensor("longitude", gpsInterface, "Long", label="Longitude", type="Long"),
        elevation,
        Sensor("nSats", gpsInterface, "Nsats", label="Satellites", type="nSats"),
    ]
    gpsDevice = Sensor("gpsDevice", gpsInterface, "GPSDevice", label="GPS device")

    # OS stat sensors
    osStatSensors = [
        OSSensor("SSID", None, "ssid"),
        OSSensor("IPAddr", None, "ipAddr"),
        OSSensor("uptime", None, "uptime"),
    ]
    # engine sensors
    engineSensors = [
#        Sensor("speed", diagInterface, "Speed", label="Speed", type="MPH"),
        Sensor("rpm", diagInterface, "Rpm", label="RPM", type="RPM"),
        Sensor("battery", diagInterface, "Battery", label="Battery", type="V"),
        Sensor("intakeTemp", diagInterface, "IntakeTemp", label="Intake temp", type="tempC"),
        Sensor("coolantTemp", diagInterface, "WaterTemp", label="Water temp", type="tempC"),
#        Sensor("airPressure", diagInterface, "Barometer", label="Barometer", type="barometer"),
        Sensor("runTime", diagInterface, "RunTime", label="Run time", type="Secs"),
        Sensor("diagCodes", diagInterface, "DiagCodes", label="Diag codes", type="diagCode"),
    ]
    outsideTemp = Sensor("outsideTemp", tempInterface, 0x4e, label="Outside temp", type="tempF")

    # dash cam
#    dashCam = Sensor("dashCam", dashCamInterface, type="image")

    # Start interfaces
    gpsInterface.start()
    diagInterface.start()
#    ndofInterface.start()
    tempInterface.start()

    # initialization
    fgColor = color("Yellow")
    bgColor = color("Black")
    face = freetype.Face(fontPath+fontName)
    display.clear(bgColor)

    # styles
    defaultStyle = Style("defaultStyle", bgColor=bgColor, fgColor=fgColor)
    textStyle = Style("textStyle", defaultStyle, face=face, fontSize=24, fgColor=color("Cyan"))
    timeStyle = Style("timeStyle", textStyle, fontSize=80, width=240, height=90, fgColor=color("Yellow"), just=1)
    ampmStyle = Style("ampmStyle", timeStyle, fontSize=32, width=60, height=90)
    tzStyle = Style("tzStyle", timeStyle, fontSize=32, width=80, height=90)
    dateStyle = Style("dateStyle", textStyle, fontSize=24, width=220, height=36)
    tempStyle = Style("tempStyle", textStyle, fontSize=72, width=180, height=90)
    labelStyle = Style("labelStyle", textStyle, fontSize=32, width=170, height=50, fgColor=color("Cyan"))
    valueStyle = Style("valueStyle", textStyle, fontSize=32, width=230, height=50, fgColor=color("LightYellow"))
    velocityStyle = Style("velocityStyle", valueStyle, width=130)
    compassStyle = Style("compassStyle", defaultStyle, width=100, height=50)
    containerStyle = Style("containerStyle", defaultStyle)
    buttonStyle = Style("buttonStyle", defaultStyle, width=100, height=90, margin=2, bgColor=color("Gray"))
    buttonTextStyle = Style("buttonTextStyle", textStyle, fontSize=18, width=96, height=86, bgColor=color("black"), fgColor=color("white"), padding=8)
    buttonImageStyle = Style("buttonImageStyle", defaultStyle, width=96, height=86)
    osStatStyle = Style("networkStatStyle", textStyle, fontSize=18, width=200, height=30, margin=1, fgColor=color("gray"))

    # button icons
    captureIcon = Image("captureIcon", buttonImageStyle, imageDir+"capture.png")
    captureInvertIcon = Image("captureInvertIcon", buttonImageStyle, imageDir+"capture-invert.png")
    recordIcon = Image("recordIcon", buttonImageStyle, imageDir+"record.png")
    recordInvertIcon = Image("recordInvertIcon", buttonImageStyle, imageDir+"stop-record.png")
    elevationGpsIcon = Image("elevationGpsIcon", buttonImageStyle, imageDir+"elevation-gps.png")
    elevationSrtmIcon = Image("elevationSrtmIcon", buttonImageStyle, imageDir+"elevation-srtm.png")
    uploadIcon = Image("uploadIcon", buttonImageStyle, imageDir+"upload.png")
    uploadInvertIcon = Image("uploadInvertIcon", buttonImageStyle, imageDir+"upload-invert.png")
    wifiOffIcon = Image("wifiOffIcon", buttonImageStyle, imageDir+"wifi-off.png")
    wifiConnectIcon = Image("wifiConnectIcon", buttonImageStyle, imageDir+"wifi-connect.png")
    wifiDisconnectIcon = Image("wifiDisconnectIcon", buttonImageStyle, imageDir+"wifi-disconnect.png")

    # lay out the screen
    dashCamWindow = Div("dashCamWindow", containerStyle, width=396, height=296, margin=2)
    wifiButton = Button("wifiButton", buttonStyle,
                            [wifiOffIcon, wifiConnectIcon, wifiDisconnectIcon],
                            onPress=toggleWifi,
                            )
    screen = Div("screen", containerStyle, [
                    Span("heading", containerStyle, [
                            Text("time", timeStyle, resource=timeResource),
                            Text("ampm", ampmStyle, resource=ampmResource),
                            Text("timeZone", tzStyle, resource=timeZoneResource),
                            Element("filler", Style("fillerStyle", defaultStyle, width=20, height=90)),
                            Div("text", containerStyle, [
                                Text("dayOfWeek", dateStyle, resource=dayOfWeekResource),
                                Text("date", dateStyle, resource=dateResource),
                                ]),
                            Text("temp", tempStyle, resource=outsideTemp),
                            ]),
                    Span("body", containerStyle, [
                        Div("sensors", containerStyle, [
                            Span("velocity", containerStyle, [
                                Div("velocitySensors", containerStyle, [
                                    Span(sensor.name, containerStyle, [
                                        Text(sensor.name+"Label", labelStyle, sensor.label),
                                        Text(sensor.name+"Value", velocityStyle, resource=sensor),
                                        ],
                                    )
                                    for sensor in velocitySensors]),
                                CompassImage("compassImage", defaultStyle, headingSensor, compassImageDir, resource=headingSensor),
                                ]),
                            Div("positionSensors", containerStyle, [
                                Span(sensor.name, containerStyle, [
                                    Text(sensor.name+"Label", labelStyle, sensor.label),
                                    Text(sensor.name+"Value", valueStyle, resource=sensor),
                                    ],
                                )
                                for sensor in positionSensors]),
                            ]),
#                        Div("engineSensors", containerStyle, [
#                            Span(sensor.name, containerStyle, [
#                                Text(sensor.name+"Label", labelStyle, sensor.label),
#                                Text(sensor.name+"Value", valueStyle, resource=sensor),
#                                ],
#                            )
#                            for sensor in engineSensors]),
                        dashCamWindow,
                        ]),
                    Span("buttons", containerStyle, [
                        # dashcam capture
                        Button("captureButton", buttonStyle,
                            [captureIcon, captureInvertIcon],
                            onPress=dashCamCapture,
                            ),
                        # dashcam record
                        Button("recordButton", buttonStyle,
                            [recordIcon, recordInvertIcon],
                            onPress=dashCamRecord,
                            ),
                        Button("button2", buttonStyle,
                            [Text("button2Content", buttonTextStyle, "")],
                            ),
                        # elevation source
                        Button("gpsAltButton", buttonStyle,
                            [elevationGpsIcon, elevationSrtmIcon],
                            onPress=toggleElevation,
                            ),
                        # upload data
                        Button("uploadButton", buttonStyle,
                            [uploadIcon, uploadInvertIcon],
                            onPress=uploadData,
                            ),
                        # wifi status
                        wifiButton,
                        Div("osStats", containerStyle, [
                            Text(sensor.name+"Value", osStatStyle, resource=sensor)
                            for sensor in osStatSensors]
                            )
                        ])
                     ])

    screen.arrange(display)
    screen.render()

    # start the dash cam
    dashCamPreview(dashCamWindow)

    # start the wifi thread
    watchWifi(wifiButton)

    # start the display
    display.start(block=True)
