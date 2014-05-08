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

import resolve
import common

ADDONID = 'plugin.video.watchcartoononline'
ADDON   = xbmcaddon.Addon(ADDONID)
HOME    = ADDON.getAddonInfo('path')
ARTWORK = os.path.join(HOME, 'resources', 'artwork')
ICON    = os.path.join(HOME, 'icon.png')
TITLE   = 'Watch Cartoon Online'
VERSION = '1.0.6'
URL     = 'http://www.watchcartoononline.com/'


SECTION  = 100
SERIES   = 200
EPISODE  = 300



def CheckVersion():
    prev = ADDON.getSetting('VERSION')
    curr = VERSION

    if prev == curr:
        return

    ADDON.setSetting('VERSION', curr)

    if curr == '1.0.0':
        d = xbmcgui.Dialog()
        d.ok(TITLE + ' - ' + VERSION, '', 'Welcome to Watch Cartoon Online', '')


def Main():
    CheckVersion()

    html = common.GetHTML(URL)

    match = re.compile('<li><a href="(.+?)">(.+?)</a></li>').findall(html)
    for url, name in match:
        if name == 'Contact':
            break
        if name != 'Home':
            AddSection(name, '', url)


def DoSection(url):
    mode = SERIES
    if url == 'http://www.watchcartoononline.com/movie-list':
        mode = EPISODE
    if url == 'http://www.watchcartoononline.com/ova-list':
        mode = EPISODE

    html = common.GetHTML(url)

    html = html.split('<div id="ddmcc_container">', 1)[-1]

    html = html.replace('<li><a href=""></a></li>', '')
  
    names = []

    match = re.compile('<li><a href="(.+?)">(.+?)</a></li>').findall(html)

    sorted = []

    for url, name in match:
        if ('#' not in url) and ('title="' not in url):
            if name not in names:
                names.append(name)
                if mode == SERIES:
                    #AddSeries(name, url)
                    newName = name
                    if newName.startswith('The '):
                        newName = newName.split('The ', 1)[-1]
                    sorted.append([newName, name, url])
                elif mode == EPISODE:
                    AddEpisode(name, url)

    sorted.sort()
    for item in sorted:
        AddSeries(item[1], item[2])


def DoSeries(html):#url):
    #html = common.GetHTML(url)

    title = re.compile('<title>(.+?) \| .+?').search(html).group(1)
    image = re.compile('"image_src" href="(.+?)"').search(html).group(1)

    html  = html.split('animelist', 1)[-1]
    match = re.compile('<a href=(.+?)<div class="ildate">').findall(html)

    for item in match:
        name = None
        url  = None
        try:
            match1 = re.compile('<a href="(.+?)".+?title=".+?">(.+?)</a>').findall(item)
            url    = match1[0][0]
            name   = match1[0][1]
        except:
            match1 = re.compile('"(.+?)".+?title=".+?">(.+?)</a>').findall(item)
            url    = match1[0][0]
            name  = match1[0][1]

        if name and url:
            AddEpisode(name, url, image)

    #if 'Previous Entries' in html:
    #    url = re.compile('<div class="alignleft"><a href="(.+?)".+?Previous Entries</a>').search(html).group(1)
    #    AddSeries('More...', url)


def GetLinkIndex(resolved):
    if len(resolved) < 2:
        return 0

    current = ''
    part    = 1

    hosts = []

    for item in resolved:
        resolver = item[0]

        if resolver == current:
            hosts[-1] = resolver + ' - Part %d' % part
            part     += 1
            hosts.append(resolver + ' - Part %d' % part)
        else:
            current = resolver
            part    = 1
            hosts.append(resolver)

    index = xbmcgui.Dialog().select('Please Select Video Host', hosts)
        
    return index


def PlayVideo(_url):
    #print _url
    resolved = resolve.ResolveURL(_url)

    if len(resolved) == 0:
        url = None
        msg = 'Unidentified Video Host'
    else:
        index    = GetLinkIndex(resolved)
        resolver = resolved[index][0]
        url      = resolved[index][1]
        msg      = resolved[index][2]

    if not url:
        d   = xbmcgui.Dialog()
        d.ok(TITLE + ' - ' + VERSION, '', msg, '')

        print 'WATCHCARTOONSONLINE - (%s) Failed to locate video for %s' % (msg, _url)
        return

    html  = common.GetHTML(_url)
    image = re.compile('"image_src" href="(.+?)"').search(html).group(1)
    title = re.compile('<title>(.+?)</title>').search(html).group(1).split(' |', 1)[0]
    title = common.Clean(title)

    #print title
    #print image

    liz = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)

    liz.setInfo( type="Video", infoLabels={ "Title": title} )
    liz.setProperty("IsPlayable","true")

    if int(sys.argv[1]) == -1:
        pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        pl.clear()
        pl.add(url, liz)
        xbmc.Player().play(pl)
    else:
        liz.setPath(url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
        

def AddEpisode(name, url, image=None):
    AddDir(name, EPISODE, url, image=image, isFolder=False)


def AddSeries(name, url):
    AddDir(name, SERIES, url)


def AddSection(name, image, url):
    if image == '':
        image = ICON
    else:
        image=os.path.join(ARTWORK, image+'.png')

    AddDir(name, SECTION, url, image, isFolder=True)


def AddDir(name, mode, url='', image=None, isFolder=True, page=1, keyword=None, infoLabels=None, contextMenu=None):
    name = common.Clean(name)

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
        #liz.setInfo(type="Video", infoLabels=infoLabels)
        infoLabels['title'] = name
    else:
        infoLabels = { 'title' : name }
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


#print sys.argv[2]

params = get_params()
mode   = None
url    = None


try:    mode = int(urllib.unquote_plus(params['mode']))
except: pass

try:    url  = urllib.unquote_plus(params['url'])
except: pass


if mode == SECTION:
    DoSection(url)

elif mode == SERIES:
    #DoSeries(url)

    html = common.GetHTML(url)

    while('Previous Entries' in html):
        DoSeries(html)
        url  = re.compile('<div class="alignleft"><a href="(.+?)".+?Previous Entries</a>').search(html).group(1)
        html = common.GetHTML(url)

    DoSeries(html)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)


elif mode == EPISODE:
    PlayVideo(url)

else:
    Main()

        
try:
#    #xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
except:
    pass
