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
dashCamDir = "/root/data/photos/"
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

# dash cam thread
def dashCamVideo():
    camera=picamera.PiCamera()
    camera.resolution = (3280, 2464)
    camera.start_preview(fullscreen=False, window = (400, 90, 400, 300))
    while True:
        time.sleep(dashCamInterval)
        camera.capture(dashCamDir+time.strftime("%Y%m%d%H%M%S")+".jpg")
    camera.stop_preview()
    
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
    headingSensor = Sensor("heading", gpsInterface, "Hdg", label="Heading", type="int")
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
#    audioStyle = Style("audioButton", defaultStyle, margin=2)
    buttonStyle = Style("buttonStyle", defaultStyle, width=100, height=90, margin=2, bgColor=color("White"))
#    buttonTextStyle = Style("buttonText", buttonStyle, fontSize=36, bgColor=color("white"), fgColor=color("black"), padding=8)
#    buttonAltStyle = Style("buttonAlt", buttonTextStyle, bgColor=color("blue"), fgColor=color("white"))
        
    # button callback routines
    def doNothing(button, display):
        return

    # layout
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
                        Div("dashCamPreview", containerStyle),
#                        Div("engineSensors", containerStyle, [
#                            Span(sensor.name, containerStyle, [
#                                Text(sensor.name+"Label", labelStyle, sensor.label),
#                                Text(sensor.name+"Value", valueStyle, display=display, resource=sensor),
#                                ],
#                            )
#                            for sensor in engineSensors]),
#                        Image("dashCam", display=display, resource=dashCam),
                        ], width=400, height=300),
#                    Span("buttons", containerStyle, [
#                        Button("volDownButton", buttonStyle,
#                            content=Image("volDownImage", imageFile=imageDir+"icons_volumedown-01.png"),
#                            altContent=Image("volDownImageInvert", imageFile=imageDir+"icons_volumedown-02.png"),
#                            ),
#                        Button("volUpButton", buttonStyle,
#                            content=Image("volUpImage", imageFile=imageDir+"icons_volumeup-01.png"),
#                            altContent=Image("volUpImageInvert", imageFile=imageDir+"icons_volumeup-02.png"),
#                            ),
#                        Button("rewButton", buttonStyle,
#                            content=Image("rewImage", imageFile=imageDir+"icons_rew-01.png"),
#                            altContent=Image("rewImageInvert", imageFile=imageDir+"icons_rew-02.png"),
#                            ),
#                        Button("playButton", buttonStyle,
#                            content=Image("playImage", imageFile=imageDir+"icons_play-01.png"),
#                            altContent=Image("playImageInvert", imageFile=imageDir+"icons_play-02.png"),
#                            ),
#                        Button("pauseButton", buttonStyle,
#                            content=Image("pauseImage", imageFile=imageDir+"icons_pause-01.png"),
#                            altContent=Image("pauseImageInvert", imageFile=imageDir+"icons_pause-02.png"),
#                            ),
#                        Button("ffButton", buttonStyle,
#                            content=Image("ffImage", imageFile=imageDir+"icons_ff-01.png"),
#                            altContent=Image("ffImageInvert", imageFile=imageDir+"icons_ff-02.png"),
#                            ),
#                        Button("sourceButton", buttonStyle,
#                            content=Image("sourceImage", imageFile=imageDir+"icons_source-01.png"),
#                            altContent=Image("sourceImageInvert", imageFile=imageDir+"icons_source-02.png"),
#                            ),
#                        Button("wifiButton", buttonStyle,
#                            content=Image("wifiImage", imageFile=imageDir+"icons_wifi-01.png"),
#                            altContent=Image("wifiImageInvert", imageFile=imageDir+"icons_wifi-02.png"),
#                            ),
#                        ]),
                     ])

    screen.arrange()
    screen.render(display)

    # start the dash cam
    dashCamThread = threading.Thread(target=dashCamVideo)
    dashCamThread.start()

    # start the display        
    display.start(block=True)
    
