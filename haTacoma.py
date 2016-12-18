tzOffset = -7

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
fontPath = "/usr/share/fonts/TTF/"
imageDir = "/root/images/"

import time
import threading
from ha.HAClasses import *
from ha.displayUI import *
from ha.haWebViews import *
from ha.fileInterface import *
from ha.gpsTimeInterface import *
from ha.I2CInterface import *
from ha.TC74Interface import *
from ha.tempInterface import *
from ha.audioInterface import *

# global variables
resources = None
stateChangeEvent = threading.Event()
resourceLock = threading.Lock()

if __name__ == "__main__":
    fgColor = color("yellow")
    bgColor = color("black")

    # interfaces
    gpsInterface = FileInterface("GPS", fileName=gpsFileName, readOnly=True, event=stateChangeEvent)
    timeInterface = GpsTimeInterface("Time", gpsInterface)
    diagInterface = FileInterface("Diag", fileName=diagFileName, readOnly=True, event=stateChangeEvent)
    i2cInterface = I2CInterface("I2C", bus=1, event=stateChangeEvent)
    tc74Interface = TC74Interface("TC74", i2cInterface)
    tempInterface = TempInterface("Temp", tc74Interface, sample=1)
    audioInterface = AudioInterface("Audio", event=stateChangeEvent)

    # time sensors
    timeResource = HASensor("time", timeInterface, "%-I:%M", type="time", label="Time")
    dateResource = HASensor("date", timeInterface, "%B %-d %Y", type="date", label="Date")
    dayOfWeekResource = HASensor("dayOfWeek", timeInterface, "%A", type="date", label="Day of week")
    timeZoneResource = HASensor("timeZone", timeInterface, "%Z", label="Time zone")

    # position sensors
    positionSensors = [
#        HASensor("position", gpsInterface, "Pos", label="Position"),
        HASensor("speed", diagInterface, "Speed", label="Speed", type="MPH"),
        HASensor("heading", gpsInterface, "Hdg", label="Heading", type="Deg"),
        HASensor("latitude", gpsInterface, "Lat", label="Latitude", type="Lat"),
        HASensor("longitude", gpsInterface, "Long", label="Longitude", type="Long"),
        HASensor("altitude", gpsInterface, "Alt", label="Elevation", type="Ft"),
#        HASensor("gpsSpeed", gpsInterface, "Speed", label="Speed", type="MPH"),
        HASensor("nSats", gpsInterface, "Nsats", label="Satellites"),
    ]

    # engine sensors
    engineSensors = [
#        HASensor("speed", diagInterface, "Speed", label="Speed", type="MPH"),
        HASensor("rpm", diagInterface, "Rpm", label="RPM", type="RPM"),
        HASensor("battery", diagInterface, "Battery", label="Battery", type="V"),
        HASensor("intakeTemp", diagInterface, "IntakeTemp", label="Intake temp", type="tempC"),
        HASensor("coolantTemp", diagInterface, "WaterTemp", label="Water temp", type="tempC"),
        HASensor("airPressure", diagInterface, "Barometer", label="Barometer", type="barometer"),
        HASensor("runTime", diagInterface, "RunTime", label="Run time", type="Secs"),
    ]
    outsideTemp = HASensor("outsideTemp", tempInterface, 0x4e, label="Outside temp", type="tempF")

    # initialization
    display = Display(displayDevice, inputDevice, views)
    display.clear(bgColor)
    face = freetype.Face(fontPath+fontName)
    
    # styles        
    defaultStyle = Style("default", face=face, fontSize=24, bgColor=bgColor, fgColor=fgColor)
    timeStyle = Style("timeStyle", defaultStyle, face=face, fontSize=80, width=300, height=90, fgColor=color("LightYellow"))
    tempStyle = Style("tempStyle", defaultStyle, face=face, fontSize=72, width=200, height=90)
    textStyle = Style("textStyle", defaultStyle, width=300, height=30, fgColor=color("cyan"))
    labelStyle = Style("labelStyle", defaultStyle, fontSize=32, width=220, height=50, fgColor=color("cyan"))
    valueStyle = Style("valueStyle", defaultStyle, fontSize=32, width=180, height=50, fgColor=color("LightYellow"))
    containerStyle = Style("container", defaultStyle)
#    audioStyle = Style("audioButton", defaultStyle, margin=2)
    buttonStyle = Style("button", defaultStyle, width=100, height=90, margin=2, bgColor=color("White"))
#    buttonTextStyle = Style("buttonText", buttonStyle, fontSize=36, bgColor=color("white"), fgColor=color("black"), padding=8)
#    buttonAltStyle = Style("buttonAlt", buttonTextStyle, bgColor=color("blue"), fgColor=color("white"))
        
    # button callback routines
    def doNothing(button, display):
        return

    # layout
    screen = Div("screen", containerStyle, [
                    Span("heading", containerStyle, [
                            Text("time", timeStyle, display=display, resource=timeResource),
                            Div("text", containerStyle, [
                                Text("dayOfWeek", textStyle, display=display, resource=dayOfWeekResource), 
                                Text("date", textStyle, display=display, resource=dateResource),
                                Text("timeZone", textStyle, display=display, resource=timeZoneResource),
                            ]),
                            Text("temp", tempStyle, display=display, resource=outsideTemp),
                        ]),
                    Span("sensors", containerStyle, [
                        Div("positionSensors", containerStyle, [
                            Span(sensor.name, containerStyle, [
                                Text(sensor.name+"Label", labelStyle, sensor.label),
                                Text(sensor.name+"Value", valueStyle, display=display, resource=sensor),
                                ],
                            )
                            for sensor in positionSensors]),
                        Div("engineSensors", containerStyle, [
                            Span(sensor.name, containerStyle, [
                                Text(sensor.name+"Label", labelStyle, sensor.label),
                                Text(sensor.name+"Value", valueStyle, display=display, resource=sensor),
                                ],
                            )
                            for sensor in engineSensors]),
                        ], height=300),
                    Span("buttons", containerStyle, [
                        Button("volDownButton", buttonStyle,
                            content=Image("volDownImage", imageFile=imageDir+"icons_volumedown-01.png"),
                            altContent=Image("volDownImageInvert", imageFile=imageDir+"icons_volumedown-02.png"),
                            ),
                        Button("volUpButton", buttonStyle,
                            content=Image("volUpImage", imageFile=imageDir+"icons_volumeup-01.png"),
                            altContent=Image("volUpImageInvert", imageFile=imageDir+"icons_volumeup-02.png"),
                            ),
                        Button("rewButton", buttonStyle,
                            content=Image("rewImage", imageFile=imageDir+"icons_rew-01.png"),
                            altContent=Image("rewImageInvert", imageFile=imageDir+"icons_rew-02.png"),
                            ),
                        Button("playButton", buttonStyle,
                            content=Image("playImage", imageFile=imageDir+"icons_play-01.png"),
                            altContent=Image("playImageInvert", imageFile=imageDir+"icons_play-02.png"),
                            ),
                        Button("pauseButton", buttonStyle,
                            content=Image("pauseImage", imageFile=imageDir+"icons_pause-01.png"),
                            altContent=Image("pauseImageInvert", imageFile=imageDir+"icons_pause-02.png"),
                            ),
                        Button("ffButton", buttonStyle,
                            content=Image("ffImage", imageFile=imageDir+"icons_ff-01.png"),
                            altContent=Image("ffImageInvert", imageFile=imageDir+"icons_ff-02.png"),
                            ),
                        Button("sourceButton", buttonStyle,
                            content=Image("sourceImage", imageFile=imageDir+"icons_source-01.png"),
                            altContent=Image("sourceImageInvert", imageFile=imageDir+"icons_source-02.png"),
                            ),
                        Button("wifiButton", buttonStyle,
                            content=Image("wifiImage", imageFile=imageDir+"icons_wifi-01.png"),
                            altContent=Image("wifiImageInvert", imageFile=imageDir+"icons_wifi-02.png"),
                            ),
                        ]),
                     ])

    screen.arrange()
    screen.render(display)
    
    # Start interfaces
    gpsInterface.start()
    diagInterface.start()
#    ndofInterface.start()
    tempInterface.start()
    display.start(block=True)
    
