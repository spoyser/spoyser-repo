
#       Copyright (C) 2013-2014
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
import xbmcplugin
import xbmcgui
import os
import urllib

import utils

import vpn

ADDON    = utils.ADDON
HOME     = utils.HOME
VERSION  = utils.VERSION
TITLE    = utils.TITLE

IMAGES   =  os.path.join(HOME, 'resources', 'images')
ICON     =  os.path.join(HOME, 'icon.png')
FANART   =  os.path.join(HOME, 'fanart.jpg')


_SETTINGS  = 100
_KILL      = 200
_SEPARATOR = 300
_COUNTRY   = 400
_VPN       = 500


def CheckVersion():
    prev = ADDON.getSetting('VERSION')
    curr = VERSION

    if prev == curr:
        return

    ADDON.setSetting('VERSION', curr)

    if prev == '0.0.0':
        utils.dialogOK('Welcome to %s' % TITLE, 'Added IP Country/City Checker')


def Main():   
    CheckVersion()
    vpn.CheckUsername()

    addDir('-- Configure %s' % TITLE,   _SETTINGS,  isFolder=False)

    current = xbmcgui.Window(10000).getProperty('VPNICITY_LABEL')

    if len(current) > 0:
        abrv      = xbmcgui.Window(10000).getProperty('VPNICITY_ABRV')
        thumbnail = os.path.join(IMAGES, abrv.lower()+'.png')
        addDir('-- Disable %s %s' % (current, TITLE), _KILL, thumbnail=thumbnail, isFolder=False)

    mode     = _COUNTRY
    isFolder = True

    if ADDON.getSetting('AUTO') == 'true':
        mode     = _VPN
        isFolder = False

    countries = vpn.GetCountries()
    for country in countries:
        thumbnail = os.path.join(IMAGES, country[2].lower()+'.png')
        addDir(country[0], mode, abrv=country[1], thumbnail=thumbnail, isFolder=isFolder)


def connect(label, abrv, server):
    return vpn.VPN(label, abrv, server)


def Country(name, abrv):
    cities = vpn.GetCities(abrv)

    for city in cities:
        label = '%s (%d)' % (city[0], city[2])
        addDir(label, _VPN, abrv=city[1], thumbnail=city[1], server=city[3], isFolder=False)

    
def addDir(label, mode, abrv='', thumbnail='', server='', isFolder=True):
    #if thumbnail=''
    #    thumbnail = ICON

    u  = sys.argv[0] 
    u += '?mode='     + str(mode)
    u += '&label='    + urllib.quote_plus(label)
    u += '&abrv='     + urllib.quote_plus(abrv)
    u += '&server='   + urllib.quote_plus(server)

    liz = xbmcgui.ListItem(label, iconImage=thumbnail, thumbnailImage=thumbnail)

    #liz.setProperty('Fanart_Image', FANART)

    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=isFolder)


def refresh():
    xbmc.executebuiltin('Container.Refresh')


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



params = get_params()
mode   = -1

try:    mode = int(params['mode'])
except: pass


cacheToDisc = True
doRefresh   = False
doEnd       = True


if mode == _COUNTRY:
    label = urllib.unquote_plus(params['label'])
    abrv  = urllib.unquote_plus(params['abrv'])

    Country(label, abrv)


elif mode == _VPN:
    label  = urllib.unquote_plus(params['label'])
    abrv   = urllib.unquote_plus(params['abrv'])
    server = urllib.unquote_plus(params['server'])
    
    if len(server) == 0:
        server    = vpn.GetBest(abrv)[3]
        doRefresh = True

    success = connect(label, abrv, server)


elif mode == _SETTINGS:
    utils.ADDON.openSettings()


elif mode == _KILL:
    vpn.KillVPN()    
    doRefresh = True


elif mode == _SEPARATOR:
    pass


else:
    cacheToDisc = False
    Main()


if doRefresh:
    refresh()


if doEnd:
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=cacheToDisc)