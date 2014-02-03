
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

ADDONID = 'plugin.video.supercartoons'
ADDON   = xbmcaddon.Addon(ADDONID)
HOME    = ADDON.getAddonInfo('path')
ARTWORK = os.path.join(HOME, 'resources', 'artwork')
ICON    = os.path.join(HOME, 'icon.png')
TITLE   = 'Super Cartoons'
VERSION = '1.0.3'
URL     = 'http://www.supercartoons.net/'


KIDSTIME   = 100
RECENT     = 200
POPULAR    = 300
CHARACTERS = 400
CHARACTER  = 500
STUDIOS    = 600
STUDIO     = 700
RANDOM     = 800
ALL        = 900
CARTOON    = 1000
SEARCH     = 1100
DOWNLOAD   = 1200


def CheckVersion():
    prev = ADDON.getSetting('VERSION')
    curr = VERSION

    if prev == curr:
        return

    ADDON.setSetting('VERSION', curr)

    if prev == '0.0.0':
        d = xbmcgui.Dialog()
        d.ok(TITLE + ' - ' + VERSION, 'Welcome to Super Cartoons', 'Watch Your Favourite Cartoons in XBMC', '')


def GetUrlAndNext(url, page):
    page  = int(page)
    items = url.split('/')

    url  = ''
    url += items[0] + '/'
    url += items[1] + '/'
    url += items[2] + '/'
    url += items[3] + '/'
    url += items[4].split('-')[0] + '-' + str(page) + '/'
    url += items[5]

    next  = ''
    next += items[0] + '/'
    next += items[1] + '/'
    next += items[2] + '/'
    next += items[3] + '/'
    next += items[4].split('-')[0] + '-' + str(page+1) + '/'
    #next += items[5] #ignore character name as it is sometimes wrong on website

    return url, next


def Clean(text):
    text = text.replace('&#8211;', '-')
    text = text.replace('&#8217;', '\'')
    text = text.replace('&#8220;', '"')
    text = text.replace('&#8221;', '"')
    text = text.replace('&#39;',   '\'')
    text = text.replace('<b>',     '')
    text = text.replace('</b>',    '')
    text = text.replace('&amp;',   '&')
    return text


def GetHTML(url):
    html, cached = geturllib.GetURL(url, 86400)
    html         = html.replace('\n',            '')
    html         = html.replace('&quot;',        '"')
    html         = html.replace('title="Search', '')
    return html


def Main():
    CheckVersion()
    
    AddSection('Kids Time',     'kidstime',   KIDSTIME, False)
    AddSection('Random',        'random',     RANDOM,   False)
    AddSection('All',           'all',        ALL)
    AddSection('Most Recent',   'recent',     RECENT)
    AddSection('Most Popular',  'popular',    POPULAR)
    AddSection('Characters',    'characters', CHARACTERS)
    AddSection('Studios',       'studios',    STUDIOS)
    AddSection('Search',        'search',     SEARCH)


def All(page):
    page  = int(page)
    url   = URL + 'cartoons/' + str(page)
    next  = URL + 'cartoons/' + str(page+1)

    html  = GetHTML(url)
    match = re.compile('title="(.+?)">.+?<img src="(.+?)".+?<span class="title">.+?<a href="(.+?)".+?">(.+?)</a>').findall(html)

    for desc, img, link, title in match:
        AddCartoon(title, img, link, desc) 

    if next in html:
        AddMore(ALL, URL, page+1)


def KidsTime():
    pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    pl.clear()  

    for i in range(0, 10):
        title, image, url = GetRandom()  

        liz = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)

        liz.setInfo( type="Video", infoLabels={"Title": title})

        pl.add(url, liz)

        if i == 0:
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
    

def Random():
    title, image, url = GetRandom()
    PlayCartoon(title, image, url)


def GetRandom():
    page = random.randrange(1, 57+1)

    url = URL + 'cartoons/' + str(page)

    cartoons = []

    html  = GetHTML(url)
    match = re.compile('title="(.+?)">.+?<img src="(.+?)".+?<span class="title">.+?<a href="(.+?)".+?">(.+?)</a>').findall(html)

    for desc, img, link, title in match:
        link = link.replace('/cartoon/', '/video/')
        link = link.replace('.html', '.mp4')
        cartoons.append([title, img, link])

    index = random.randrange(0, len(cartoons))

    title = cartoons[index][0]
    image = cartoons[index][1]
    url   = cartoons[index][2]

    return title, image, url


def GetSearchTitle(title):
    title = Clean(title)
    title = RemoveCharacter(title)
    title = title.replace(' - Super Cartoons', '')

    if title.startswith('- '):
        title = title[2:]
    return title


def RemoveCharacter(title):
    uTitle = title.upper()
    remove = ['MICKEY-MOUSE', 'DONALD-DUCK', 'GOOFY', 'PLUTO', 'CHIP-AND-DALE', 'DAISY-DUCK', 'FIGARO', 'MINNIE-MOUSE', 'HUEY-DEWEY-LOUIE', 'HUMPHREY-THE-BEAR', 'WILE-E.-COYOTE', 'ROAD-RUNNER', 'PORKY-PIG', 'DAFFY-DUCK', 'ELMER-FUDD', 'BUGS-BUNNY', 'HENERY-HAWK', 'TWEETY', 'SYLVESTER', 'YOSEMITE-SAM', 'SPEEDY-GONZALES', 'TASMANIAN-DEVIL', 'TOM-JERRY', 'THE-PINK-PANTHER', 'POPEYE', 'PEPE-LE-PEW', 'BARNYARD-DAWG', 'RALPH-WOLF-AND-SAM-SHEEPDOG', 'FOGHORN-LEGHORN']

    for item in remove:
        if uTitle.startswith(item):
            return title[len(item)+1:]

    return title


def GetSearchImage(link):
    title = link.rsplit('/', 1)[1].rsplit('.', 1)[0]
    title = URL + 'images/cartoons/' + RemoveCharacter(title) + '.jpg'

    return title


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

    page     = int(page)
    nResults = int(ADDON.getSetting('SEARCH'))
    keyword  = urllib.quote_plus(keyword)
    start    = (page-1) * nResults

    url = 'http://www.google.co.uk/search?q=site:http://www.supercartoons.net/cartoon+%s&start=%d&num=%d' % (keyword, start, nResults)

    html = GetHTML(url)
    main = re.compile('<table style(.+?)</table>').findall(html)
    for item in main:
        if 'supercartoons' in item:
            item  = item.split('href')[2]            
            item  = re.compile('q=(.+?).html.+?">(.+?)</a>').findall(item)

            link  = item[0][0] + '.html'
            title = GetSearchTitle(item[0][1])
            image = GetSearchImage(link)

            AddCartoon(title, image, link, '')

    if 'nav_next_2.gif' in html:
        AddMore(SEARCH, '', page+1, keyword)


def PlayCartoon(title, image, url):
    liz = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)

    liz.setInfo( type="Video", infoLabels={ "Title": title} )
    liz.setPath(url)

    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


def MostRecent():
    html  = GetHTML(URL)
    #match = re.compile('Most Recently Added Cartoons(.+?)Most Popular Cartoons').search(html).group(1)
    match = re.compile('<h3>Best Cartoons</h3>(.+?)<h3>Cartoons</h3>').search(html).group(1)
    match = re.compile('title="(.+?)">.+?<img src="(.+?)".+?<span class="title">.+?<a href="(.+?)".+?">(.+?)</a>').findall(match)

    for desc, img, link, title in match:
        AddCartoon(title, img, link, desc)


def MostPopular():
    html  = GetHTML(URL)
    #match = re.compile('Most Popular Cartoons(.+?)</html>').search(html).group(1)
    match = re.compile('<h3>Best Cartoons</h3>.+?<h3>Cartoons</h3>(.+?)</div></div>').search(html).group(1)
    match = re.compile('title="(.+?)">.+?<img src="(.+?)".+?<span class="title">.+?<a href="(.+?)".+?">(.+?)</a>').findall(match)

    for desc, img, link, title in match:
        AddCartoon(title, img, link, desc)  


def Studios(page):
    #only one at the moment
    DoStudios(1)


def DoStudios(page):
    url   = URL + 'studios/' + str(page)
    html  = GetHTML(url)
    match = re.compile('title="(.+?)">.+?<img src="(.+?)".+?<span class="title">.+?<a href="(.+?)".+?">(.+?)</a>').findall(html)

    for desc, img, link, title in match:
        AddStudio(title, img, link, desc)


def Studio(_url, page):
    page = int(page)

    url, next = GetUrlAndNext(_url, page)

    html  = GetHTML(url)
    match = re.compile('title="(.+?)">.+?<img src="(.+?)".+?<a class="title" href="(.+?)".+?">(.+?)</a>').findall(html)

    for desc, img, link, title in match:
        AddCartoon(title, img, link, desc)

    if next in html:
        AddMore(STUDIO, _url, page+1)


def Characters(page):
    #for now just fetch both pages
    characters = []

    characters += GetCharacters(1)
    characters += GetCharacters(2)

    characters.sort(key=lambda tup: tup[0])

    for character in characters:
        title = character[0]
        img   = character[1]
        link  = character[2]
        desc  = character[3]
        AddCharacter(title, img, link, desc)


def GetCharacters(page):
    url   = URL + 'characters/' + str(page)
    html  = GetHTML(url)
    match = re.compile('title="(.+?)">.+?<img src="(.+?)".+?<span class="title">.+?<a href="(.+?)".+?">(.+?)</a>').findall(html)

    characters = []

    for desc, img, link, title in match:
        characters.append([title, img, link, desc])

    return characters


def Character(_url, page):
    page = int(page)

    url, next = GetUrlAndNext(_url, page)

    html  = GetHTML(url)
    match = re.compile('title="(.+?)">.+?<img src="(.+?)".+?<a class="title" href="(.+?)".+?">(.+?)</a>').findall(html)

    for desc, img, link, title in match:
        AddCartoon(title, img, link, desc)

    if next in html:
        AddMore(CHARACTER, _url, page+1)
        

def AddCartoon(title, img, link, desc):
    link = link.replace('/cartoon/', '/video/')
    link = link.replace('.html', '.mp4')

    infoLabels = {'title':title, 'plot':desc}

    menu = []
    menu.append(('Download', 'XBMC.RunPlugin(%s?mode=%d&title=%s&url=%s)' % (sys.argv[0], DOWNLOAD, urllib.quote_plus(title), urllib.quote_plus(link))))

    AddDir(title, CARTOON, url=link, image=img, isFolder=False, infoLabels=infoLabels, contextMenu=menu)


def AddCharacter(title, img, link, desc):

    if desc.startswith('Watch Free'):
        desc = desc.split('. ', 1)[1]
    infoLabels = {'title':title, 'plot':desc}

    AddDir(title, CHARACTER, url=link, image=img, isFolder=True, infoLabels=infoLabels)


def AddStudio(title, img, link, desc):
    AddDir(title, STUDIO, url=link, image=img, isFolder=True)  
    

def AddSection(name, image, mode, isFolder=True):
    AddDir(name, mode, image=os.path.join(ARTWORK, image+'.png'), isFolder=isFolder)


def AddMore(mode, url, page, keyword = None):
    AddDir('More...', mode, url, image=os.path.join(ARTWORK, 'more.png'), page=page, keyword=keyword)


def AddDir(name, mode, url='', image=None, isFolder=True, page=1, keyword=None, infoLabels=None, contextMenu=None):
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


def GetSearch():
    kb = xbmc.Keyboard('', TITLE, False)
    kb.doModal()
    if not kb.isConfirmed():
        return None

    return kb.getText()


def Download(title, url):
    file = DownloadPath(title, url)
    if not file:
        return
    
    try:
        import download
        download.download(url, file)
    except Exception, e:
        print TITLE + ' Error during downloading of ' + url
        print str(e)

    
   
def FileSystemSafe(text):
    text = re.sub('[:\\/*?\<>|"]+', '', text)
    return text.strip()


def DownloadPath(title, url):    		
    downloadFolder = ADDON.getSetting('DOWNLOAD_FOLDER')

    if ADDON.getSetting('ASK_FOLDER') == 'true':
        dialog = xbmcgui.Dialog()
	downloadFolder = dialog.browse(3, 'Download to folder...', 'files', '', False, False, downloadFolder)
	if downloadFolder == '' :
	    return None

    if downloadFolder is '':
        d = xbmcgui.Dialog()
	d.ok('Super Cartoons', 'You have not set the default download folder.\nPlease update the addon settings and try again.','','')
	ADDON.openSettings() 
	downloadFolder = ADDON.getSetting('DOWNLOAD_FOLDER')

    if downloadFolder == '' and ADDON.getSetting('ASK_FOLDER') == 'true':
        dialog = xbmcgui.Dialog()
	downloadFolder = dialog.browse(3, 'Download to folder...', 'files', '', False, False, downloadFolder)	

    if downloadFolder == '' :
        return None

    downloadFolder = xbmc.translatePath(downloadFolder)

    filename = title
   
    if ADDON.getSetting('ASK_FILENAME') == 'true':        
        kb = xbmc.Keyboard(filename, 'Download Cartoon as...' )
	kb.doModal()
	if kb.isConfirmed():
	    filename = kb.getText()
	else:
	    return None

    ext      = url.rsplit('.', 1)[-1]
    filename = FileSystemSafe(filename) + '.' + ext

    if not os.path.exists(downloadFolder):
        os.mkdir(downloadFolder)

    return os.path.join(downloadFolder, filename)
    

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


if mode == RECENT:
    MostRecent()

elif mode == POPULAR:
    MostPopular()

elif mode == ALL:
    page = urllib.unquote_plus(params['page'])
    All(page)

elif mode == RANDOM:
    Random()

elif mode == KIDSTIME:
    KidsTime()

elif mode == CHARACTERS:
    page = urllib.unquote_plus(params['page'])
    Characters(page)

elif mode == CHARACTER:
    page = urllib.unquote_plus(params['page'])
    url  = urllib.unquote_plus(params['url'])
    Character(url, page)

elif mode == STUDIOS:
    page = urllib.unquote_plus(params['page'])
    Studios(page)

elif mode == STUDIO:
    page = urllib.unquote_plus(params['page'])
    url  = urllib.unquote_plus(params['url'])
    Studio(url, page)

elif mode == CARTOON:
    url   = urllib.unquote_plus(params['url'])
    title = urllib.unquote_plus(params['title'])
    image = urllib.unquote_plus(params['image'])
    PlayCartoon(title, image, url)

elif mode == SEARCH:
    page    = 1
    keyword = ''
    try:
        page    = urllib.unquote_plus(params['page'])
        keyword = urllib.unquote_plus(params['keyword'])
    except:
        pass
    Search(page, keyword)


elif mode == DOWNLOAD:
    url   = urllib.unquote_plus(params['url'])
    title = urllib.unquote_plus(params['title'])
    Download(title, url)

else:
    Main()

        
try:
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
except:
    pass
