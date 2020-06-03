# Camera web UI

import os
import subprocess
import json
from jinja2 import FileSystemLoader
from ha import *
from ha.camera.classes import *
from ha.camera.storage import *
from ha.camera.events import *

# camera user interface
def cameraUI(function, camera, date, resource, cameras, resources, templates, views):
    if function == "snaps":
        return snaps(camera, date, resource, cameras, templates)
    elif function == "events":
        return events(camera, date, cameras, templates)
    elif function == "stats":
        return stats(camera, cameras, templates)
    elif function == "stream":
        return stream(camera, date, resource, cameras, templates)
    elif function == "download":
        return download(camera, date, resource, cameras, templates)
    else:
        return wall(cameras, templates)

# display a wall of all cameras
def wall(cameras, templates):
    date = time.strftime("%Y%m%d")
    debug('debugWall', "date = ", date)
    playlistList = []
    for cameraName in list(cameras.keys()):
        videoDir = cameraDir+cameraName+"/videos/"+dateDir(date)
        # return newest playlist that isn't an event
        playlists = os.listdir(videoDir)
        for playlist in sorted(playlists, reverse=True):
            if playlist.split(".")[-1] == "m3u8":
                if playlist.split(".")[-2][-5:] != "event":
                    playlistList.append(playlist)
                    debug('debugWall', "camera = ", cameraName)
                    debug('debugWall', "playlist = ", playlist)
                    break
    [capacity, used, avail, percent] = getStorage()
    return templates.get_template("wall.html").render(title=webPageTitle+" cameras", script="",
                        dateDisp=time.strftime("%a %B %-d %Y %-H:%M"),
                        cameras=([camera, cameras[camera].label] for camera in sorted(cameras)),
                        date=date, time=time.strftime("%H%M"),
                        playlists=playlistList)

# display the snapshots for a camera on the specified day
# resource:
#     <startTime>.<nSnaps>.<increment>
#     HHMMSS.NNN.HHMMSS
#     default: 000000.288.0005

def snaps(cameraName, date, resource, cameras, templates):
    today = time.strftime("%Y%m%d")
    if not camera:
        cameraName = cameras[0].name
    if not date:
        date = today
    if not resource:
        resource = "000000.288.000500"
        daily = True
    else:
        daily = False
    (startTime, nSnaps, incr) = (resource.split(".")+["0","0"])[0:3]
    debug('debugSnaps', "camera = ", cameraName)
    debug('debugSnaps', "date = ", date)
    debug('debugSnaps', "daily = ", daily)
    debug('debugSnaps', "startTime = ", startTime)
    debug('debugSnaps', "nSnaps = ", nSnaps)
    debug('debugSnaps', "incr = ", incr)
    snapDir = cameraDir+cameraName+"/thumbs/"+dateDir(date)
    snapshots = os.listdir(snapDir)
    debug('debugSnaps', "snapshots = ", len(snapshots))
    # build a matrix of snapshots
    # snapList = [("", "")]*int(nSnaps)
    snapList = []
    snapIncr = int(incr[0:2])*3600+int(incr[2:4])*60+int(incr[4:6])
    debug('debugSnaps', "snapIncr = ", snapIncr)
    snapThreads = []
    [date, hour, minute, second] = splitTime(date+startTime)
    snapTime = startTime
    now = time.strftime("%H%M%S")
    for i in range(int(nSnaps)):
        debug('debugSnaps', "  snapTime = ", snapTime)
        # don't try to find snaps in the future
        if (int(snapTime) > int(now)) and (date == today):
            break
        snapshot = date+snapTime+"_snap.jpg"
        if snapshot not in snapshots:
            # debug('debugSnaps', "  creating ", snapshot)
            # createSnap(cameraName, snapshot, False)
            snapshot = ""   # don't try to display it yet
        snapHour = int(snapTime[0:2])
        snapMinute = int(snapTime[2:4])
        # snapTimes = ["%02d"%(minute) for minute in range(snapMinute, snapMinute+5)]
        if incr == "000500":    # currently showing 5 minute intervals
            nextSnap = snapTime+".5.000100"
            snapTimeDisp = snapTime[2:4]
        elif incr == "000100":  # currently showing 1 minute intervals
            nextSnap = snapTime+".6.000010"
            snapTimeDisp = snapTime[2:4]
        else:                       # currently showing 10 second intervals
            nextSnap = ""
            snapTimeDisp = snapTime[2:4]+":"+snapTime[4:6]
        snapList.append((snapshot, snapHour, snapTimeDisp, snapTime, nextSnap))
        snapTime = addTimes(snapTime, incr)

    debug('debugSnaps', "snapList = ", len(snapList))
    debug('debugSnaps', "snapHour = ", snapHour)
    if daily:
        # reverse the order and trim future hours
        snapListDisp = []
        snapList += [("", "")]*int((60-snapMinute)/5)
        for hour in range(snapHour, -1, -1):
            if snapList[hour*12:hour*12+12] != [("", "")]*12:
                snapListDisp += [("", "%2d"%hour)]
                snapListDisp += snapList[hour*12:hour*12+12]
    else:
        snapListDisp = [("", "%2d"%snapHour)] + snapList
    return templates.get_template("snaps.html").render(title=webPageTitle+" "+cameras[cameraName].label+" camera", script="",
                        dateDisp=time.strftime("%a %B %-d %Y", time.strptime(date, "%Y%m%d")),
                        camera=cameraName,
                        date=date,
                        snaps=snapListDisp)

# display the dates for which there are camera events and videos
def stats(cameraName, cameras, templates):
    if cameraName:
        cameraList = [cameraName]
    else:
        cameraList = list(cameras.keys())
    try:
        eventStorage = json.load(open(stateDir+"storage.json"))
    except IOError:
        eventStorage = {}

    # update today's stats
    for cameraName in cameraList:
        updateStorageStats(cameraName, time.strftime("%Y%m%d"), cameraDir, eventStorage)

    # create a multidimensional array containing the data for display
    #    cameraDays = ["displayCamera1", camera1, ["displayYearMonth1", yearMonth1, [[displayDay1, day1, nEvents, size],
    #                                                                                ...,
    #                                                                                [displayDayN, dayN, nEvents, size]],
    #                                             ...,
    #                                             ["displayYearMonthN", yearMonthN, [[displayDay1, day1, nEvents, size],
    #                                                                                ...,
    #                                                                                [displayDayN, dayN, nEvents, size]]],
    #                  ...,
    #                  "displayCameraN", cameraN, ["displayYearMonth1", yearMonth1, [[displayDay1, day1, nEvents, size],
    #                                                                                ...,
    #                                                                                [displayDayN, dayN, nEvents, size]],
    #                                             ...,
    #                                             ["displayYearMonthN", yearMonthN, [[displayDay1, day1, nEvents, size],
    #                                                                                ...,
    #                                                                                [displayDayN, dayN, nEvents, size]]]]
    cameraDays = []
    lastCamera = ""
    weekday = 0
    for cameraDay in sorted(eventStorage.keys()):
        (cameraName, year, month, day) = cameraDay.split("/")
        lastWeekday = weekday
        weekday = int(time.strftime("%w", time.strptime(year+month+day, "%Y%m%d")))
        if cameraName != lastCamera:    # new camera
            if lastCamera != "":    # not the first camera
                # fill out the remainder of the week for the previous camera/year/month
                for d in range(7 - lastWeekday - 1):
                    cameraDays[-1][2][-1][2].append(["", "", "", ""])
            cameraDays.append([cameras[cameraName].label, cameraName, []])
            lastCamera = cameraName
            lastYearMonth = ""
        if year+month != lastYearMonth: # new year/month
            if lastYearMonth != "": # same camera
                # fill out the remainder of the week for the previous camera/year/month
                for d in range(7 - weekday):
                    cameraDays[-1][2][-1][2].append(["", "", "", ""])
            cameraDays[-1][2].append([time.strftime("%B %Y", time.strptime(year+month, "%Y%m")), year+month, []])
            lastYearMonth = year+month
            # fill in the days in the week prior to the calendar day of week
            for d in range(weekday):
                cameraDays[-1][2][-1][2].append(["", "", "", ""])
        [nEvents, size] = eventStorage[cameraDay]
        cameraDays[-1][2][-1][2].append([day.lstrip("0"), day, nEvents, size])
    # fill out the remainder of the week for the previous camera/year/month
    for d in range(7 - weekday - 1):
        cameraDays[-1][2][-1][2].append(["", "", "", ""])
    # get storage device statistics
    [capacity, used, avail, percent] = getStorage()
    debug('debugIndex', "cameraDays", cameraDays)
    return templates.get_template("stats.html").render(title=webPageTitle+" camera statistics", script="",
                        capacity=capacity, used=used, avail=avail, percent=percent,
                        cameraDays=cameraDays)

# return a set of event thumbnails for a specified camera and date
def events(cameraName, date, cameras, templates):
    if not date:
        date = time.strftime("%Y%m%d")
    debug('debugImage', "camera = ", cameraName)
    debug('debugImage', "date = ", date)
    imageDir = cameraDir+cameraName+"/images/"+dateDir(date)
    imageFiles = os.listdir(imageDir)
    images = []
    for imageFile in sorted(imageFiles, reverse=True):
        [imageName, ext] = imageFile.split(".")
        [eventName, eventType] = imageName.split("_")
        images.append([imageName, eventName[8:14]+"%3A", eventName[8:10]+":"+eventName[10:12]+":"+eventName[12:14], eventType])
    # fill out the remainder of the row if there are < 4 images
    if len(images) < 4:
        images += [["", "", "", ""] for i in range((int(len(images)/4)+1)*4-len(images))]
    return templates.get_template("events.html").render(title=webPageTitle+" "+cameras[cameraName].label+" events", script="",
                        date=date,
                        dateDisp=time.strftime("%a %B %-d %Y", time.strptime(date, "%Y%m%d")),
                        camera=cameraName,
                        images=images)

# stream a playlist from a camera
def stream(cameraName, date, playlist, cameras, templates):
    if not cameraName:
        cameraName = cameras[0].name
    if not date:
        date = time.strftime("%Y%m%d")
    videoDir = cameraDir+cameraName+"/videos/"+dateDir(date)
    if playlist:
        playlist += ".m3u8"
    else:
        # return newest playlist that isn't an event
        playlists = os.listdir(videoDir)
        for playlist in sorted(playlists, reverse=True):
            if playlist.split(".")[-1] == "m3u8":
                if playlist.split(".")[-2][-5:] != "event":
                    break
    debug('debugStream', "camera = ", cameraName)
    debug('debugStream', "date = ", date)
    debug('debugStream', "playlist = ", playlist)
    return templates.get_template("stream.html").render(title=webPageTitle+" "+cameras[cameraName].label+" camera", script="",
                        dateDisp=time.strftime("%a %B %-d %Y", time.strptime(date, "%Y%m%d")),
                        camera=cameraName,
                        date=date,
                        playlist=playlist)

# download a video clip from a camera
def download(cameraName, date, playlist, cameras, templates):
    if not cameraName:
        cameraName = cameras[0].name
    if not date:
        date = time.strftime("%Y%m%d")
    if not playlist:
        playlist = time.strftime("%H%M")
    videoDir = cameraDir+cameraName+"/videos/"+dateDir(date)
    startHour = playlist[0:2]
    startMinute = playlist[2:4]
    endHour = startHour
    endMinute = str(int(startMinute) + 1)
    debug('debugDownload', "camera = ", cameraName)
    debug('debugDownload', "date = ", date)
    debug('debugDownload', "startHour = ", startHour)
    debug('debugDownload', "startMinute = ", startMinute)
    debug('debugDownload', "endHour = ", endHour)
    debug('debugDownload', "endMinute = ", endMinute)
    return templates.get_template("download.html").render(title=webPageTitle+" "+cameras[cameraName].label+" camera download", script="",
                        dateDisp=time.strftime("%a %B %-d %Y", time.strptime(date, "%Y%m%d")),
                        camera=cameraName, date=date,
                        starthour=startHour, startminute=startMinute, endhour=endHour, endminute=endMinute)
