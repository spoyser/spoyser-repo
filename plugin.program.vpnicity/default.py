
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
import vpn_utils as utils
import vpn


ADDON    = utils.ADDON
HOME     = utils.HOME
VERSION  = utils.VERSION
TITLE    = utils.TITLE
GETTEXT  = utils.GETTEXT
PROFILE  = utils.PROFILE

IMAGES   =  os.path.join(HOME, 'resources', 'images')
ICON     =  os.path.join(HOME, 'icon.png')
FANART   =  os.path.join(HOME, 'fanart.jpg')

HASABRV  = len(ADDON.getSetting('ABRV')) > 0

ENABLEAUTO  = 'Autostart %s VPNicity'
DISABLEAUTO = 'Clear autostart'


_SETTINGS  = 100
_KILL      = 200
_SEPARATOR = 300
_COUNTRY   = 400
_VPN       = 500
_AUTO      = 600
_CLEARAUTO = 700


def Main():
    import message
    message.check()
    utils.checkVersion()
    CheckPlugin()
    vpn.CheckUsername()
    
    if not vpn.validToRun():
        utils.log('Login Error')
        return

    # utils.checkOS()

    addDir('-- Configure %s' % TITLE,   _SETTINGS,  isFolder=False)

    current = xbmcgui.Window(10000).getProperty('VPNICITY_LABEL')

    if len(current) > 0:
        abrv      = xbmcgui.Window(10000).getProperty('VPNICITY_ABRV')
        thumbnail = utils.DISABLE #'os.path.join(IMAGES, abrv.lower()+'.png')
        addDir('-- Disable %s %s' % (current, TITLE), _KILL, thumbnail=thumbnail, isFolder=False)

    mode     = _COUNTRY
    isFolder = True

    if ADDON.getSetting('AUTO') == 'true':
        mode     = _VPN
        isFolder = False

    countries = vpn.GetCountries()

    CreateFile('-Remove-')

    for country in countries:
        label = country[0]
        menu  = []
        menu.append((ENABLEAUTO % label, 'XBMC.RunPlugin(%s?mode=%d&abrv=%s)' % (sys.argv[0], _AUTO, urllib.quote_plus(country[2]))))
        thumbnail = os.path.join(IMAGES, country[2].lower()+'.png')
        addDir(label, mode, abrv=country[1], thumbnail=thumbnail, isFolder=isFolder, menu=menu)

        try:    CreateFile(country[0], country[1])
        except: pass


def CheckPlugin():
    if ADDON.getSetting('SFPLUGIN') == 'false':
        if utils.yesno('Would you like to install the ', 'VPNicity Connect plug-in?', 'Access VPNicity anywhere in Kodi!'):
            xbmc.executebuiltin('XBMC.RunScript(special://home/addons/plugin.program.vpnicity/installSF.py)')
        else: pass


def CreateFile(label,abrv=''):
    folder   = os.path.join(PROFILE, 'countries')
    filename = os.path.join(folder,  label)

    if not os.path.exists(folder):
        os.makedirs(folder)

    if os.path.exists(filename):
        return

    file = open(filename, 'w')
    file.write(abrv)
    file.close()


def clearAuto():
    setAuto(abrv='', label='', server='')


def setAuto(abrv, label='', server=''):
    ADDON.setSetting('ABRV',   abrv)
    ADDON.setSetting('LABEL',  label)
    ADDON.setSetting('SERVER', server)


def connect(label, abrv, server):
    return vpn.VPN(label, abrv, server)


def Country(name, abrv):
    cities = vpn.GetCities(abrv)

    for city in cities:
        label = '%s (%d)' % (city[0], city[2])
        abrv   = city[1]
        server = city[3]
        menu   = []
        menu.append((ENABLEAUTO % label, 'XBMC.RunPlugin(%s?mode=%d&abrv=%s&label=%s&server=%s)' % (sys.argv[0], _AUTO, urllib.quote_plus(abrv), urllib.quote_plus(label), urllib.quote_plus(server))))
        addDir(label, _VPN, abrv=abrv, thumbnail=city[1], server=server, isFolder=False, menu=menu)

    
def addDir(label, mode, abrv='', thumbnail='', server='', isFolder=True, menu=None):
    #if thumbnail=''
    #    thumbnail = ICON

    u  = sys.argv[0] 
    u += '?mode='     + str(mode)
    u += '&label='    + urllib.quote_plus(label)
    u += '&abrv='     + urllib.quote_plus(abrv)
    u += '&server='   + urllib.quote_plus(server)

    liz = xbmcgui.ListItem(label, iconImage=thumbnail, thumbnailImage=thumbnail)

    if not menu:
        menu = []

    if HASABRV:
        menu.append((DISABLEAUTO, 'XBMC.RunPlugin(%s?mode=%d)' % (sys.argv[0], _CLEARAUTO)))

    if len(menu) > 0:
        liz.addContextMenuItems(menu, replaceItems=False)

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


elif mode == _AUTO:
    try:    abrv = urllib.unquote_plus(params['abrv'])
    except: abrv = ''

    try:    label = urllib.unquote_plus(params['label'])
    except: label = ''

    try:    server = urllib.unquote_plus(params['server'])
    except: server = ''

    setAuto(abrv, label, server)
    doRefresh = True


elif mode == _CLEARAUTO:
    clearAuto()
    doRefresh = True


elif mode == _SEPARATOR:
    pass


else:
    cacheToDisc = False
    Main()


if doRefresh:
    refresh()


xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=cacheToDisc)