# Camera web UI

import os
import subprocess
import json
from jinja2 import FileSystemLoader
from ha import *
from ha.camera.classes import *
from ha.camera.storage import *

# camera user interface
def cameraUI(function, camera, date, resource, cameras, resources, templates, views):
    if function == "snaps":
        return snaps(camera, date, resource, cameras, templates)
    elif function == "events":
        return events(camera, date, cameras, templates)
    elif function == "dates":
        return dates(camera, cameras, templates)
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
    for camera in cameras:
        videoDir = cameraDir+camera+"/videos/"+dateDir(date)
        # return newest playlist that isn't an event
        playlists = os.listdir(videoDir)
        for playlist in sorted(playlists, reverse=True):
            if playlist.split(".")[-1] == "m3u8":
                if playlist.split(".")[-2][-5:] != "event":
                    playlistList.append(playlist)
                    debug('debugWall', "camera = ", camera)
                    debug('debugWall', "playlist = ", playlist)
                    break
    [capacity, used, avail, percent] = getStorage()
    return templates.get_template("wall.html").render(title=webPageTitle+" cameras", script="",
                        dateDisp=time.strftime("%a %B %-d %Y %-H:%M"),
                        capacity=capacity, used=used, avail=avail, percent=percent,
                        cameras=([camera, cameras[camera].label] for camera in sorted(cameras)),
                        date=date, time=time.strftime("%H%M"),
                        playlists=playlistList)

# display the snapshots for a camera on the specified day
def snaps(camera, date, resource, cameras, templates):
    if not camera:
        camera = cameras[0]
    if not date:
        date = time.strftime("%Y%m%d")
    debug('debugSnaps', "camera = ", camera)
    debug('debugSnaps', "date = ", date)
    snapDir = cameraDir+camera+"/thumbs/"+dateDir(date)
    snapshots = os.listdir(snapDir)
    debug('debugSnaps', "snapshots = ", len(snapshots))
    # build a matrix of snapshots for the day at 5 minute intervals
    snapList = [("", "")]*288
    for snap in snapshots:
        snapHour = int(snap[8:10])
        snapMinute = int(snap[10:12])
        snapIndex = snapHour * 12 + snapMinute/5
        snapTimes = ["%02d"%(minute) for minute in range(snapMinute, snapMinute+5)]
        snapList[snapHour * 12 + snapMinute/5] = (snap, snapHour, snapTimes)
    # reverse the order and trim future hours
    snapListDisp = []
    for hour in range(23, -1, -1):
        if snapList[hour*12:hour*12+12] != [("", "")]*12:
            snapListDisp += [("", "%2d"%hour)]
            snapListDisp += snapList[hour*12:hour*12+12]
    return templates.get_template("snaps.html").render(title=webPageTitle+" "+cameras[camera].label+" camera", script="",
                        dateDisp=time.strftime("%a %B %-d %Y", time.strptime(date, "%Y%m%d")),
                        camera=camera,
                        date=date,
                        snaps=snapListDisp)

# display the dates for which there are camera events and videos
def dates(camera, cameras, templates):
    if camera:
        cameraList = [camera]
    else:
        cameraList = cameras.keys()
    try:
        eventStorage = json.load(open(stateDir+"storage.json"))
    except IOError:
        eventStorage = {}

    # update today's stats
    for camera in cameraList:
        updateStorageStats(camera, time.strftime("%Y%m%d"), cameraDir, eventStorage)

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
        (camera, year, month, day) = cameraDay.split("/")
        lastWeekday = weekday
        weekday = int(time.strftime("%w", time.strptime(year+month+day, "%Y%m%d")))
        if camera != lastCamera:    # new camera
            if lastCamera != "":    # not the first camera
                # fill out the remainder of the week for the previous camera/year/month
                for d in range(7 - lastWeekday - 1):
                    cameraDays[-1][2][-1][2].append(["", "", "", ""])
            cameraDays.append([cameras[camera].label, camera, []])
            lastCamera = camera
            lastYearMonth = ""
        if year+month != lastYearMonth: # new year/month
            if lastYearMonth != "": # same camera
                # fill out the remainder of the week for the previous camera/year/month
                for d in range(7 - weekday):
                    cameraDays[-1][2][-1][2].append(["", "", "", ""])
            cameraDays[-1][2].append([time.strftime("%Y %B", time.strptime(year+month, "%Y%m")), year+month, []])
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
    return templates.get_template("dates.html").render(title=webPageTitle+" cameras", script="",
                        capacity=capacity, used=used, avail=avail, percent=percent,
                        cameraDays=cameraDays)

# return a set of event thumbnails for a specified camera and date
def events(camera, date, cameras, templates):
    if not date:
        date = time.strftime("%Y%m%d")
    debug('debugImage', "camera = ", camera)
    debug('debugImage', "date = ", date)
    imageDir = cameraDir+camera+"/images/"+dateDir(date)
    imageFiles = os.listdir(imageDir)
    images = []
    for imageFile in sorted(imageFiles, reverse=True):
        [imageName, ext] = imageFile.split(".")
        [eventName, eventType] = imageName.split("_")
        images.append([imageName, eventName[8:12]+"%3A", eventName[8:10]+":"+eventName[10:12]+":"+eventName[12:14], eventType])
    # fill out the remainder of the row if there are < 4 images
    if len(images) < 4:
        images += [["", "", "", ""] for i in range((int(len(images)/4)+1)*4-len(images))]
    return templates.get_template("events.html").render(title=webPageTitle+" "+cameras[camera].label+" events", script="",
                        date=date,
                        dateDisp=time.strftime("%a %B %-d %Y", time.strptime(date, "%Y%m%d")),
                        camera=camera,
                        images=images)

# stream a playlist from a camera
def stream(camera, date, playlist, cameras, templates):
    if not camera:
        camera = cameras[0]
    if not date:
        date = time.strftime("%Y%m%d")
    videoDir = cameraDir+camera+"/videos/"+dateDir(date)
    if playlist:
        playlist += ".m3u8"
    else:
        # return newest playlist that isn't an event
        playlists = os.listdir(videoDir)
        for playlist in sorted(playlists, reverse=True):
            if playlist.split(".")[-1] == "m3u8":
                if playlist.split(".")[-2][-5:] != "event":
                    break
    debug('debugStream', "camera = ", camera)
    debug('debugStream', "date = ", date)
    debug('debugStream', "playlist = ", playlist)
    return templates.get_template("stream.html").render(title=webPageTitle+" "+cameras[camera].label+" camera", script="",
                        dateDisp=time.strftime("%a %B %-d %Y", time.strptime(date, "%Y%m%d")),
                        camera=camera,
                        date=date,
                        playlist=playlist)

# download a video clip from a camera
def download(camera, date, playlist, cameras, templates):
    if not camera:
        camera = cameras[0]
    if not date:
        date = time.strftime("%Y%m%d")
    if not playlist:
        playlist = time.strftime("%H%M")
    videoDir = cameraDir+camera+"/videos/"+dateDir(date)
    startHour = playlist[0:2]
    startMinute = playlist[2:4]
    endHour = startHour
    endMinute = str(int(startMinute) + 1)
    debug('debugDownload', "camera = ", camera)
    debug('debugDownload', "date = ", date)
    debug('debugDownload', "startHour = ", startHour)
    debug('debugDownload', "startMinute = ", startMinute)
    debug('debugDownload', "endHour = ", endHour)
    debug('debugDownload', "endMinute = ", endMinute)
    return templates.get_template("download.html").render(title=webPageTitle+" "+cameras[camera].label+" camera download", script="",
                        dateDisp=time.strftime("%a %B %-d %Y", time.strptime(date, "%Y%m%d")),
                        camera=camera, date=date,
                        starthour=startHour, startminute=startMinute, endhour=endHour, endminute=endMinute)
