rootDir = "/root/"
dataDir = rootDir+"data/"
audioDir = "audio/"
gpsFileName = dataDir+"gps.json"
diagFileName = dataDir+"diags.json"
imuFileName = dataDir+"9dof.json"
audioFileName = audioDir+"audio.json"

displayDevice = "/dev/fb0"
inputDevice = "/dev/input/event0"
fontName = "FreeSansBold.ttf"
fontPath = "/root/.fonts/"
imageDir = "/root/images/"
compassImageDir = "/root/compass/"
dashCamImageDir = "/root/data/photos/"
dashCamVideoDir = "/root/data/videos/"
dashCamInterval = 10
# dashCamStillResolution = (2592, 1944)    # V1
dashCamStillResolution = (3280, 2464)    # V2
dashCamVideoResolution = (1920, 1080)

import time
import threading
import picamera
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

# dash cam preview
def dashCamPreview(container):
    if dashCam:
        dashCam.resolution = dashCamStillResolution
        dashCam.start_preview(fullscreen=False, window = container.getSizePos())

# dash cam capture
def dashCamCapture(button):
    if dashCam:
        if button.altContent:
            button.altContent.render(display)
        dashCam.capture(dashCamImageDir+time.strftime("%Y%m%d%H%M%S")+".jpg")
        button.content.render(display)

# dash cam recording
def dashCamRecord(button):
    global recording
    if dashCam:
        if recording:
            dashCam.stop_recording()
            dashCam.resolution = dashCamStillResolution
            button.content.render(display)
            recording = False
        else:
            dashCam.resolution = dashCamVideoResolution
            dashCam.start_recording(dashCamVideoDir+time.strftime("%Y%m%d%H%M%S")+".h264")
            if button.altContent:
                button.altContent.render(display)
            recording = True
#    dashCam.annotate_size = 120
#    dashCam.annotate_foreground = picamera.Color('red')
#    dashCam.annotate_text = time.strftime("%Y %m %d %H:%M:%S")

# dash cam stop recording
def dashCamStopRec(button):
    if dashCam:
        dashCam.stop_recording()
        dashCam.resolution = dashCamStillResolution
#    dashCam.annotate_text = ""

if __name__ == "__main__":

    # interfaces
    gpsInterface = FileInterface("gpsInterface", fileName=gpsFileName, readOnly=True, event=stateChangeEvent, defaultValue=0.0)
    timeInterface = TimeInterface("timeInterface", gpsInterface, clock="utc")
    diagInterface = FileInterface("diagInterface", fileName=diagFileName, readOnly=True, event=stateChangeEvent)
    i2cInterface = I2CInterface("i2cInterface", bus=1, event=stateChangeEvent)
    tc74Interface = TC74Interface("tc74Interface", i2cInterface)
    tempInterface = TempInterface("tempInterface", tc74Interface, sample=1)
    audioInterface = AudioInterface("audioInterface", event=stateChangeEvent)
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
    positionSensors = [
        Sensor("latitude", gpsInterface, "Lat", label="Latitude", type="Lat"),
        Sensor("longitude", gpsInterface, "Long", label="Longitude", type="Long"),
        Sensor("altitude", gpsInterface, "GPSAlt", label="Elevation", type="Ft"),
        Sensor("nSats", gpsInterface, "Nsats", label="Satellites", type="nSats"),
    ]
    gpsDevice = Sensor("gpsDevice", gpsInterface, "GPSDevice", label="GPS device")
    gpsAltitude = Sensor("gpsAltitude", gpsInterface, "Alt", label="GPS elevation", type="Ft")

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
    display.clear(bgColor)
    face = freetype.Face(fontPath+fontName)

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
    buttonStyle = Style("buttonStyle", defaultStyle, width=100, height=90, margin=2, bgColor=color("White"))
    buttonTextStyle = Style("buttonText", textStyle, fontSize=18, bgColor=color("black"), fgColor=color("white"), padding=8)
    buttonAltStyle = Style("buttonAlt", buttonTextStyle, bgColor=color("white"), fgColor=color("black"))

    # button callback routines
    def doNothing(button, display):
        return

    # layout
    dashCamWindow = Div("dashCamWindow", containerStyle, width=396, height=296, margin=2)
    screen = Div("screen", containerStyle, [
                    Span("heading", containerStyle, [
                            Text("time", timeStyle, display=display, resource=timeResource),
                            Text("ampm", ampmStyle, display=display, resource=ampmResource),
                            Text("timeZone", tzStyle, display=display, resource=timeZoneResource),
                            Element("filler", Style("fillerStyle", defaultStyle, width=20, height=90), display=display),
                            Div("text", containerStyle, [
                                Text("dayOfWeek", dateStyle, display=display, resource=dayOfWeekResource),
                                Text("date", dateStyle, display=display, resource=dateResource),
                                ]),
                            Text("temp", tempStyle, display=display, resource=outsideTemp),
                            ]),
                    Span("body", containerStyle, [
                        Div("sensors", containerStyle, [
                            Span("velocity", containerStyle, [
                                Div("velocitySensors", containerStyle, [
                                    Span(sensor.name, containerStyle, [
                                        Text(sensor.name+"Label", labelStyle, sensor.label),
                                        Text(sensor.name+"Value", velocityStyle, display=display, resource=sensor),
                                        ],
                                    )
                                    for sensor in velocitySensors]),
                                CompassImage("compassImage", defaultStyle, headingSensor, compassImageDir, display=display, resource=headingSensor),
                                ]),
                            Div("positionSensors", containerStyle, [
                                Span(sensor.name, containerStyle, [
                                    Text(sensor.name+"Label", labelStyle, sensor.label),
                                    Text(sensor.name+"Value", valueStyle, display=display, resource=sensor),
                                    ],
                                )
                                for sensor in positionSensors]),
                            ]),
#                        Div("engineSensors", containerStyle, [
#                            Span(sensor.name, containerStyle, [
#                                Text(sensor.name+"Label", labelStyle, sensor.label),
#                                Text(sensor.name+"Value", valueStyle, display=display, resource=sensor),
#                                ],
#                            )
#                            for sensor in engineSensors]),
                        dashCamWindow,
                        ]),
                    Span("buttons", containerStyle, [
                        Button("captureButton", buttonStyle, display=display,
                            content=Image("button0Content", buttonTextStyle, imageDir+"capture.png", width=96, height=86),
                            altContent=Image("button0AltContent", buttonAltStyle, imageDir+"capture-invert.png", width=96, height=86),
                            onPress=dashCamCapture,
                            ),
                        Button("recordButton", buttonStyle, display=display,
                            content=Image("button1Content", buttonTextStyle, imageDir+"record.png", width=96, height=86),
                            altContent=Image("button1AltContent", buttonAltStyle, imageDir+"stop-record.png", width=96, height=86),
                            onPress=dashCamRecord,
                            ),
                        Button("button2", buttonStyle, display=display,
                            content=Text("button2Content", buttonTextStyle, "", width=96, height=86),
                            ),
                        Button("button3", buttonStyle, display=display,
                            content=Text("button3Content", buttonTextStyle, "", width=96, height=86),
                            ),
                        Button("button4", buttonStyle, display=display,
                            content=Text("button4Content", buttonTextStyle, "", width=96, height=86),
                            ),
                        Button("button5", buttonStyle, display=display,
                            content=Text("button5Content", buttonTextStyle, "", width=96, height=86),
                            ),
                        Button("gpsAltButton", buttonStyle, display=display,
                            content=Text("gpsAltitude", buttonTextStyle, resource=gpsAltitude, width=96, height=86),
                            ),
                        Button("gpsButton", buttonStyle, display=display,
                            content=Text("gpsDevice", buttonTextStyle, resource=gpsDevice, width=96, height=86),
                            ),
                        ]),
                     ])

    screen.arrange()
    screen.render(display)

    # start the dash cam
    dashCamPreview(dashCamWindow)

    # start the display
    display.start(block=True)
