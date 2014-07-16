#
#       Copyright (C) 2014 Datho-Digital
#       Sean Poyser (seanpoyser@dathodigital.co.uk)
#

import json
import time
import datetime

import geturllib

from program import Channel
from program import Program

# TRIBUNE API
# http://developer.tmsapi.com
# user =  tyler.messa
# pass =  SxkLE8Aa7dQZ

# GBR-0001194-DEFAULT


SECSINDAY = 86400
API       = '9emnn93tqhp8esgf78z3d6pu'#'bv72mavp679jjt5ccvg7258s'
HOUR      = datetime.timedelta(hours = 1)
ZERO      = datetime.timedelta()


# ---------------------------------------


def setCacheDir(dir):
    geturllib.SetCacheDir(dir)


def getPrograms(channels, startTime, endTime, cacheOnly):
    lineups = []
    for channel in channels:
        lineup = channel.lineup
        if lineup:
            if len(lineup) > 0 and (lineup not in lineups):
                lineups.append(lineup)

    allPrograms = []

    for lineup in lineups:
        subset = {}
        for channel in channels:
            if channel.lineup == lineup:
                subset[channel.tribuneID] = channel
        programList = _getPrograms(subset, lineup, startTime, endTime, cacheOnly)
        allPrograms.extend(programList)

    return allPrograms


# ---------------------------------------------------------
# these are really private

def _sanitizeText(text):
    newText    = ''
    ignoreNext = False

    for c in text:
        if ord(c) < 127:
            newText   += c
            ignoreNext = False
        elif ignoreNext:
            ignoreNext = False
        else:
            newText   += ' '
            ignoreNext = True

    return newText


def _convertTimeToAPI(theTime): #converts to string for API call
    return str(theTime).replace(' ', 'T').rsplit(':', 1)[0]   + ':00Z'


def _convertTime(theString):
    if not theString:
        return None

    theString = theString.rsplit('Z', 1)[0]
    theString = theString + ':00'

    t = time.strptime(theString, '%Y-%m-%dT%H:%M:%S')
    d = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)

    return d


def _getPrograms(channels, lineup, startTime, endTime, cacheOnly):
    response = _getProgramsAPI(channels, lineup, startTime, endTime, cacheOnly)

    programList = []

    for channel in response:
        if 'error' in channel:
            print '%s' % channel['error']
            return []

        airings = channel['airings']
    
        for airing in airings:
            program   = airing['program']
            stationID = airing['stationId']

            channel      = channels[stationID]
            channelPlus1 = None

            plus1 = stationID+'+'
            if plus1 in channels:
                channelPlus1 = channels[plus1]

            startTime = _convertTime(airing['startTime'])
            endTime   = _convertTime(airing['endTime'])

            try:    shortDesc = _sanitizeText(program['shortDescription'])
            except: shortDesc = ''

            try:    longDesc = _sanitizeText(program['longDescription'])
            except: longDesc = ''

            try:    title = program['title']
            except: title = ''

            try:    
                image   = 'http://dath.tmsimg.com/'+ program['preferredImage']['uri']
                smImage = image #+ '?w=240' #XBMC does a better job of resizing
            except: 
                image   = None
                smImage = None

            print image

            program = Program(channel, title, startTime, endTime, longDesc, None, image, smImage, None)
            programList.append(program) 

            if channelPlus1:
                program = Program(channelPlus1, title, startTime+HOUR, endTime+HOUR, longDesc, None, image, smImage, None)
                programList.append(program) 

    return programList


def _getProgramsAPI(channels, lineup, startTime, endTime, cacheOnly):
    if (not lineup) or len(lineup) < 1:
        return [{ 'error' : 'Invalid Tribune Lineup' }]

    chnIDs = ''
    for key in channels:
        chnIDs += channels[key].tribuneID +','

    if (not chnIDs) or len(chnIDs) < 1:
        return [{ 'error' : 'Invalid Tribune Channel' }]

    #chnIDs = chnIDs[:-1] #remove final comma

    plus1  = '+' in chnIDs
    chnIDs = chnIDs.replace('+', '')
    offset = HOUR if plus1 else ZERO
    
    URL = 'http://data.tmsapi.com/v1/lineups/'

    startTime = _convertTimeToAPI(startTime - offset)
    endTime   = _convertTimeToAPI(endTime)

    #detail = 'Basic'
    detail = 'Detailed'
    #detail = 'DetailedNoImage'

    #imageSize = 'Sm'
    #imageSize = 'Md'
    imageSize = 'Lg'
    #imageSize = 'Ms'

    #aspect = '2x3'
    #aspect = '3x4'
    aspect = '4x3'
    #aspect = '16x9'

    url ='%s%s/grid?stationId=%s&startDateTime=%s&endDateTime=%s&size=%s&imageSize=%s&imageAspectTV=%s&imageText=false&api_key=%s' % (URL, lineup, chnIDs, startTime, endTime, detail, imageSize, aspect, API)

    #print "Requested URL %s" % url

    try:    response = geturllib.GetURL(url, SECSINDAY, cacheOnly)
    except: return [{ 'error' : 'No Response' }]

    if len(response) < 1:
        return []
    
    try:    return json.loads(response)
    except: return [{ 'error' : 'Invalid Response' }]

    return [{ 'error' : 'Invalid Response' }]