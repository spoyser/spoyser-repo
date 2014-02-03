
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

ADDONID = 'plugin.video.kidstube'
ADDON   = xbmcaddon.Addon(ADDONID)
GETTEXT = ADDON.getLocalizedString
HOME    = ADDON.getAddonInfo('path')
ARTWORK = os.path.join(HOME, 'resources', 'artwork')
ICON    = os.path.join(HOME, 'icon.png')
TITLE   = 'Kids-Tube.nl'
VERSION = '1.0.2'
URL     = 'http://www.kids-tube.nl/'


PARSE  = 100
VIDEO  = 300
MENU   = 400
EXTRA  = 500
AZ     = 600
SEARCH = 700

YOUTUBE = 100
VIMEO   = 200


def CheckVersion():
    prev = ADDON.getSetting('VERSION')
    curr = VERSION

    if prev == curr:
        return

    ADDON.setSetting('VERSION', curr)

    if prev == '0.0.0':
        d = xbmcgui.Dialog()
        d.ok(TITLE + ' - ' + VERSION, GETTEXT(30001), GETTEXT(30002), '')
        return


def Clean(text):
    text = text.replace('&#038;',  '&')
    text = text.replace('&#8211;', '-')
    text = text.replace('&#8217;', '\'')
    text = text.replace('&#8220;', '"')
    text = text.replace('&#8221;', '"')
    text = text.replace('&#39;',   '\'')
    text = text.replace('<b>',     '')
    text = text.replace('</b>',    '')
    text = text.replace('&amp;',   '&')
    text = text.replace('\ufeff', '')
    return text


def FixURL(url):
    url = url.replace('\\\'', '%27')
    return url


def GetHTML(url, useCache = True):
    if useCache:
        html, cached = geturllib.GetURL(url, 86400)
    else:
        html = geturllib.GetURLNoCache(url)

    html  = html.replace('\n', '')
    return html


def Main():
    CheckVersion()
    
    AddSection('Nieuwste kinderfilmpjes', '', PARSE,  URL)
    AddSection('Babyfilmpjes',            '', MENU,   'Babyfilmpjes')
    AddSection('Peuterfilmpjes',          '', MENU,   'Peuterfilmpjes')
    AddSection('Kleuterfilmpjes',         '', MENU,   'Kleuterfilmpjes')
    AddSection('Sinterklaas',             '', MENU,   'Sinterklaas')
    AddSection('Kinderliedjes',           '', MENU,   'Kinderliedjes')
    AddSection('Kinderfilms',             '', MENU,   'Kinderfilms')
    AddSection('Voor vaders en moeders',  '', MENU,   'Voor vaders en moeders')
    AddSection('Extra',                   '', EXTRA,  'Extra')
    AddSection('A-Z',                     '', AZ,     'A-Z')
    AddSection(GETTEXT(30006),            '', SEARCH)


def DoMenu(url):
    html = GetHTML(URL)
    html = re.compile(url+'(.+?)<span class="um-anchoremulator" ><span class="wpmega-link-title">').search(html).group(1)

    match = re.compile('<a title=".+?" href="(.+?)">.+? class="wpmega-link-title">(.+?)</span></a>').findall(html)

    if len(match) == 0:
        match = re.compile('<a href="(.+?)"><span class="wpmega-link-title">(.+?)</span></a>').findall(html)
        
    for url, title in match:
        AddDir(title, PARSE, url=url)


def DoExtra(url):
    html = GetHTML(URL)
    html = re.compile(url+'(.+?)</ul>').search(html).group(1)

    match = re.compile('<a title=".+?" href="(.+?)">.+? class="wpmega-link-title">(.+?)</span></a>').findall(html)

    if len(match) == 0:
        match = re.compile('<a href="(.+?)"><span class="wpmega-link-title">(.+?)</span></a>').findall(html)        

    for url, title in match:
        AddDir(title, PARSE, url=url)


def DoAZ():
    url = URL + 'kinderfilmpjes-overzicht/'
    html = GetHTML(url)
    
    html = html.split('>A<', 1)[1]
    html = html.replace('<div><p><a', '<div><a')

    match = re.compile('<a title=".+?" href="(.+?)">(.+?)</a>').findall(html)

    items = []

    for url, title in match:
        title = title.replace('<br />', '')
        items.append([title, url])

    items.sort()
    for item in items:
        AddDir(item[0], PARSE, url=item[1])


def GetKeyword():
    kb = xbmc.Keyboard('', TITLE, False)
    kb.doModal()
    if not kb.isConfirmed():
        return None

    text = kb.getText()

    if text == '':
        return None

    return text

def DoSearch():
    keyword = GetKeyword()
    if not keyword:
        return

    url = URL + '?s=%s' % urllib.quote_plus(keyword)
    ParseURL(url)
    

def ParseURL(_url):
    search = None
    if '/?s=' in _url:
        search = '/?s=' + _url.split('/?s=', 1)[1]

    original = GetHTML(_url)
    html     = original.replace('post-ratings', 'ratings')

    html = html.replace('img src', 'img dummy src')
    html = html.split('<div id="post-')[1:]

    for item in html:
        match = re.compile('<a href="(.+?)".+?<img .+? src="(.+?)" alt=".+?".+?title=".+?">(.+?)</a>').findall(item)
        try:
            url    = match[0][0]
            image  = match[0][1].replace('&amp;w=216', '&w=648').replace('&amp;h=120', '&h=360')
            image  = image.split('"', 1)[0]
            title  = match[0][2]
            #fanart = image.replace('&w=648', '&w=846').replace('&h=360', '&h=480')
            AddVideo(title, url, image)
        except:
            pass

    try:    nav = re.compile('<div class=\'wp-pagenavi\'>(.+?)</div>').search(original).group(1)
    except: return

    match = re.compile('href="http://www.kids-tube.nl/page/(.+?)/').findall(nav)

    pages = [1]
    root  = None
    for page in match:
        if int(page) not in pages:
            pages.append(int(page))

    pages.sort()

    root = 'http://www.kids-tube.nl/'

    for page in range(1, pages[-1]+1):
        url = root
        if page > 1:
            url += 'page/%d' % page
            if search:
                url += search 

        if search and search not in url: 
            url += search 
            url = url.replace('//?s', '/?s')  
    
        if url != _url:
            AddMore(page, url)


def PlayID(mode, id):
    url = None

    if mode == YOUTUBE:
        return PlayYouTube(id) 
        #url = 'plugin://plugin.video.youtube/?path=root/video&action=play_video&videoid=%s' % id

    if mode == VIMEO:
        if CheckVimeo(): 
            url = 'plugin://plugin.video.vimeo/?action=play_video&videoid=%s' % id

    if url:
        xbmc.Player().play(url) 


def PlayYouTube(id):
    from simpleYT import yt
    return yt.PlayVideo(id)


def CheckVimeo():
    try:
        vimeo = 'plugin.video.vimeo'
        path  = xbmcaddon.Addon(vimeo).getAddonInfo('path')
        if os.path.exists(path):
            return True
    except Exception, e:
        pass

    d = xbmcgui.Dialog()
    d.ok(TITLE + ' - ' + VERSION, GETTEXT(30003), GETTEXT(30004) ,GETTEXT(30005))

    return False
    

def PlayURL(url):
    html = GetHTML(url)

    try:    return PlayID(YOUTUBE, re.compile('www.youtube-nocookie.com/v/(.+?)"').search(html).group(1))
    except: pass

    try:    return PlayID(YOUTUBE, re.compile('www.youtube.com/embed/(.+?)\?').search(html).group(1))
    except: pass

    html = html.replace('https', 'http')

    try:    return PlayID(VIMEO, re.compile('content="http://www.vimeo.+?clip_id=(.+?)"').search(html).group(1))
    except: pass

    print "KIDS-TUBE.NL - ERROR OBTAINING VIDEO ID FROM %s " % url
 
   
def AddSection(name, image, mode, url=''):
    if image == '':
        image = ICON
    else:
        image=os.path.join(ARTWORK, image+'.png')
    AddDir(name, mode, url, image, isFolder=True)


def AddVideo(name, url, image, fanart=None):
    AddDir(name, VIDEO, url=url, image=image, isFolder=False, fanart=fanart)


def AddMore(page, url):
    page = int(page)
    name = GETTEXT(30007) % page
    AddDir(name, PARSE, url=url)


def AddDir(name, mode, url='', image=None, isFolder=True, fanart=None, infoLabels=None, contextMenu=None):
    if not image:
        image = ICON

    name = Clean(name)

    u  = sys.argv[0] 
    u += '?mode='  + str(mode)
    u += '&title=' + urllib.quote_plus(name)
    u += '&image=' + urllib.quote_plus(image)

    if url != '':     
        u += '&url='   + urllib.quote_plus(url) 

    liz = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)

    if fanart:
        liz.setProperty("Fanart_Image", fanart)

    if contextMenu:
        liz.addContextMenuItems(contextMenu)

    if infoLabels:
        liz.setInfo(type="Video", infoLabels=infoLabels)

    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=isFolder)
 

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
url    = None

try:    mode = int(urllib.unquote_plus(params['mode']))
except: pass

try:    url = urllib.unquote_plus(params['url'])
except: pass


if mode == PARSE:    
    ParseURL(url)

elif mode == MENU:
    DoMenu(url)

elif mode == EXTRA:
    DoExtra(url)

elif mode == AZ:    
    DoAZ()

elif mode == SEARCH:    
    DoSearch()

elif mode == VIDEO:    
    PlayURL(url)

else:
    Main()

        
try:
    #xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
except:
    pass
