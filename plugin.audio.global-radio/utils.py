
#       Copyright (C) 2017-
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

import xbmc
import xbmcaddon

import os

import sfile


ADDONID = 'plugin.audio.global-radio'
ADDON   = xbmcaddon.Addon(ADDONID)
HOME    = ADDON.getAddonInfo('path')
PROFILE = ADDON.getAddonInfo('profile')
TITLE   = ADDON.getAddonInfo('name')
VERSION = ADDON.getAddonInfo('version')
ICON    = os.path.join(HOME, 'icon.png')
FANART  = os.path.join(HOME, 'fanart.jpg')
IMAGES  = os.path.join(HOME, 'resources', 'images')
GETTEXT = ADDON.getLocalizedString


PLAYABLE = xbmc.getSupportedMedia('video') + '|' + xbmc.getSupportedMedia('music')
PLAYABLE = PLAYABLE.replace('|.zip', '')
PLAYABLE = PLAYABLE.split('|')


def GetRandomUserAgent():
    import random
    agents = []  
    agents.append('Mozilla/5.0 (Android; Mobile; rv:%d.0) Gecko/%d.0 Firefox/%d.0')

    agent = random.choice(agents) % (random.randint(10, 40), random.randint(10, 40), random.randint(10, 40))

    return agent


def GetHTML(url, useCache=True, agent=None):
    import cache

    if not agent:
        agent = GetRandomUserAgent()

    if useCache:
        html = cache.getURL(url, maxSec=1800, agent=agent)
    else:
        html = cache.getURLNoCache(url, agent=agent)

    html  = html.replace('\n', '')
    return html



def DialogOK(line1, line2='', line3=''):
    import xbmcgui
    d = xbmcgui.Dialog()
    d.ok(TITLE, line1, line2 , line3)


def DialogYesNo(line1, line2='', line3='', noLabel=None, yesLabel=None):
    import xbmcgui
    d = xbmcgui.Dialog()
    if noLabel == None or yesLabel == None:
        return d.yesno(TITLE + ' - ' + VERSION, line1, line2 , line3) == True
    else:
        return d.yesno(TITLE + ' - ' + VERSION, line1, line2 , line3, noLabel, yesLabel) == True


def Log(text):
    log(text)


DEBUG = False
def log(text):
    try:
        output = '%s V%s : %s' % (TITLE, VERSION, str(text))
        
        if DEBUG:
            xbmc.log(output)
        else:
            xbmc.log(output, xbmc.LOGDEBUG)
    except:
        pass



def isFilePlayable(path):
    try:    return ('.' + sfile.getextension(path) in PLAYABLE)
    except: return False



def isPlayable(path):
    if not sfile.exists(path):
        return False

    if sfile.isfile(path):
        playable = isFilePlayable(path)
        return playable
         
    current, dirs, files = sfile.walk(path)

    for file in files:
        if isPlayable(os.path.join(current, file)):
            return True

    for dir in dirs:        
        if isPlayable(os.path.join(current, dir)):
            return True

    return False



def parseFolder(folder, subfolders=True):
    items = []

    current, dirs, files = sfile.walk(folder)

    if subfolders:
        for dir in dirs:        
            path = os.path.join(current, dir)
            if isPlayable(path):
                items.append([dir, path, False])

    for file in files:
        path = os.path.join(current, file)
        if isPlayable(path):
            items.append([file.split('.')[0], path, True])

    return items


def parseDate(dateString): #2017-02-10T19:00:00
    import datetime
    if type(dateString) in [str, unicode]:          
        dt = dateString.split('T')
        d  = dt[0]
        t  = dt[1]
        ds = d.split('-')
        ts = t.split(':')
        return datetime.datetime(int(ds[0]), int(ds[1]) ,int(ds[2]), int(ts[0]), int(ts[1]), int(ts[2]))

    if type(dateString) in [int]:          
        return datetime.datetime.fromtimestamp(float(dateString))
          
    return dateString

