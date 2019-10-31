# camera video functions
ftpUsername = "pi"
chunkDuration = 10
eventDuration = 30

import time
import os
import subprocess
import math
import datetime
from ha import *
from ha.camera.classes import *

cameraKey = keyDir+"camera.key"

# read a m38u playlist file
# add the timestamp and duration of each chunk to a list
def getPlaylist(fileName, chunkList):
    playlist = open(fileName).read()
    lines = playlist.split("\n")
    for i in range(len(lines)):
        if lines[i].split(":")[0] == "#EXTINF":
            chunkList.append((lines[i+1].split(".")[0], float(lines[i].split(":")[1].rstrip(","))))
            i += 1
    return chunkList

# collect the m3u8 playlists in a video directory and add them to a list
def getPlaylists(videoDir):
    videoFiles = os.listdir(videoDir)
    videoFiles.sort()
    chunkList = []
    eventList = []
    for videoFile in videoFiles:
        if videoFile.split(".")[-1] == "m3u8":
            if videoFile.split(".")[0][-5:] == "event":
                eventList.append(videoFile.split(".")[0].split("-")[0])
            else:
                chunkList = getPlaylist(videoDir+videoFile, chunkList)
    return (chunkList, eventList)

# build a m3u8 playlist that contains the specified time period
def makePlaylist(start, end, chunkList):
    maxDuration = 0.0
    chunks = []
    for chunk in chunkList:
        if chunk[0] > start:
            maxDuration = max(maxDuration, chunk[1])
            chunks.append(chunk)
        if chunk[0] > end:
            break
    playlist  = "#EXTM3U\n"
    playlist += "#EXT-X-PLAYLIST-TYPE:VOD\n"
    playlist += "#EXT-X-VERSION:3\n"
    playlist += "#EXT-X-TARGETDURATION:"+str(int(math.ceil(maxDuration)))+"\n"
    playlist += "#EXT-X-MEDIA-SEQUENCE:0\n"
    for chunk in chunks:
        playlist += "#EXTINF:"+str(chunk[1])+",\n"
        playlist += chunk[0]+".ts\n"
    playlist += "#EXT-X-ENDLIST\n"
    playlist += "\n"
    return playlist

# return the start and end times given an event time and before and after deltas
def getEventTimes(eventTime, before, after):
    timeFmt = "%Y%m%d%H%M%S"
    eventTimeDatetime = datetime.datetime(*time.strptime(eventTime, timeFmt)[0:6])
    startTimeDatetime = eventTimeDatetime - datetime.timedelta(seconds=before)
    endTimeDatetime = eventTimeDatetime + datetime.timedelta(seconds=after)
    start = time.strftime(timeFmt, startTimeDatetime.timetuple())
    end = time.strftime(timeFmt, endTimeDatetime.timetuple())
    return (start, end)

# record video for a camera
def recordVideo(cameraDir, camera, date):
    debug('debugEnable', "starting video thread for camera", camera.name)
    videoDir = cameraDir+camera.name+"/videos/"+dateDir(date)
    cameraUsername = getValue(cameraKey, "cameraUsername")
    cameraPassword = getValue(cameraKey, "cameraPassword")
    debug("debugVideo", "videoDir:", videoDir)
    os.popen("mkdir -p "+videoDir)
    while True:
        try:
            cmd  = "/usr/bin/ffmpeg -i rtsp://"+cameraUsername+":"+cameraPassword+"@"+camera.ipAddr+":"+str(camera.port)+"/"+camera.resource
            cmd += " -nostats -loglevel error"
            cmd += " -an -vcodec copy -use_localtime 1 -hls_list_size 0 -hls_time "+str(chunkDuration)
            cmd += " -hls_segment_filename "+videoDir+"%Y%m%d%H%M%S.ts "
            cmd += videoDir+time.strftime("%Y%m%d%H%M%S")+".m3u8"
            debug("debugVideo", "recording started for camera", camera.name)
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True).decode()
            debug("debugVideo", "recording finished for camera", camera.name, output)
        except subprocess.CalledProcessError as exception:
            log("recording failed for camera", camera.name, "exit code:", exception.returncode, exception.output)
        time.sleep(60)
    debug('debugEnable', "ending video thread for camera", camera.name)

# find a video fragment that contains the specified time
def findChunk(videoDir, startTime):
    startTime = (startTime+"00")[0:6]   # add seconds if there aren't any
    videoFiles = os.listdir(videoDir)
    tsFileNames = []
    # filter out files that are not .ts
    for videoFile in videoFiles:
       if videoFile.split(".")[1] == "ts":
           if videoFile.split(".")[0].isnumeric():
               tsFileNames.append(videoFile)
    tsFileNames.sort()
    # find the chunk where the event starts
    firstFileIndex = len(tsFileNames)
    for tsFileName in tsFileNames:
        if int(tsFileName[8:14]) >= int(startTime[8:14]): # hhmmss
            firstFileIndex = tsFileNames.index(tsFileName)
            break
    return (tsFileNames, firstFileIndex)

# make a video clip from a series of ts chunks
def makeClip(videoDir, startTime, duration, fileType):
    nChunks = int(duration / chunkDuration)
    nChunks = min(nChunks, 60)  # 10 minutes max
    debug("debugClip", "creating clip", "videoDir:", videoDir, "startTime:", startTime, "duration:", duration, "nChunks:", nChunks)
    (tsFileNames, firstFileIndex) = findChunk(videoDir, startTime)
    debug("debugClip", "firstChunk:", tsFileNames[0], "firstChunkIndex:", firstFileIndex)
    # concatenate the chunks into one file
    catFileName = startTime+"-cat.ts"
    with open(videoDir+catFileName, "wb") as catFile:
        for tsFileName in tsFileNames[firstFileIndex:firstFileIndex+nChunks]:
            debug("debugClip", "chunk:", tsFileName)
            with open(videoDir+tsFileName, "rb") as tsFile:
                catFile.write(tsFile.read())
    # convert the clip
    clipFileName = startTime+"."+fileType
    cmd = "/usr/bin/ffmpeg -i "+videoDir+catFileName+" -nostats -loglevel error -y -c copy "+videoDir+clipFileName
    debug("debugClip", "cmd:", cmd)
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True).decode()
        debug("debugClip", "deleting", catFileName)
        output = subprocess.check_output("rm "+videoDir+catFileName, stderr=subprocess.STDOUT, shell=True).decode()
        return clipFileName
    except subprocess.CalledProcessError as exception:
        log("clip creation failed for", clipFileName, "exit code:", exception.returncode, exception.output)
        return "clip creation failed"
