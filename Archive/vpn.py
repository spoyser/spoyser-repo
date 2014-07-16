
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

import utils
import os
import re
import time
import subprocess
import xbmc
import xbmcgui

import kill

PROFILE  = utils.PROFILE

REGEX = 'server name="(.+?)" capacity="(.+?)" city="(.+?)" country="(.+?)" icon="(.+?)" ip="(.+?)" status="(.+?)" visible="(.+?)"'

COUNTRIES = {'AU':'Australia', 'AT':'Austria', 'BE':'Belguim', 'BR':'Brazil', 'DK':'Denmark', 'DE':'Germany', 'ES':'Spain', 'FR':'France', 'HU':'Hungary',  'JP':'Japan', 'KR':'South Korea', 'NL':'Netherlands', 'PL':'Poland', 'SG':'Singapore', 'CH':'Switzerland', 'SE':'Sweden', 'UK':'United Kingdom', 'US':'United States'}

URL      = 'http://www.wlvpn.com/serverList.xml'
ADDON    = utils.ADDON
HOME     = utils.HOME
PROFILE  = utils.PROFILE
RESPONSE = os.path.join(PROFILE, 'openvpn.log')

import quicknet

class MyVPN():
    def __init__(self, items):
        self.server   = items[0]
        self.capacity = int(items[1])
        self.city     = items[2]
        self.abrv     = items[3]
        self.icon     = self.abrv.lower()
        self.ip       = items[5]
        self.status   = int(items[6])
        self.visible  = items[7] == '1'
        self.country  = self.abrv
        if COUNTRIES.has_key(self.country):
                self.country = COUNTRIES[self.country]
        self.isOkay = self.status == 1 and self.visible


def GetCountries():
    html  = quicknet.getURL(URL, maxSec=60*15)
    items = re.compile(REGEX).findall(html)

    names     = []
    countries = []
    for item in items:
        vpn = MyVPN(item)
        if vpn.isOkay and vpn.country not in names:
            names.append(vpn.country)
            countries.append([vpn.country, vpn.abrv, vpn.icon])

    countries.sort()
    return countries


def GetBest(abrv):
    cities  = GetCities(abrv)
    nCities = len(cities)

    if nCities < 1:
        return None

    best = cities[0]

    for city in cities:
        if best[2] > city[2]:
            best = city

    return best

    
def GetCities(abrv):
    html  = quicknet.getURL(URL, maxSec=60*15)
    items = re.compile(REGEX).findall(html)

    cities = []
    for item in items:
        vpn = MyVPN(item)        
        if vpn.abrv == abrv:
             vpn = MyVPN(item)
             if vpn.isOkay:
                 cities.append([vpn.city, vpn.icon, vpn.capacity, vpn.ip])

    cities.sort()
    return cities


def KillVPN(silent=False): 
    kill.KillVPN()
    if not silent:
        utils.dialogOK('%s now disabled' % utils.TITLE)    


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


def BestVPN(abrv):
    if len(abrv) == 0:
        return

    best = GetBest(abrv)

    return VPN(COUNTRIES[best[1].upper()], best[1], best[3])


def VPN(label, abrv, server):
    authPath = os.path.join(PROFILE, 'temp')
    cfgPath  = os.path.join(PROFILE, 'cfg.opvn')

    KillVPN(silent=True)

    WriteAuthentication(authPath)
    WriteConfiguration(server, cfgPath, authPath)

    busy = utils.showBusy()

    response = OpenVPN(cfgPath)

    if busy:
        busy.close()

    if response:
        label = label.rsplit(' (', 1)[0]
        if IsEnabled(response):
            utils.dialogOK('%s %s now enabled' % (label, utils.TITLE))
            xbmcgui.Window(10000).setProperty('VPNICITY_RUNNING', 'True')
        else:
            KillVPN()
            utils.dialogOK('%s %s failed to start' % (label, utils.TITLE), 'Please check your settings', 'and try again')        

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


def CheckUsername():
    user = ADDON.getSetting('USER')
    pwd  = ADDON.getSetting('PASS')

    if user != '' and pwd != '':
        return True

    utils.dialogOK('Please enter your username and password')
    ShowSettings()    
    return False


def ShowSettings():
    ADDON.openSettings()