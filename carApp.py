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
dashCamImageDir = "/root/data/photos/"
dashCamVideoDir = "/root/data/videos/"
dashCamInterval = 10

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
compassImgFileNames = ["/root/compass/hdg "+hdg+".png" for hdg in ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]]
dashCam=picamera.PiCamera()
dashCam.resolution = (3280, 2464)

# dash cam preview
def dashCamPreview(container):
    dashCam.start_preview(fullscreen=False, window = container.getSizePos())

# dash cam capture
def dashCamCapture():
    dashCam.capture(dashCamImageDir+time.strftime("%Y%m%d%H%M%S")+".jpg")
    
# dash cam start recording
def dashCamStartRec():
    dashCam.resolution = (1920, 1080)
    dashCam.start_recording(dashCamVideoDir+time.strftime("%Y%m%d%H%M%S")+".h264")
#    dashCam.annotate_size = 120 
#    dashCam.annotate_foreground = picamera.Color('red')
#    dashCam.annotate_text = time.strftime("%Y %m %d %H:%M:%S")
    
# dash cam stop recording
def dashCamStopRec():
    dashCam.stop_recording()
    dashCam.resolution = (3280, 2464)
#    dashCam.annotate_text = ""
    
#def dashCamImage():
#    while True:
#        os.popen("/usr/bin/raspistill -e png -o "+dashCamFile+" -w 400 -h 300 -n")
#        time.sleep(dashCamInterval)
        
if __name__ == "__main__":

    # interfaces
    gpsInterface = FileInterface("gpsInterface", fileName=gpsFileName, readOnly=True, event=stateChangeEvent)
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
        Sensor("altitude", gpsInterface, "Alt", label="Elevation", type="Ft"),
        Sensor("nSats", gpsInterface, "Nsats", label="Satellites"),
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
        Sensor("diagCodes", diagInterface, "DiagCodes", label="Diag codes",type="diagCode"),
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
    display = Display("display", displayDevice, inputDevice, views)
    display.clear(bgColor)
    face = freetype.Face(fontPath+fontName)
    
    # styles        
    defaultStyle = Style("defaultStyle", bgColor=bgColor, fgColor=fgColor)
    textStyle = Style("textStyle", defaultStyle, face=face, fontSize=24, fgColor=color("Cyan"))
    timeStyle = Style("timeStyle", textStyle, fontSize=80, width=200, height=90, fgColor=color("Yellow"))
    ampmStyle = Style("ampmStyle", timeStyle, fontSize=32, width=80, height=90)
    tzStyle = Style("tzStyle", timeStyle, fontSize=32, width=80, height=90)
    dateStyle = Style("dateStyle", textStyle, fontSize=24, width=260, height=36)
    tempStyle = Style("tempStyle", textStyle, fontSize=72, width=180, height=90)
    labelStyle = Style("labelStyle", textStyle, fontSize=32, width=170, height=50, fgColor=color("Cyan"))
    valueStyle = Style("valueStyle", textStyle, fontSize=32, width=230, height=50, fgColor=color("LightYellow"))
    velocityStyle = Style("velocityStyle", valueStyle, width=130)
    compassStyle = Style("compassStyle", defaultStyle, width=100, height=50)
    containerStyle = Style("containerStyle", defaultStyle)
    buttonStyle = Style("buttonStyle", defaultStyle, width=100, height=90, margin=2, bgColor=color("White"))
    buttonTextStyle = Style("buttonText", textStyle, fontSize=18, bgColor=color("black"), fgColor=color("white"), padding=8)
    buttonAltStyle = Style("buttonAlt", buttonTextStyle, bgColor=color("blue"), fgColor=color("white"))
        
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
                                CompassImage("compassImage", defaultStyle, headingSensor, compassImgFileNames, display=display, resource=headingSensor),
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
#                        Image("dashCam", display=display, resource=dashCam),
                        dashCamWindow,
                        ]),
                    Span("buttons", containerStyle, [
                        Button("captureButton", buttonStyle, display=display,
                            content=Text("button0Content", buttonTextStyle, "Capture", width=96, height=86),
                            onPress=dashCamCapture,
#                            altContent=Image("volDownImageInvert", imageFile=imageDir+"icons_volumedown-02.png"),
                            ),
                        Button("startRecButton", buttonStyle, display=display,
                            content=Text("button1Content", buttonTextStyle, "Start rec", width=96, height=86),
                            onPress=dashCamStartRec,
#                            altContent=Image("volUpImageInvert", imageFile=imageDir+"icons_volumeup-02.png"),
                            ),
                        Button("stopRecButton", buttonStyle, display=display,
                            content=Text("button2Content", buttonTextStyle, "Stop rec", width=96, height=86),
                            onPress=dashCamStopRec,
#                            altContent=Image("rewImageInvert", imageFile=imageDir+"icons_rew-02.png"),
                            ),
                        Button("button3", buttonStyle, display=display,
                            content=Text("button3Content", buttonTextStyle, "", width=96, height=86),
#                            altContent=Image("playImageInvert", imageFile=imageDir+"icons_play-02.png"),
                            ),
                        Button("button4", buttonStyle, display=display,
                            content=Text("button4Content", buttonTextStyle, "", width=96, height=86),
#                            altContent=Image("pauseImageInvert", imageFile=imageDir+"icons_pause-02.png"),
                            ),
                        Button("button5", buttonStyle, display=display,
                            content=Text("button5Content", buttonTextStyle, "", width=96, height=86),
#                            altContent=Image("ffImageInvert", imageFile=imageDir+"icons_ff-02.png"),
                            ),
                        Button("button6", buttonStyle, display=display,
                            content=Text("button6Content", buttonTextStyle, "", width=96, height=86),
#                            altContent=Image("sourceImageInvert", imageFile=imageDir+"icons_source-02.png"),
                            ),
                        Button("wifiButton", buttonStyle, display=display,
                            content=Text("button7Content", buttonTextStyle, "WiFi", width=96, height=86),
#                            altContent=Image("wifiImageInvert", imageFile=imageDir+"icons_wifi-02.png"),
                            ),
                        ]),
                     ])

    screen.arrange()
    screen.render(display)

    # start the dash cam
    dashCamPreview(dashCamWindow)

    # start the display        
    display.start(block=True)
    
