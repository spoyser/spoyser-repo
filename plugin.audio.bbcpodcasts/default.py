#
#       Copyright (C) 2013-
#       Sean Poyser (seanpoyser@gmail.com)
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

import urllib
import xbmcplugin
import xbmcgui
import xbmcaddon

import time
import re
import os
from xml.etree import ElementTree
import threading


import quicknet
import pc_utils as utils


_STATION      = 100
_SHOW         = 200
_PODCAST      = 300
_DOWNLOAD     = 400
_SEARCH       = 500
_SEARCHRESULT = 600


ADDON   = utils.ADDON
TITLE   = utils.TITLE
PROFILE = utils.PROFILE
URL     = utils.URL


global Year
Year = 2013


def downloadPath(url):        		
    downloadFolder = ADDON.getSetting('download_folder')

    if ADDON.getSetting('ask_folder') == 'true':
        dialog = xbmcgui.Dialog()
	downloadFolder = dialog.browse(3, 'Save to folder...', 'files', '', False, False, downloadFolder)
	if downloadFolder == '' :
	    return None

    if downloadFolder is '':
        d = xbmcgui.Dialog()
	d.ok(TITLE,'You have not set the default download folder.\nPlease update the addon settings and try again.','','')
        ADDON.openSettings()
	downloadFolder = ADDON.getSetting('download_folder')

    if downloadFolder == '' and ADDON.getSetting('ask_folder') == 'true':
        dialog = xbmcgui.Dialog()
	downloadFolder = dialog.browse(3, 'Save to folder...', 'files', '', False, False, downloadFolder)	

    if downloadFolder == '' :
        return None

    title = url.split('/')[-1]
    ext   = title.split('.')[-1]

    if ext == 'm4a':
        ext = 'mp4'
        title = title[:-3]
        title = title + ext

    filename = ''
   
    if ADDON.getSetting('ask_filename') == 'true':
        kb = xbmc.Keyboard('', 'Save video as...' )
	kb.doModal()
	if kb.isConfirmed():
	    filename = kb.getText()
	else:
	    return None

    if filename == '':
        filename = title
    else:
        filename = re.sub('[:\\/*?\<>|"]+', '', filename)
        filename = filename + '.' + ext

    return os.path.join(downloadFolder, filename)


def Download(url):
    savePath = downloadPath(url)
  
    if not savePath:
        return

    tempPath = savePath.replace('\\', '/')
    tempPath = xbmc.translatePath(os.path.join(PROFILE, savePath.rsplit('/', 1)[-1]))
   
    time = str(225*len(savePath))
    xbmc.executebuiltin('XBMC.Notification(' + TITLE + ', Downloading: ' + savePath + ',' + time + ')')
    urllib.urlretrieve(url, tempPath)

    import sfile
    sfile.copy(tempPath, savePath)
    sfile.delete(tempPath)


def PlayPodcast(url, duration, thumbnail):
    if duration == None:
        duration = '0'
    duration = int(duration)

    if thumbnail == None:
        thumbnail = 'DefaultPlaylist.png'
        
    liz = xbmcgui.ListItem(name, iconImage = thumbnail, thumbnailImage = thumbnail)
    liz.setInfo('music', {'Title': name, "Duration" : duration})
    liz.setProperty('mimetype', 'audio/mpeg')

    #pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    #pl.clear()    
    #pl.add(url, liz)

    #xbmc.Player(xbmc.PLAYER_CORE_MPLAYER).play(pl)

    liz.setPath(url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


def find(f, seq):
    for item in seq:
        if f(item): 
            return item[1]
    return None


def GetOPML():
    global Year
    opml = ElementTree.fromstring(quicknet.getURL(URL, 3600)) # 1 hr  

    try:
        head = opml.find('head')
        date = head.findtext('dateModified').split(' ')
        Year = int(date[3])
    except:
        pass

    return opml


def FixString(str):
    return str.encode('utf-8', 'replace')   


def CleanString(str):
    str = str.replace('&gt;', '>')
    str = str.replace('&amp;', '&')
    return str


def Main():          
    xml = GetOPML()

    addDir('Search', 'Search', _SEARCH)

    for body in xml.findall('body'):
        for outer in body.findall('outline'):
            for outline in outer.findall('outline'):
                attributes = outline.items()
                fullname  = find(lambda item: item[0] == 'fullname',  attributes)
                networkId = find(lambda item: item[0] == 'networkId', attributes)
                if networkId and fullname:
                    content = outline.find('outline')
                    if content is not None:
                        addDir(fullname, networkId, _STATION)


def LoadStation(_networkId):
    xml = GetOPML()

    for body in xml.findall('body'):
        for outer in body.findall('outline'):
            for outline in outer.findall('outline'):
                networkId = find(lambda item: item[0] == 'networkId', outline.items())
                if networkId == _networkId:
                    for show in outline.findall('outline'):
                        attributes = show.items()
                        name    = find(lambda item: item[0] == 'text',        attributes)
                        desc    = find(lambda item: item[0] == 'description', attributes)
                        image   = find(lambda item: item[0] == 'imageHref',   attributes)
                        xmlUrl  = find(lambda item: item[0] == 'xmlUrl',      attributes) 
                        genre   = find(lambda item: item[0] == 'bbcgenres',   attributes) 
                        keyname = find(lambda item: item[0] == 'keyname',     attributes) 
                        addStation(name, xmlUrl, genre, keyname, image, desc)



def LoadShow(url, genre, keyname):
    xml = quicknet.getURL(url, 3600) # 1 hr
    xml = ElementTree.fromstring(xml)

    channel = xml.find('channel')
    title   = channel.findtext('title')
    imageT  = channel.find('image')
    image   = imageT.findtext('url')

    for item in channel.findall('item'):
        name     = item.findtext('title')
        desc     = item.findtext('description')
        url      = item.findtext('link')
        content  = item.find(".//{http://search.yahoo.com/mrss/}content")
        duration = find(lambda item: item[0] == 'duration',   content.items()) 
        addPodcast(name, url, genre, keyname, title, duration, image, desc)


def Search():
    kb = xbmc.Keyboard('', 'Search BBC Podcasts', False)
    kb.doModal()
    if not kb.isConfirmed():
          return

    search = kb.getText()
    if search == '':
        return

    url = 'http://www.bbc.co.uk/podcasts/search.json?q=' + search

    try:
        import json as simplejson 

        search = quicknet.getURL(url, 3600) # 1 hr

        jsn = simplejson.loads(search)

        for item in jsn:
            try:        
                title       = item['title']
                url         = item['link']  + '.rss' 
                description = item['description'].replace('<span class="pc-quickfind-match">', '').replace('</span>', '')
                thumb       = fixImage(item['image'], '256x256')
                fanart      = fixImage(item['image'], '1280x720')
                addSearchResult(title, url, thumb, fanart, description)
                print artwork
            except:
                pass

    except:
        pass

    #TODO genres


def LoadSearchResult(url):
    LoadShow(url, '', '')

                         
def get_params(path):
    params = {}
    path   = path.split('?', 1)[-1]
    pairs  = path.split('&')

    for pair in pairs:
        split = pair.split('=')
        if len(split) > 1:
            params[split[0]] = urllib.unquote_plus(split[1])

    return params
   

def addSearchResult(title, url, thumb, fanart, description):
    u  =  sys.argv[0]
    u += '?url='  + urllib.quote_plus(url)
    u += '&mode=' + str(_SEARCHRESULT) 

    try:    u += '&name=' + urllib.quote_plus(title)
    except: u += '&name=' + urllib.quote_plus('title')

    liz = xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)

    liz.setInfo(type='music', infoLabels={'Title':title, 'comment':description, 'year':Year, 'artist':' ', 'genre':' ', 'album':title} ) 

    liz.setProperty('Fanart_Image', fanart)    

    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)        


def fixImage(image, resolution):
    image = image.replace('80x80',     resolution)
    image = image.replace('304x304',   resolution)
    image = image.replace('1408x1408', resolution)
    return image


def addPodcast(name, url, genre, keyname, title, duration, _thumbnail = 'DefaultPlaylist.png', desc=''):
    thumbnail = fixImage(_thumbnail, '256x256')
    fanart    = fixImage(_thumbnail, '1280x720')

    name = FixString(name)
    desc = FixString(desc)

    if duration == None:
        duration = '0'

    u   = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(_PODCAST) + "&name=" + urllib.quote_plus(name) + "&duration=" + urllib.quote_plus(duration) + "&thumbnail=" + urllib.quote_plus(thumbnail)
        
    liz = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)

    liz.setInfo(type='music', infoLabels={"Title": name, "comment" : desc, "year" : Year, "artist" : keyname, "genre" : genre, "album" : title} )    

    liz.setProperty('Fanart_Image', fanart)    
    liz.setProperty('IsPlayable', 'true')

    contextMenu = []
    contextMenu.append(('Download', 'XBMC.RunPlugin(%s?mode=%s&url=%s)' % (sys.argv[0], str(_DOWNLOAD), url)))
    liz.addContextMenuItems(contextMenu)    

    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = False)


def addStation(name, url, genre, keyname, _thumbnail = 'DefaultPlaylist.png', desc=''):
    thumbnail = fixImage(_thumbnail, '256x256')
    fanart    = fixImage(_thumbnail, '1280x720')

    name = FixString(name)
    desc = FixString(desc)

    u   = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(_SHOW) + "&name=" + urllib.quote_plus(name) + "&genre=" + urllib.quote_plus(genre) + "&keyname=" + urllib.quote_plus(keyname)
        
    liz = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)

    liz.setInfo(type='music', infoLabels={"Title": name, "comment" : desc, "year" : Year, "artist" : keyname, "genre" : genre, "album" : name} )        

    liz.setProperty('Fanart_Image', fanart)  

    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = True)        



def addDir(name, url, mode, thumbnail = 'DefaultPlaylist.png'):
    name = FixString(name)

    u   = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
        
    liz = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)

    liz.setInfo(type='', infoLabels={"Title": name})

    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = True)



params=get_params(sys.argv[2])


url       = None
name      = None
mode      = None
genre     = None
keyname   = None
duration  = None
thumbnail = None


try:    url = params['url']
except: pass

try:    name = params['name']
except: pass

try:    mode = int(params['mode'])
except: pass


#print 'Mode: %s' % str(mode)
#print 'URL : %s' % str(url)
#print 'Name: %s' % str(name)


if mode == _STATION:
    LoadStation(url)


elif mode == _SHOW:
    try:    genre = params['genre']
    except: pass

    try:    keyname = params['keyname']
    except: pass

    LoadShow(url, genre, keyname)


elif mode == _DOWNLOAD:
    Download(url)


elif mode == _PODCAST:
    try:    duration = params['duration']
    except: pass

    try:    thumbnail = params['thumbnail']
    except: pass
  
    PlayPodcast(url, duration, thumbnail)


elif mode == _SEARCH:
    Search()


elif mode == _SEARCHRESULT:
    LoadSearchResult(url)

else:
    Main()

        
xbmcplugin.endOfDirectory(int(sys.argv[1]))