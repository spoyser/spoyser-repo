import urllib
import geturllib
import xbmcplugin
import xbmcgui
import xbmcaddon
import time
import re
import os
from xml.etree import ElementTree
import threading
import json


_STATION      = 100
_SHOW         = 200
_PODCAST      = 300
_DOWNLOAD     = 400
_SEARCH       = 500
_SEARCHRESULT = 600

NAME  = 'plugin.audio.bbcpodcasts'
TITLE = 'BBC Podcasts'
ADDON = xbmcaddon.Addon(id = NAME)
URL   = ADDON.getSetting('URL') # http://www.bbc.co.uk/podcasts.opml
PATH  = xbmc.translatePath(os.path.join('special://profile', 'addon_data', NAME))

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
	ADDON.openSettings(sys.argv[0])
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
    savePath   = downloadPath(url)
   
    if savePath:
        time = str(225*len(savePath))
        xbmc.executebuiltin("XBMC.Notification(" + TITLE + ", Downloading: " + savePath + "," + time + ")")
        urllib.urlretrieve(url, savePath)


def PlayPodcast(url, duration, thumbnail):
    if duration == None:
        duration = '0'
    duration = int(duration)

    if thumbnail == None:
        thumbnail = 'DefaultPlaylist.png'
        
    liz = xbmcgui.ListItem(name, iconImage = thumbnail, thumbnailImage = thumbnail)
    liz.setInfo('music', {'Title': name, "Duration" : duration})
    liz.setProperty('mimetype', 'audio/mpeg')
    liz.setProperty('IsPlayable', 'true')

    pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    pl.clear()    
    pl.add(url, liz)

    xbmc.Player(xbmc.PLAYER_CORE_MPLAYER).play(pl)


def find(f, seq):
    for item in seq:
        if f(item): 
            return item[1]
    return None


def GetOPML():
    global Year
    opml = ElementTree.fromstring(geturllib.GetURL(URL, 3600)) # 1 hr  

    try:
        head = opml.find('head')
        date = head.findtext('dateModified').split(' ')
        Year = int(date[3])
    except:
        pass

    return opml


def FixString(_str):
    return _str.encode('utf-8', 'replace')   


def CleanString(_str):
    _str = _str.replace('&gt;', '>')
    _str = _str.replace('&amp;', '&')
    return _str


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
    xml = ElementTree.fromstring(geturllib.GetURL(url, 3600)) # 1 hr

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


    #http://www.bbc.co.uk/podcasts/search.jsonp?q=m&callback=podcastCallback
    #url = 'http://www.bbc.co.uk/podcasts/quick_search/' + search
    url = 'http://www.bbc.co.uk/podcasts/search.jsonp?q=' + search


    try:
        search = geturllib.GetURL(url, 3600) # 1 hr
        search = search.split('(', 1)[1]
        search = search.rsplit(')', 1)[0]

        jsn = json.loads(search)

        for item in jsn:
            fullTitle   = item['fullTitle']
            shortTitle  = item['shortTitle']
            description = item['podDescription']
            artwork     = 'http://static.bbci.co.uk/podcasts/artwork/' + shortTitle + '.jpg'
            addSearchResult(fullTitle, shortTitle, artwork, description)
    except:
        pass

    #TODO genres


def LoadSearchResult(url):
    url = 'http://www.bbc.co.uk/podcasts/series/' + url

    try:
        response = geturllib.GetURL(url, 3600) # 1 hr
        rss      = 'http://downloads' + re.compile('downloads(.+?)rss.xml').findall(response)[0] + 'rss.xml'
        #keyname  = re.findall("var keyname = '(.+?)'", response)[0]
        keyname  = re.findall('class="pc-desktop pc-keyname-(.+?)">', response)[0]
        genres   = re.findall('ul class="pc-results-box-genres">(.+?)</ul>', response)[0]
        genres   = re.findall('<li>(.+?)</li>', genres)
        genre    = ''
        for g in genres:
            genre = genre + CleanString(g) + ', '
        if len(genre) > 2:
            genre = genre[:-2]
        LoadShow(rss, genre, keyname)
    except:
        pass

                         
def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
           params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param


def addSearchResult(fullTitle, shortTitle, artwork, description):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(shortTitle) + "&mode=" + str(_SEARCHRESULT) + "&name=" + urllib.quote_plus(fullTitle)

    liz = xbmcgui.ListItem(fullTitle, iconImage=artwork, thumbnailImage=artwork)

    liz.setInfo(type='music', infoLabels={"Title" : fullTitle, "comment" : description, "year" : Year, "artist" : shortTitle, "genre" : ' ', "album" : fullTitle} )        

    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = True)        


def addPodcast(name, url, genre, keyname, title, duration, thumbnail = 'DefaultPlaylist.png', desc=''):
    name = FixString(name)
    desc = FixString(desc)

    if duration == None:
        duration = '0'

    u   = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(_PODCAST) + "&name=" + urllib.quote_plus(name) + "&duration=" + urllib.quote_plus(duration) + "&thumbnail=" + urllib.quote_plus(thumbnail)
        
    liz = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)

    liz.setInfo(type='music', infoLabels={"Title": name, "comment" : desc, "year" : Year, "artist" : keyname, "genre" : genre, "album" : title} )    

    contextMenu = []
    contextMenu.append(('Download', 'XBMC.RunPlugin(%s?mode=%s&url=%s)' % (sys.argv[0], str(_DOWNLOAD), url)))
    liz.addContextMenuItems(contextMenu)    

    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = False)


def addStation(name, url, genre, keyname, thumbnail = 'DefaultPlaylist.png', desc=''):
    name = FixString(name)
    desc = FixString(desc)

    u   = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(_SHOW) + "&name=" + urllib.quote_plus(name) + "&genre=" + urllib.quote_plus(genre) + "&keyname=" + urllib.quote_plus(keyname)
        
    liz = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)

    liz.setInfo(type='music', infoLabels={"Title": name, "comment" : desc, "year" : Year, "artist" : keyname, "genre" : genre, "album" : name} )        

    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = True)        



def addDir(name, url, mode, thumbnail = 'DefaultPlaylist.png'):
    name = FixString(name)

    u   = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
        
    liz = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)

    liz.setInfo(type='', infoLabels={"Title": name})

    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = True)


if __name__ == "__main__":
    try:
        geturllib.SetCacheDir(xbmc.translatePath(os.path.join("special://profile", "addon_data", 'plugin.audio.bbcpodcasts','cache' ) ) )
    except:
        pass


params=get_params()

url       = None
name      = None
mode      = None
genre     = None
keyname   = None
duration  = None
thumbnail = None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass

try:
    name=urllib.unquote_plus(params["name"])
except:
    pass

try:
    mode=int(params["mode"])
except:
    pass


#print "Mode: " + str(mode)
#print "URL: "  + str(url)
#print "Name: " + str(name)

if (mode == None) or (url == None) or (len(url) < 1):
    Main()

elif mode == _STATION:
    LoadStation(url)

elif mode == _SHOW:
    try:
        genre=urllib.unquote_plus(params["genre"])
    except:
        pass

    try:
        keyname=urllib.unquote_plus(params["keyname"])
    except:
        pass

    LoadShow(url, genre, keyname)

elif mode == _DOWNLOAD:
    Download(url)

elif mode == _PODCAST:
    try:
        duration=urllib.unquote_plus(params["duration"])
    except:
        pass

    try:
        thumbnail=urllib.unquote_plus(params["thumbnail"])
    except:
        pass

    PlayPodcast(url, duration, thumbnail)

elif mode == _SEARCH:
    Search()

elif mode == _SEARCHRESULT:
    LoadSearchResult(url)
        
xbmcplugin.endOfDirectory(int(sys.argv[1]))