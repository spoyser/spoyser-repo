
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
import time
import re
import subprocess
import urllib

import kill

import utils

ADDONID  = utils.ADDONID
ADDON    = utils.ADDON
HOME     = utils.HOME
PROFILE  = utils.PROFILE
TITLE    = utils.TITLE
VERSION  = utils.VERSION

RESPONSE =  os.path.join(PROFILE, 'openvpn.log')
IMAGES   =  os.path.join(HOME, 'resources', 'images')
ICON     =  os.path.join(HOME, 'icon.png')
FANART   =  os.path.join(HOME, 'fanart.jpg')
URL      =  'http://www.wlvpn.com/serverList.xml'

REGEX = 'server name="(.+?)" capacity="(.+?)" city="(.+?)" country="(.+?)" icon="(.+?)" ip="(.+?)" status="(.+?)" visible="(.+?)"'

COUNTRIES = {'AU':'Australia', 'BE':'Belguim', 'BR':'Brazil', 'DK':'Denmark', 'DE':'Germany', 'ES':'Spain', 'FR':'France', 'HU':'Hungary',  'JP':'Japan', 'KR':'South Korea', 'NL':'Netherlands', 'PL':'Poland', 'SE':'Sweden', 'SG':'Singapore', 'UK':'United Kingdom', 'US':'United  States'}


import cache
cache.SetDir(os.path.join(PROFILE, 'cache'))

_SETTINGS  = 100
_KILL      = 200
_SEPARATOR = 300
_COUNTRY   = 400
_VPN       = 500

class MyVPN():
    def __init__(self, items):
        self.server   = items[0]
        self.capacity = int(items[1])
        self.city     = items[2]
        self.abrv     = items[3]
        self.icon     = os.path.join(IMAGES, self.abrv.lower()+'.png') # items[4]
        self.ip       = items[5]
        self.status   = int(items[6])
        self.visible  = items[7] == '1'
        self.country  = self.abrv
        if COUNTRIES.has_key(self.country):
                self.country = COUNTRIES[self.country]
        self.isOkay = self.status == 1 and self.visible
            

def ShowSettings():
    ADDON.openSettings()


def ShowBusy():
    busy = None
    try:
        import xbmcgui
        busy = xbmcgui.WindowXMLDialog('DialogBusy.xml', '')
        busy.show()

        try:    busy.getControl(10).setVisible(False)
        except: pass
    except:
        busy = None

    return busy



def CheckVersion():
    prev = ADDON.getSetting('VERSION')
    curr = VERSION

    if prev == curr:
        return

    ADDON.setSetting('VERSION', curr)

    if prev == '0.0.0':
        utils.dialogOK('Welcome to Datho-Digital VPN')


def CheckUsername():
    user = ADDON.getSetting('USER')
    pwd  = ADDON.getSetting('PASS')

    if user != '' and pwd != '':
        return True

    utils.dialogOK('Please enter your username and password')
    ShowSettings()    
    return False


def Main():   
    CheckVersion()
    CheckUsername()

    addDir('Configure VPN', _SETTINGS,  isFolder=False)
    addDir('Disable VPN',   _KILL,      isFolder=False)
    addDir(' ',             _SEPARATOR, isFolder=False)

    html  = cache.GetURL(URL, maxSecs = 60*15)
    items = re.compile(REGEX).findall(html)

    names     = []
    countries = []
    for item in items:
        vpn = MyVPN(item)
        if vpn.country not in names:
            names.append(vpn.country)
            countries.append([vpn.country, vpn.abrv, vpn.icon])

    countries.sort()
    for country in countries:
        addDir(country[0], _COUNTRY, abrv=country[1], thumbnail=country[2])


def Country(name, abrv):
    html  = cache.GetURL(URL, maxSecs = 60*15)
    items = re.compile(REGEX).findall(html)

    cities = []
    for item in items:
        vpn = MyVPN(item)        
        if vpn.abrv == abrv:
             vpn = MyVPN(item)
             if vpn.isOkay:
                 cities.append([vpn.city, vpn.icon, vpn.capacity, vpn.ip])

    cities.sort()
    for city in cities:
        label = '%s (%d)' % (city[0], city[2])
        addDir(label, _VPN, thumbnail=city[1], server=city[3], isFolder=False)


def Run(cmdline, timeout=0):
    print "COMMAND - %s" % cmdline

    ret = 'Error: Process failed to start'

    if timeout > 0:
        path = RESPONSE

        shell = True

        si = None
        if os.name == 'nt':
            shell = False
            si = subprocess.STARTUPINFO
            si.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess._subprocess.SW_HIDE

        f  = open(path, mode='w')
        ps = subprocess.Popen(cmdline, shell=shell, stdout=f, startupinfo=si)

        xbmc.sleep(5000)

        while timeout > 0:
            xbmc.sleep(1000)
            timeout -= 1

            f1  = open(path, mode='r')
            ret = f1.read()
            f1.close()

            if IsEnabled(ret) or IsDisabled(ret):
                timeout = 0

        f.close()

    else:
        ps  = subprocess.Popen(cmdline, shell=False, stdout=subprocess.PIPE)
        ret = ps.stdout.read()
        ps.stdout.close()

    #try:
    #    print "RESULT - %s" % str(ret)
    #except:
    #    pass

    return ret


def KillVPN(): 
    kill.KillVPN()
        

def OpenVPN(config):
    import path
    exe = path.getPath(ADDON.getSetting('OS'))

    if not exe:
        return None

    try:    timeout  = int(ADDON.getSetting('TIMEOUT'))
    except: timeout  = 99999

    cmdline  =  utils.getSudo()
    cmdline += '"' + exe + '"'
    cmdline += ' '
    cmdline += '"' + config + '"'
    cmdline  = cmdline.replace('\\', '/')


    return Run(cmdline, timeout)



def IsEnabled(response):
    if 'Initialization Sequence Completed' in response:
        return True

    return False


def IsDisabled(response):
    if 'process exiting' in response:
        return True
    return False


def VPN(label, abrv, server):
    busy = ShowBusy()

    authPath = os.path.join(PROFILE, 'temp')
    cfgPath  = os.path.join(PROFILE, 'cfg.opvn')

    KillVPN()

    WriteAuthentication(authPath)
    WriteConfiguration(server, cfgPath, authPath)

    response = OpenVPN(cfgPath)

    if busy:
        busy.close()

    if response:
        label = label.rsplit(' (', 1)[0]
        if IsEnabled(response):
            utils.dialogOK('%s VPN now enabled' % label)
        else:
            KillVPN()
            utils.dialogOK('%s VPN failed to start' % label, 'Please check your settings', 'and try again')        

    #DeleteFile(authPath)
    #DeleteFile(cfgPath)
    #DeleteFile(RESPONSE)


def DeleteFile(path):
    tries = 10
    while os.path.exists(path) and tries > 0: 
        try: 
            tries -= 1
            os.remove(path) 
            break 
        except: 
            xbmc.sleep(500)


def WriteAuthentication(path):
    CheckUsername()

    user = ADDON.getSetting('USER')
    pwd  = ADDON.getSetting('PASS')

    if user == '' and pwd == '':
        return

    f = open(path, mode='w')

    f.write(user)
    f.write('\r\n')
    f.write(pwd)
    f.write('\r\n')
    f.close()


def WriteConfiguration(server, dest, authPath):
    root    = os.path.join(HOME, 'resources', 'configs')
    config  = os.path.join(root, 'cfg.opvn')
    cert    = os.path.join(root, 'vpn.crt')
    port    = ADDON.getSetting('PORT')

    file    = open(config, mode='r')
    content = file.read()
    file.close()

    authPath = authPath.replace('\\', '/')
    cert     = cert.replace('\\', '/')

    content = content.replace('#SERVER#',               server)
    content = content.replace('#PORT#',                 port)
    content = content.replace('#CERTIFICATE#',    '"' + cert     + '"')
    content = content.replace('#AUTHENTICATION#', '"' + authPath + '"')

    file = open(dest, mode='w')
    file.write(content)
    file.close()

    
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
mode     = -1

try:    mode = int(params['mode'])
except: pass


if mode == _COUNTRY:
    label = urllib.unquote_plus(params['label'])
    abrv  = urllib.unquote_plus(params['abrv'])

    Country(label, abrv)

elif mode == _VPN:
    label  = urllib.unquote_plus(params['label'])
    abrv   = urllib.unquote_plus(params['abrv'])
    server = urllib.unquote_plus(params['server'])

    VPN(label, abrv, server)

elif mode == _SETTINGS:
    ShowSettings()

elif mode == _KILL:
    KillVPN()
    utils.dialogOK('VPN now disabled')


elif mode == _SEPARATOR:
    pass

else:
    Main()

    
xbmcplugin.endOfDirectory(int(sys.argv[1]))