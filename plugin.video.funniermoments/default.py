#
#      Copyright (C) 2013 Sean Poyser
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
import urllib2
import random
import re
import os

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui

ADDONID = 'plugin.video.funniermoments'
ADDON   = xbmcaddon.Addon(ADDONID)
HOME    = ADDON.getAddonInfo('path')
ARTWORK = os.path.join(HOME, 'resources', 'artwork')
ICON    = os.path.join(HOME, 'icon.png')
TITLE   = 'Funnier Moments'
VERSION = '1.0.12'
URL     = 'http://www.funniermoments.com/'
MOBILE  = False


ALL      = 100
NEW      = 200
TOP      = 300
RANDOM   = 400
PROGRAM  = 500
CARTOON  = 600
KIDSTIME = 700
SEARCH   = 800
LIBRARY  = 900
DOWNLOAD = 1000
MORE     = 1100


def CheckVersion():
    prev = ADDON.getSetting('VERSION')
    curr = VERSION

    if prev == curr:
        return

    ADDON.setSetting('VERSION', curr)

    d = xbmcgui.Dialog()

    #if prev == '0.0.0':
    #    d.ok(TITLE + ' - ' + VERSION, 'Funnier Moments acquires distribution rights for all videos', 'This costs money - please consider a small donation', 'via the website - www.funniermoments.com')
        
    d.ok(TITLE + ' - ' + VERSION, 'Funnier Moments acquires distribution rights for all videos', 'This costs money - please consider a small donation', 'via the website - www.funniermoments.com')



def Clean(text):
    text = text.replace('&#8211;', '-')
    text = text.replace('&#8217;', '\'')
    text = text.replace('&#8220;', '"')
    text = text.replace('&#8221;', '"')
    text = text.replace('&#39;',   '\'')
    text = text.replace('&euml;',  'e')
    text = text.replace('<b>',     '')
    text = text.replace('</b>',    '')
    text = text.replace('&amp;',   '&')
    text = text.replace('\ufeff', '')
    text = text.replace('&nbsp;', ' ')
    return text.strip()


def FixURL(url):
    url = url.replace('\\\'', '%27')
    return url



def PostHTML(url, data, maxAge = 86400):
    html = geturllib.PostURL(url, data, maxAge)
    html = html.replace('\n', '')
    html = html.replace('\t', '')
    return html


def GetHTML(url, maxAge = 86400):
    html = geturllib.GetURL(url,maxAge)
    html = html.replace('\n', '')
    html = html.replace('\t', '')
    return html


def Main():
    CheckVersion()

    AddSection('Kids Time',      'kidstime', KIDSTIME, False)    
    AddSection('All Moments',    'all',      ALL)
    AddSection('New Moments',    'new',      NEW)
    AddSection('Top Moments',    'top',      TOP)
    AddSection('Random Moment',  'random',   RANDOM,   False)
    AddSection('Search Moments', 'search',   SEARCH)


def AddSection(name, image, mode, isFolder=True):
    AddDir(name, mode, image=os.path.join(ARTWORK, image+'.png'), isFolder=isFolder)


def AddMore(mode, url, page, keyword = None):
    AddDir('More Moments...', mode, url, image=os.path.join(ARTWORK, 'more.png'), page=page, keyword=keyword)


def AddDir(name, mode, url='', image=None, isFolder=True, page=1, keyword=None, infoLabels=None, contextMenu=None):
    name = Clean(name)

    if not image:
        image = ICON

    u  = sys.argv[0] 
    u += '?mode='  + str(mode)
    u += '&title=' + urllib.quote_plus(name)
    u += '&image=' + urllib.quote_plus(image)
    u += '&page='  + str(page)

    if url != '':     
        u += '&url='   + urllib.quote_plus(url) 

    if keyword:
        u += '&keyword=' + urllib.quote_plus(keyword) 

    liz = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)

    if contextMenu:
        liz.addContextMenuItems(contextMenu)

    if infoLabels:
        liz.setInfo(type="Video", infoLabels=infoLabels)

    if not isFolder:
        liz.setProperty("IsPlayable","true")


    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=isFolder)


def All():
    html  = GetHTML(URL)
    html  = html.replace('&nbsp;&nbsp;&nbsp;', '')
    match = re.compile('<li class=""><a href="(.+?)" class="">(.+?) \(.+?\)</a></li>').findall(html)

    list = []

    for url, title in match:
        if title not in list:
            menu = []
            menu.append(('Add To Library', 'XBMC.RunPlugin(%s?mode=%d&title=%s&url=%s)' % (sys.argv[0], LIBRARY, urllib.quote_plus(title), urllib.quote_plus(url))))

            list.append(title)            
            AddProgram(title, url, 1, menu)


def Program(_url, page):
    page  = int(page)
    url   = _url + '&' + 'order=ASC&page=' + str(page)
    html  = GetHTML(url)

    main = re.compile('<h2><p>(.+?)</p></h2>').search(html).group(1)

    split = '<h2><p>%s</p></h2>' % main
    html  = html.split(split, 1)[-1]
    #html = html.split('http://www.yesads.com', 1)[-1]

    match = re.compile('<a href="(.+?)" class="pm-thumb-fix pm-thumb-145"><span class="pm-thumb-fix-clip"><img src="(.+?)" alt="(.+?)" width="145"><span class="vertical-align"></span></span></a>.+?watch.php').findall(html)

    for url, img, title in match:
        url  = url.split('"',     1)[0]

        try:    title = title.split(' - ', 1)[1]
        except: pass

        AddCartoon(title, url, img)

    next = _url.rsplit('/', 1)[1].split('&', 1)[0]
    next += '&page=%d' % (page+1)

    if next in html:
        AddMore(PROGRAM, _url, page+1)


def New():
    url  = URL + 'newvideos.php'
    html = GetHTML(url)

    split = 'class="pm-ul-new-videos thumbnails'
    html  = html.split(split, 1)[-1]    
    
    match = re.compile('<a href="(.+?)" class="pm-thumb-fix pm-thumb-145"><span class="pm-thumb-fix-clip"><img src="(.+?)" alt="(.+?)" width="145"><span class="vertical-align"></span></span></a>.+?<div class="pm-li-video">').findall(html)

    for url, img, title in match:
        url   = url.split('"',     1)[0]

        #try:    title = title.split(' - ', 1)[1]
        #except: pass

        AddCartoon(title, url, img)


def Top(page):
    page = int(page)

    _url = 'topvideos.php?&page='
    url  = URL + _url + str(page)
    html = GetHTML(url)
    
    match = re.compile('<span class="pm-video-rank">(.+?)</span>.+?<a href="(.+?)" class="pm-thumb-fix pm-thumb-194"><span class="pm-thumb-fix-clip"><img src="(.+?)" alt="(.+?)" width="194"><span class="vertical-align"></span></span></a>').findall(html)

    for rank, url, img, title in match:   
        AddCartoon(rank + ': ' + title, url, img)

    page += 1
    next  = _url + str(page)

    if next in html:
        AddMore(TOP, _url, page)


def GetRandom():
    url  = URL + 'randomizer.php'
    html = GetHTML(url, 0) 

    try:    title = re.compile('title" content="Watch (.+?) Full Episode Online 4 FREE in HIGH QUALITY"').search(html).group(1)
    except: pass

    try:    id    = re.compile('watch.php\?vid=(.+?)"').search(html).group(1)
    except: pass

    try:    url   = 'http://www.funniermoments.com/watch.php?vid=%s'        % id
    except: pass

    try:    img   = 'http://www.funniermoments.com/uploads/thumbs/%s-1.jpg' % id
    except: pass

    return title, img, url


def Random():
    title, img, url = GetRandom()
    PlayCartoon(title, img, url)


def AddCartoon(title, url, image):
    image += '|referer=http://www.funniermoments.com'

    menu = []
    menu.append(('Download', 'XBMC.RunPlugin(%s?mode=%d&title=%s&url=%s)' % (sys.argv[0], DOWNLOAD, urllib.quote_plus(title), urllib.quote_plus(url))))


    AddDir(title, CARTOON, url, image, isFolder=False, contextMenu=menu)


def AddProgram(title, url, page, menu):
    AddDir(title, PROGRAM, url, page=page, contextMenu=menu)


def Download(title, _url):
    file = DownloadPath(_url)
    if not file:
        return

    url  = GetCartoonURL(_url)
    url  = url.rsplit('|', 1)[0]

    try:
        import download
        download.download(url, file)
    except Exception, e:
        print TITLE + ' Error during downloading of ' + _url
        print str(e)


def FileSystemSafe(text):
    text = re.sub('[:\\/*?\<>|"]+', '', text)
    return text.strip()


def DownloadPath(url):          
    downloadFolder = ADDON.getSetting('DOWNLOAD_FOLDER')

    if ADDON.getSetting('ASK_FOLDER') == 'true':
        dialog = xbmcgui.Dialog()
    downloadFolder = dialog.browse(3, 'Download to folder...', 'files', '', False, False, downloadFolder)
    if downloadFolder == '' :
        return None

    if downloadFolder is '':
        d = xbmcgui.Dialog()
    d.ok('Funnier Moments', 'You have not set the default download folder.\nPlease update the addon settings and try again.','','')
    ADDON.openSettings() 
    downloadFolder = ADDON.getSetting('DOWNLOAD_FOLDER')

    if downloadFolder == '' and ADDON.getSetting('ASK_FOLDER') == 'true':
        dialog = xbmcgui.Dialog()
    downloadFolder = dialog.browse(3, 'Download to folder...', 'files', '', False, False, downloadFolder)   

    if downloadFolder == '' :
        return None

    downloadFolder = xbmc.translatePath(downloadFolder)

    html   = GetHTML(url)
    info   = re.compile('<h3 class="entry-title">(.+?)</h3>').search(html).group(1)
    series = FileSystemSafe(info.split(' - ', 1)[0])
    title  = FileSystemSafe(info.split(' - ', 1)[-1])

    season, episode, name = GetSeasonInfo(title)

    filename = '%s - %sx%s' % (name, season, episode)
   
    if ADDON.getSetting('ASK_FILENAME') == 'true':        
        kb = xbmc.Keyboard(filename, 'Download Cartoon as...' )
    kb.doModal()
    if kb.isConfirmed():
        filename = kb.getText()
    else:
        return None

    ext      = 'mp4'
    filename = FileSystemSafe(filename) + '.' + ext

    if not os.path.exists(downloadFolder):
        os.mkdir(downloadFolder)

    downloadFolder = os.path.join(downloadFolder, series)
    if not os.path.exists(downloadFolder):
        os.mkdir(downloadFolder)

    return os.path.join(downloadFolder, filename)


def AddToLibrary(series, _url, page):
    page  = int(page)
    url   = _url + '&' + 'order=ASC&page=' + str(page)
    html  = GetHTML(url)

    main = re.compile('<h2>(.+?)</h2>').search(html).group(1)
    split = '<h2>%s</h2>' % main

    html  = html.split(split, 1)[1]

    match = re.compile('<a href="(.+?)" class="pm-thumb-fix pm-thumb-145"><span class="pm-thumb-fix-clip"><img src="(.+?)" alt="(.+?)" width="145"><span class="vertical-align"></span></span></a>.+?watch.php').findall(html)

    index = len(match)

    for url, img, title in match:
        url  = url.split('"', 1)[0]

        try:    title = title.split(' - ', 1)[1]
        except: pass

        AddCartoonToLibrary(series, title, url, img, index)
        index -= 1

    next = _url.rsplit('/', 1)[1].split('&', 1)[0]
    next += '&page=%d' % (page+1)

    if next in html:
        AddToLibrary(series, _url, page+1)


def AddCartoonToLibrary(series, title, url, img, index):
    try:
        series  = Clean(series)
        series  = FixNameForLibrary(series)
        series  = FileSystemSafe(series)
        library = xbmc.translatePath(ADDON.getSetting('LIBRARY'))
        if not os.path.exists(library):
            os.mkdir(library)

        season, episode, name = GetSeasonInfo(title, index)

        library = os.path.join(library, series)
        if not os.path.exists(library):
            os.mkdir(library)

        library = os.path.join(library, 'Season %s' % season)
        if not os.path.exists(library):
            os.mkdir(library)

        episode = FixEpisodeForLibrary(series, episode)

        filename = '%sx%s - %s.strm' % (season, episode, name)
        fullname = os.path.join(library, filename)

        strm = '%s?mode=%d&url=%s&title=%s&image=%s&'% (sys.argv[0], CARTOON, urllib.quote_plus(url), urllib.quote_plus(title), urllib.quote_plus(img))
        
        file = open(fullname, 'w')
        file.write(strm)
        file.close()

    except Exception, e:
        print str(e)
        pass


def GetSeasonInfo(title, index = 0):
    items = title.split(' - ', 1)
    info  = items[0]

    try:
        name  = items[1]

        if 'x' in info:
            season = int(info.split('x', 1)[0])
        else:
            season = 1

        episode  = info.split('x', 1)[-1]
        name     = Clean(name)
    except:
        season  = 1
        episode = index
        name    = info

    name = FileSystemSafe(name)

    return season, episode, name 


def FixEpisodeForLibrary(series, episode):
    SERIES = series.upper()
    if SERIES == 'THE IMPOSSIBLES' and episode == '01':
        return '02'
    if SERIES == 'THE IMPOSSIBLES' and episode == '02':
        return '03'
    if SERIES == 'THE IMPOSSIBLES' and episode == '03':
        return '04'
    if SERIES == 'THE IMPOSSIBLES' and episode == '04':
        return '01'

    return episode


def FixNameForLibrary(series):
    SERIES = series.upper()

    if 'THE ADDAMS FAMILY' in SERIES:
        return 'The Addams Family (1973)'

    if 'THE ADVENTURES OF DON COYOTE' in SERIES:
        return 'Don Coyote and Sancho Panda'

    if 'AUGGIE DOGGIE & DOGGIE DADDY' in SERIES:
        return 'Augie Doggie & Doggie Daddy'
    
    if 'PAC-MAN (THE SERIES)' in SERIES:
        return 'Pac-Man'

    if 'SCOOBY\'S ALL-STAR LAFF-A-LYMPICS' in SERIES:
        return 'Scooby\'s All Star Laff-A-Lympics'

    if 'COPS (THE ANIMATED SERIES)' in SERIES:
        return 'C.O.P.S'

    if 'COW & CHICKEN' in SERIES:
        return 'Cow and Chicken'

    if 'THE FUNKY PHANTOM' in SERIES:
        return 'Funky Phantom'

    if 'GOOBER' in SERIES:
        return 'Goober and the Ghost-Chasers'

    if 'HEATHCLIFF & DINGBAT SHOW' in SERIES:
        return 'Heathcliff'

    if 'GRAPE APE' in SERIES:
        return 'Grape Ape'

    return series
    

def GetCartoonURL(url):
    html  = GetHTML(url)
    match = re.compile('http://funniermoments.com/vids/(.+?).mp4').search(html).group(1)
    url   = 'http://funniermoments.com/vids/%s.mp4' % match
    url   = FixURL(url)
    url  += '|referer=http://www.funniermoments.com'
    return url


def PlayCartoon(title, image, url):
    if not url:
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem('title'))

    url = GetCartoonURL(url)

    if '|referer=' not in image:
        image += '|referer=http://www.funniermoments.com'

    liz = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)

    liz.setInfo( type="Video", infoLabels={ "Title": title} )
    liz.setPath(url)

    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
   

def KidsTime():
    pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    pl.clear()  

    titles = []

    for i in range(0, 10):
        title, image, url = GetRandom()  
        if title not in titles:
            titles.append(title)
            url = GetCartoonURL(url)

            liz = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)

            liz.setInfo( type="Video", infoLabels={"Title": title})

            pl.add(url, liz)

            if i == 0:
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
    

def GetSearchKeyword():
    kb = xbmc.Keyboard('', TITLE, False)
    kb.doModal()
    if not kb.isConfirmed():
        return None

    text = kb.getText()

    if text == '':
        return None

    return text


def Search(page, keyword):
    if not keyword or keyword == '':
        keyword = GetSearchKeyword()
    if not keyword or keyword == '':
        return

    page = int(page)

    _url = 'search.php?keywords=%s&page=' % urllib.quote_plus(keyword)
    url  = URL + _url + str(page)

    html = GetHTML(url)
    html = html.split('Search Results')[-1]

    match = re.compile('<a href="(.+?)" class="pm-thumb-fix pm-thumb-145"><span class="pm-thumb-fix-clip"><img src="(.+?)" alt="(.+?)" width="145"><span class="vertical-align"></span></span></a>.+?watch.php').findall(html)

    for url, img, title in match:
        AddCartoon(title, url, img)

    page += 1
    _url += str(page) 
    _url  = urllib.unquote_plus(_url)

    if _url in html:
        AddMore(SEARCH, '', page, keyword)
    
    
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



import geturllib
geturllib.SetCacheDir(xbmc.translatePath(os.path.join('special://profile', 'addon_data', ADDONID ,'cache')))

params = get_params()
mode   = None

try:    mode = int(urllib.unquote_plus(params['mode']))
except: pass

#print "***** MODE *********"
#print mode

if mode == ALL:
    All()

elif mode == NEW:
    New()

elif mode == TOP:
    page = urllib.unquote_plus(params['page'])
    Top(page)

elif mode == PROGRAM:
    url  = urllib.unquote_plus(params['url'])
    page = urllib.unquote_plus(params['page'])
    Program(url, page)


elif mode == MORE:
    url = urllib.unquote_plus(params['url'])
    More(url)


elif mode == CARTOON:
    url   = urllib.unquote_plus(params['url'])
    title = urllib.unquote_plus(params['title'])
    image = urllib.unquote_plus(params['image'])
    PlayCartoon(title, image, url)


elif mode == LIBRARY:
    url   = urllib.unquote_plus(params['url'])
    title = urllib.unquote_plus(params['title'])
    AddToLibrary(title, url, 1)


elif mode == DOWNLOAD:
    url   = urllib.unquote_plus(params['url'])
    title = urllib.unquote_plus(params['title'])
    Download(title, url)


elif mode == RANDOM:
    Random()

elif mode == KIDSTIME:
    KidsTime()


elif mode == SEARCH:
    page    = 1
    keyword = ''
    try:
        page    = urllib.unquote_plus(params['page'])
        keyword = urllib.unquote_plus(params['keyword'])
    except:
        pass
    Search(page, keyword)

else:
    Main()

        
try:
    #xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
except:
    pass

