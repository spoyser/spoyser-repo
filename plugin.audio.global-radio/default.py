#
#      Copyright (C) 2017 - Sean Poyser
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import xbmcplugin
import xbmcgui

import urllib
import os

import utils

ADDON   = utils.ADDON
TITLE   = utils.TITLE
ICON    = utils.ICON
FANART  = utils.FANART
IMAGES  = utils.IMAGES
GETTEXT = utils.GETTEXT


THUMBPATTERN  = 'http://fs.geronimo.thisisglobal.com/image/%s/png/w256'
FANARTPATTERN = 'http://fs.geronimo.thisisglobal.com/image/%s/png/w1280'


_RADIOROOT      = 100
_ONAIR          = 200
_LISTENAGAIN    = 300
_CHANNEL        = 400
_EPISODE        = 500
_RESET          = 600
_DOWNLOAD       = 700
_SHOW_DOWNLOAD  = 800
_PLAY_DOWNLOAD  = 900
_DELETE         = 1000


#STATIONS
CAPITAL  = 30001
HEART    = 30002
CAPITALX = 30003
LBC      = 30004
RADIOX   = 30005
SMOOTH   = 30006
GOLD     = 30007


STATIONS = {}
STATIONS[CAPITAL]  = [CAPITAL,  'http://www.capitalfm.com/',     3, 1] #3 - Use API
STATIONS[HEART]    = [HEART,    'http://www.heart.co.uk/',       3, 1] #3 - Use API
STATIONS[CAPITALX] = [CAPITALX, 'http://www.capitalxtra.com/',   1, 1] #1 - London/National
STATIONS[LBC]      = [LBC,      'http://www.lbc.co.uk/',         1, 0] #1 - London/National, 0 - No Listen Again
STATIONS[RADIOX]   = [RADIOX,   'http://www.radiox.co.uk/',      2, 1] #2 - London/Manchester/National
STATIONS[SMOOTH]   = [SMOOTH,   'http://www.smoothradio.com/',   3, 1] #3 - Use API
STATIONS[GOLD]     = [GOLD,     'http://www.mygoldmusic.co.uk/', 0, 1] #0 - National Only




def main():
    for station in STATIONS.values():
        stationID = str(station[0])
        thumbnail = os.path.join(IMAGES, '%s_icon.png'   % stationID)
        fanart    = os.path.join(IMAGES, '%s_fanart.png' % stationID)

        menu = []

        if station[2] != 0 and ADDON.getSetting(stationID).split(':')[0]:
            menu.append((GETTEXT(30041), 'XBMC.RunPlugin(%s?mode=%d&url=%s)' % (sys.argv[0], _RESET, stationID)))

        addDirectoryItem(getStationName(stationID), url=stationID, mode=_RADIOROOT, thumbnail=thumbnail, fanart=fanart, isFolder=True, isPlayable=False, menu=menu)

    downloadFolder = ADDON.getSetting('DOWNLOAD_FOLDER')
    if downloadFolder:
        import sfile
        if len(sfile.glob(downloadFolder)) > 0:
            addDirectoryItem(GETTEXT(30012), url='', mode=_SHOW_DOWNLOAD, thumbnail=ICON, fanart=FANART, isFolder=True, isPlayable=False)


def showDownload():
    downloadFolder = ADDON.getSetting('DOWNLOAD_FOLDER')
    if not downloadFolder:
        return

    files = utils.parseFolder(downloadFolder, subfolders=False)
    
    for file in files:
        name = file[0]
        path = file[1]

        extras = '&name=' + urllib.quote_plus(name)

        menu = []
        menu.append((GETTEXT(30043), 'XBMC.RunPlugin(%s?mode=%d&url=%s&name=%s)' % (sys.argv[0], _DELETE, urllib.quote_plus(path), urllib.quote_plus(name)))) 

        addDirectoryItem(name, url=path, mode=_PLAY_DOWNLOAD, thumbnail=ICON, fanart=FANART, isFolder=False, isPlayable=True, extras=extras, menu=menu)


def radioRoot(stationID):
    thumbnail = os.path.join(IMAGES, '%s_icon.png'   % stationID)
    fanart    = os.path.join(IMAGES, '%s_fanart.png' % stationID)
    name      = getStationName(stationID)
    locality  = getStationLocality(stationID)[0]

    addDirectoryItem(GETTEXT(30010) % locality, url=stationID, mode=_ONAIR, thumbnail=thumbnail, fanart=fanart, isFolder=False, isPlayable=True)

    if STATIONS[int(stationID)][3] != 0:
        addDirectoryItem(GETTEXT(30011), url=stationID, mode=_LISTENAGAIN, thumbnail=thumbnail, fanart=fanart, isFolder=True,  isPlayable=False)

    if ADDON.getSetting('AUTO_PLAY') == 'true':
        onAir(stationID, playNow=True)


def getStationName(stationID):
    return GETTEXT(int(stationID))


def getStationRoot(stationID):
    stations = STATIONS.values()
    root     = stations[0][1] #defaut to first one

    stationID = int(stationID)
    for station in stations:
        if stationID == station[0]:
            root = station[1]

    root += getStationLocality(stationID)[1]

    return root


def getStationLocality(stationID):
    setting   = str(stationID)
    stationID = int(stationID)
    locality  = ADDON.getSetting(setting)

    if locality.split(':')[0]:
        return locality.split(':')

    localityType = STATIONS[stationID][2]

    label, prefix = getStationLocalityFromType(stationID, localityType)

    ADDON.setSetting(setting, '%s:%s' % (label, prefix))
    return label, prefix


def getStationLocalityFromType(stationID, localityType):
    stnName = getStationName(stationID)

    if localityType == 0:
        return '%s %s' % (stnName, GETTEXT(30050)), 'radio/player/'


    national   = '%s %s' % (stnName, GETTEXT(30050))
    london     = '%s %s' % (stnName, GETTEXT(30051))
    manchester = '%s %s' % (stnName, GETTEXT(30052))

    if localityType == 1:
        choices = []
        choices.append((national, 'national'))
        choices.append((london,   'london'))
        return getlocalityFixedChoice(choices)

    if localityType == 2:
        choices = []
        choices.append((national,   'national'))
        choices.append((london,     'london'))
        choices.append((manchester, 'manchester'))
        return getlocalityFixedChoice(choices)


    if localityType == 3:
        return getlocalityAPIChoice(stationID)


    return '', 'national/radio/player/'


def getlocalityAPIChoice(stationID):
    import re
    url  = STATIONS[stationID][1] + 'api/1.0/station_preference/listen-live/'
    html = utils.GetHTML(url)
    html = html.replace('\\', '')
    html = html.split('<li class=')[1:]

    choices = []
    for item in html:
        items = re.compile('"(.+?)">.+?value="(.+?)".+?').findall(item)
        choices.append((items[0][1], items[0][0]))

    choices.sort()
    label, prefix = getlocalityFixedChoice(choices)

    if stationID == HEART:
        prefix = prefix.replace('radio', 'on-air') 

    return label, prefix


def getlocalityFixedChoice(choices):
    select = []
    for choice in choices:
        select.append(choice[0])

    choice = -1
    while choice < 0:
        choice = xbmcgui.Dialog().select(GETTEXT(30040), select) 

    choice = choices[choice]

    return choice[0], '%s/radio/player/' % choice[1]

          
def getLiveLinks(stationID):
    import re

    url   = getStationRoot(stationID)
    html  = utils.GetHTML(url)
    links = re.compile("audioUrl: '(.+?)'").findall(html)
    return links


def getLiveURL(stationID):
    try:
        import random

        links = getLiveLinks(stationID)

        return random.choice(links[:-1]) #remove last item as it doesn't stream in Kodi

    except:
        pass    


def getChannels(stationID):
    try:
        import re
        import json

        channels = []

        url  = getStationRoot(stationID)
        html = utils.GetHTML(url)

        url = re.compile('gusto.listen.init\((.+?)\)').search(html).group(1).replace(' ', '').replace('"', '')
        url = url.split(',')
        src = url[2]
        stn = url[0]
        url = src + '/Stations/' + stn + '/Channels'
        
        html     = utils.GetHTML(url)
        response = json.loads(html)
       

        for item in response:
            try:
                name      = item['Name']
                channelID = item['ChannelId']
                image     = item['ImageFile']
                channels.append([name, image, channelID, src])

            except:
                pass
        
    except:
        pass

    return channels


def listenAgain(stationID):
    channels = getChannels(stationID)

    episodes = {}
    ordered  = []

    for channel in channels:
        name      = channel[0].strip()
        image     = channel[1]
        channelID = channel[2]
        extras    = '&source=' + urllib.quote_plus(channel[3])

        thumb  = THUMBPATTERN  % image 
        fanart = FANARTPATTERN % image 

        if name in ordered:
            episodes[name][1] += ':%s' % channelID
        else:
            episodes[name] = [name, channelID, thumb, fanart, extras]
            ordered.append(name)

    for episode in ordered:
        episode   = episodes[episode]
        name      = episode[0]
        channelID = episode[1]
        thumb     = episode[2]
        fanart    = episode[3]
        extras    = episode[4]
        addDirectoryItem(name, url=channelID, mode=_CHANNEL, thumbnail=thumb, fanart=fanart, isFolder=True, isPlayable=False, extras=extras)



def channel(channelID, source):
    import json

    channelIDs = channelID.split(':')

    responses = {}
    image     = None

    for channelID in channelIDs:
        url  = source + '/Channels/' + channelID + '/Episodes'
        html = utils.GetHTML(url)

        response = json.loads(html)

        responses[channelID] = response

    for channelID in responses:
        response = responses[channelID]

        for item in response:
            try:    image = item['ImageFile']
            except: pass

    if image:
        thumb  = THUMBPATTERN  % image 
        fanart = FANARTPATTERN % image 
    else:
        thumb  = ICON 
        fanart = FANART 

    ordered = []

    download = GETTEXT(30042)

    for channelID in responses:
        response = responses[channelID]
        for item in response:
            name  = item['Name']
            desc  = item['Description']
            link  = item['MediaFiles'][0]['Filename']
            start = utils.parseDate(item['StartDate'])

            ordered.append([start, [name, desc, link]])

    ordered.sort()
    
    for item in ordered:
        name  = item[1][0]
        desc  = item[1][1]
        link  = item[1][2]
            
        menu = []

        menu.append((download, 'XBMC.RunPlugin(%s?mode=%d&url=%s&name=%s)' % (sys.argv[0], _DOWNLOAD, link, urllib.quote_plus(name))))
        
        addDirectoryItem(name, url=link, mode=_EPISODE, thumbnail=thumb, fanart=fanart, isFolder=False, isPlayable=True, menu=menu)


def deleteFile(path, name):
    if not utils.DialogYesNo(GETTEXT(30044) % name, GETTEXT(30045)):
        return

    import sfile
    sfile.delete(path)
    if sfile.exists(path):
        utils.DialogOK(GETTEXT(30046) % name)

    

def playDownload(path, name):
    playItem(path, name, ICON, FANART, playNow=False)


def onAir(stationID, playNow=False):
    thumbnail = os.path.join(IMAGES, '%s_icon.png'   % stationID)
    fanart    = os.path.join(IMAGES, '%s_fanart.png' % stationID)

    url  = getLiveURL(stationID)
    name = getStationName(stationID)

    playItem(url, name, thumbnail, fanart, playNow)



def playItem(url, name, thumbnail, fanart, playNow):
    liz  = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)

    liz.setInfo('music', {'Title':name})
    liz.setProperty('Fanart_Image', fanart)

    if hasattr(liz, 'setArt'):
        art = {}
        art['thumb']     = thumbnail
        art['fanart']    = fanart
        art['landscape'] = fanart
        art['banner']    = fanart
        art['poster']    = fanart
        
        if len(art) > 0:
            liz.setArt(art) 

    if playNow:
        pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        pl.clear()    
        pl.add(url, liz)
        xbmc.Player().play(pl)
    else:
        liz.setPath(url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
  

def playEpisode(episode, name, thumb, fanart):
    url = 'http://fs.geronimo.thisisglobal.com/audio/' + episode
    
    pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    pl.clear()    

    title = '%s - %s' % (TITLE, name)

    liz = xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
    liz.setInfo('music', {'Title': title})
    liz.setProperty('Fanart_Image', fanart)

    liz.setPath(url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)



def download(episode, name):
    if xbmcgui.Window(10000).getProperty('GLOBAL-DOWNLOADING'):
        utils.DialogOK(GETTEXT(30047))
        return

    downloadPath = getDownloadPath(name)

    if not downloadPath:
        return

    #add original extension
    downloadPath += '.' + episode.rsplit('.', 1)[-1]

    url = 'http://fs.geronimo.thisisglobal.com/audio/' + episode

    import download
    download. download(url, downloadPath, title=name)


def getDownloadPath(name):
    downloadFolder = ADDON.getSetting('DOWNLOAD_FOLDER')

    if downloadFolder == '':
        utils.DialogOK(GETTEXT(30060))
	ADDON.openSettings() 
	downloadFolder = ADDON.getSetting('DOWNLOAD_FOLDER')

    if downloadFolder == '':
        return None

    import re
    filename = re.sub('[:\\/*?\<>|"]+', '', name)
    return os.path.join(downloadFolder, filename)



def addDirectoryItem(name, url, mode, thumbnail, fanart, isFolder, isPlayable, extras=None, menu=None):
    u   = sys.argv[0]
    u  += '?url='    + urllib.quote_plus(url)
    u  += '&mode='   + str(mode)
    u  += '&name='   + urllib.quote_plus(name)
    u  += '&thumb='  + urllib.quote_plus(thumbnail)
    u  += '&fanart=' + urllib.quote_plus(fanart)

    if extras:
        u += extras

    liz = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)

    liz.setProperty('Fanart_Image', fanart)
 
    if isPlayable:
        liz.setProperty('IsPlayable','true')

    if menu:
        liz.addContextMenuItems(menu)

    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=isFolder)


def refresh():
    xbmc.executebuiltin('Container.Refresh')


def get_params(path):
    params = {}
    path   = path.split('?', 1)[-1]
    pairs  = path.split('&')

    for pair in pairs:
        split = pair.split('=')
        if len(split) > 1:
            params[split[0]] = urllib.unquote_plus(split[1])

    return params


def process_params(params):
    params = get_params(params)
    mode   = None

    try:    mode = int(params['mode'])
    except: pass

    try:    url = params['url']
    except: url = ''


    if mode == _RADIOROOT:
        try:    return radioRoot(url)
        except: pass


    if mode == _ONAIR:
        try:    return onAir(url)
        except: pass

        
    if mode == _LISTENAGAIN:
        try:    return listenAgain(url)
        except: pass


    if mode == _CHANNEL:
        try:    return channel(url, params['source'])
        except: pass


    if mode == _EPISODE:
        try:    return playEpisode(url, params['name'], params['thumb'], params['fanart'])
        except: pass


    if mode == _SHOW_DOWNLOAD:
        try:    return showDownload()
        except: pass


    if mode == _PLAY_DOWNLOAD:
        try:    return playDownload(url, params['name'])
        except: pass


    if mode == _DELETE:
        try:    
            deleteFile(url, params['name'])
            return refresh()
        except:
            pass


    if mode == _RESET:
        try:    
            ADDON.setSetting(url, '')
            return refresh()
        except:
            pass


    if mode == _DOWNLOAD:
        try:    return download(url, params['name'])
        except: pass

    main()


process_params(sys.argv[2])
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)