
#       Copyright (C) 2013-2014
#       Sean Poyser (seanpoyser@gmail.com) and Richard Dean (write2dixie@gmail.com)
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

import vpn_utils as utils
import os
import re
import time
import datetime
import subprocess
import xbmc
import xbmcgui
import requests

import ipcheck
import kill

PROFILE  = utils.PROFILE
ADDONID  = utils.ADDONID

REGEX = 'server name="(.+?)" capacity="(.+?)" city="(.+?)" country="(.+?)" icon="(.+?)" ip="(.+?)" status="(.+?)" visible="(.+?)"'

COUNTRIES = {'AU':'Australia', 'AT':'Austria', 'BE':'Belguim', 'BR':'Brazil', 'CA':'Canada', 'DK':'Denmark', 'DE':'Germany', 'ES':'Spain', 'FR':'France', 'GB':'Great Britain', 'HU':'Hungary',  'JP':'Japan', 'KR':'South Korea', 'NL':'Netherlands', 'PL':'Poland', 'SG':'Singapore', 'CH':'Switzerland', 'SE':'Sweden', 'UK':'United Kingdom', 'US':'United States'}

URL      = utils.getBaseUrl()
ADDON    = utils.ADDON
HOME     = utils.HOME
PROFILE  = utils.PROFILE
TITLE    = utils.TITLE
RESPONSE = os.path.join(PROFILE, 'openvpn.log')

import quicknet


LOGINURL = utils.LOGINURL
USERNAME = utils.GetSetting('USER')
PASSWORD = utils.GetSetting('PASS')


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


def AutoSelectCity(plugin, country):
    cities = GetCities(country)

    theList = []

    for city in cities:
        label = '%s (%d)' % (city[0], city[2])
        theList.append([label, label, city[1]])

    import browser
    choice = browser.getCountry(ADDONID, theList)

    for city in cities:
        label = '%s (%d)' % (city[0], city[2])
        if choice == label:
            return VPN(city[0], city[1], city[3])


def AutoSelect(plugin, countries):
    if len(countries) == 0:
        return

    import random

    country = None
    if countries[0] == '*':
        try:    country = random.choice(COUNTRIES.keys())       #Python 2.x
        except: country = random.choice(list(COUNTRIES.keys())) #Python 3.x
    else:
        country = random.choice(countries).strip()

    if not country:
        return

    if country.upper().endswith('+CITY'):
        return AutoSelectCity(plugin, country.upper().split('+CITY', 1)[0])

    best = GetBest(country)

    VPN(COUNTRIES[best[1].upper()], best[1], best[3])


def GetBest(abrv):
    cities  = GetCities(abrv)
    nCities = len(cities)

    if nCities < 1:
        return None

    import random
    return random.choice(cities)

    #best = cities[0]

    #for city in cities:
    #    if best[2] > city[2]:
    #        best = city

    #return best

    
def GetCities(abrv):
    abrv  = abrv.upper()
    html  = quicknet.getURL(URL, maxSec=60*15)
    items = re.compile(REGEX).findall(html)

    cities = []
    for item in items:
        vpn = MyVPN(item)        
        if vpn.abrv == abrv:
             if vpn.isOkay:
                 cities.append([vpn.city, vpn.icon, vpn.capacity, vpn.ip])

    cities.sort()
    return cities


def KillVPN(silent=False): 
    kill.KillVPN()
    if not silent:
        message = '%s now disabled' % TITLE
        xbmcgui.Window(10000).setProperty('VPNICITY_CONNECTED', 'False')
        utils.notify(message)
        ipcheck.Network()


def Run(cmdline, timeout=0):
    if utils.platform() == "android":
        return RunAndroid(cmdline, timeout)

    utils.log('COMMAND - %s' % cmdline)

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
    #    utils.log('RESULT - %s' % str(ret))
    #except:
    #    pass

    return ret


def RunAndroid(cmdline, timeout=0):
    xbmc.executebuiltin(cmdline)

    path = RESPONSE

    xbmc.sleep(5000)

    while timeout > 0:
        xbmc.sleep(1000)
        timeout -= 1

        f   = open(path, mode='r')
        ret = f.readlines()
        f.close()

        #remove first 2 lines as these may be from previous run
        if len(ret) > 0:
            ret = ret[1:]
        if len(ret) > 0:
            ret = ret[1:]

        ret = ''.join(ret)

        if IsEnabled(ret) or IsDisabled(ret):
            timeout = 0

    return ret


def OpenVPN(config):
    import path
    exe = path.getPath(ADDON.getSetting('OS'))

    if not exe:
        return None

    try:    timeout  = int(ADDON.getSetting('TIMEOUT'))
    except: timeout  = 99999

    if utils.platform() == "android":
        cmdline = "StartAndroidActivity(%s,%s,%s,%s)" % \
                    ( "com.vpnicity.openvpn.control", "com.vpnicity.openvpn.control.CONNECT", "com.vpnicity.openvpn.control.PROFILE_PATH", "file://" + config )
    else :
        cmdline  =  utils.getSudo()
        cmdline += '"' + exe + '"'
        cmdline += ' '
        cmdline += '"' + config + '"'
        cmdline  = cmdline.replace('\\', '/')

    return Run(cmdline, timeout)


def IsEnabled(response):
    if ('Initialization Sequence Completed' in response) or ('SUCCESS' in response):
        return True

    return False


def IsDisabled(response):
    if ('process exiting' in response) or ('AUTH_FAILED' in response):
        return True
    return False


def BestVPN(abrv):
    if len(abrv) == 0:
        return

    best = GetBest(abrv)

    return VPN(COUNTRIES[best[1].upper()], best[1], best[3])


def VPN(label, abrv, server):
    if not validToRun():
        utils.log('Login Error via Context Menu')
        return False

    authPath = os.path.join(PROFILE, 'temp')
    cfgPath  = os.path.join(PROFILE, 'cfg.ovpn')

    KillVPN(silent=True)

    WriteAuthentication(authPath)
    WriteConfiguration(server, cfgPath, authPath)

    busy = utils.showBusy()

    response = OpenVPN(cfgPath)

    if busy:
        busy.close()

    success = True

    if response:
        label = label.rsplit(' (', 1)[0]
        if IsEnabled(response):
            # if utils.platform() == "android":
            #     xbmc.sleep(10000)
            message = '%s %s now enabled' % (label, TITLE)
            utils.notify(message)         
            xbmcgui.Window(10000).setProperty('VPNICITY_LABEL',  label)
            xbmcgui.Window(10000).setProperty('VPNICITY_ABRV',   abrv)
            xbmcgui.Window(10000).setProperty('VPNICITY_SERVER', server)
            xbmcgui.Window(10000).setProperty('VPNICITY_CONNECTED', 'True')
            ipcheck.Network()

        else:
            KillVPN(silent=True)
            if utils.platform() == "android":
                xbmc.sleep(5000)
            message = '%s %s failed to start. Please check your settings.' % (label, TITLE)
            utils.notify(message)
            ipcheck.Network() 
            success = False

    #DeleteFile(authPath)
    #DeleteFile(cfgPath)
    #DeleteFile(RESPONSE)

    return success


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
    # CheckUsername()

    user = USERNAME + '@vpnicity'
    pwd  = PASSWORD

    if user == '' and pwd == '':
        return

    f = open(path, mode='w')
    
    if utils.platform() == 'osx':
        f.write(user)
        f.write('\n')
        f.write(pwd)
        f.write('\n')
        f.close()
        
    else:
        f.write(user)
        f.write('\r\n')
        f.write(pwd)
        f.write('\r\n')
        f.close()


def WriteConfiguration(server, dest, authPath):
    root    = os.path.join(HOME, 'resources', 'configs')
    config  = os.path.join(root, 'cfg.ovpn')
    cert    = os.path.join(root, 'vpn.crt')
    port    = ADDON.getSetting('PORT')

    file    = open(config, mode='r')
    content = file.read()
    file.close()

    authPath = authPath.replace('\\', '/')
    cert     = cert.replace('\\', '/')

    content = content.replace('#SERVER#', server)
    content = content.replace('#PORT#', port)

    if utils.platform() == 'android':
        authentication = '<auth-user-pass>\r\n'               \
                       + USERNAME + '@vpnicity' + '\r\n'    \
                       + PASSWORD + '\r\n'    \
                       + '</auth-user-pass>'
                       
    else:
        authentication = 'auth-user-pass "%s"' % authPath

    content = content.replace('#AUTHENTICATION#', authentication)
    
    file = open(dest, mode='w')
    file.write(content)
    file.close()


def CheckUsername():
    utils.log('================== in CheckUsername ==================')
    user = USERNAME
    pwd  = PASSWORD

    if user != '' and pwd != '':
        return True

    dlg = utils.yesno('VPNicity requires a subscription.', '', 'Would you like to enter your account details now?')

    if dlg == 1:
        user = utils.dialogKB('', 'Enter Your VPNicity Username')
        pwd  = utils.dialogKB('', 'Enter Your VPNicity Password')
        
        ADDON.setSetting('USER', user)
        ADDON.setSetting('PASS', pwd)
        
        SetupAccount()
        
    return True
        

def SetupAccount():
    utils.checkOS()
    os = utils.GetSetting('OS')

    if os == 'MacOS':
        utils.dialogOK('It appears you are running on Mac OS.', '', 'You may need administrator access to run VPNicity.')

        sudo = utils.dialogKB('', "Enter the 'User Account' password for your computer.")

        ADDON.setSetting('SUDO', 'true')
        ADDON.setSetting('SUDOPASS', sudo)

        utils.dialogOK('We will now finish your installation.', 'Please double check your settings after we are done.', 'Thank you!')
        xbmc.executebuiltin('XBMC.RunScript(special://home/addons/plugin.program.vpnicity/install.py)')

    if 'OpenELEC' in os:
        utils.dialogOK('It appears you are running on OpenELEC.', 'We will now finish your installation.', 'Please double check your settings after we are done.')    
        xbmc.executebuiltin('XBMC.RunScript(/storage/.kodi/addons/plugin.program.vpnicity/install.py)')
        
    else:
        return
        

def ShowSettings():
    ADDON.openSettings()


def getPreviousTime():
    utils.log('================== in getPreviousTime ==================')
    time_object = utils.GetSetting('LOGIN_TIME')
    
    if time_object == '':
        time_object = '2001-01-01 00:00:00'
        
    previousTime = parseTime(time_object)
    
    return previousTime


def parseTime(when):
    if type(when) in [str, unicode]:
        dt = when.split(' ')
        d  = dt[0]
        t  = dt[1]
        ds = d.split('-')
        ts = t.split(':')
        when = datetime.datetime(int(ds[0]), int(ds[1]) ,int(ds[2]), int(ts[0]), int(ts[1]), int(ts[2].split('.')[0]))
        
    return when


def validToRun():
    utils.log('================== in validToRun ==================')
    previousTime = getPreviousTime()
    now          = datetime.datetime.today()
    delta        = now - previousTime
    nSeconds     = (delta.days * 86400) + delta.seconds
    
    if nSeconds > 35 * 60:
        if not Login():
            return False

        ADDON.setSetting('LOGIN_TIME', str(now))
        
    return True

def Login():
    utils.log('================ VPNicity Login ================')
    with requests.Session() as s:
        try:
            s.get(LOGINURL)
        except: 
            return False
        
        USER     = ADDON.getSetting('USER')
        PASS     = ADDON.getSetting('PASS')
        PAYLOAD  = { 'log' : USER, 'pwd' : PASS, 'wp-submit' : 'Log In' }
        response = 'login_error'
        code     =  0

        if USER and PASS:
            login    = s.post(LOGINURL, data=PAYLOAD)
            response = login.content
            # code     = login.status_code
            # saveCookies(s.cookies, cookiefile)
        
        if 'no-access-redirect' in response:
            error   = '301 - No Access.'
            message = 'It appears that your subscription has expired.'
            utils.log(message + ' : ' + error)
            utils.dialogOK(message, error, 'Please check your account at www.vpnicity.com')

            KillVPN(silent=True)
            
            return False
            
        areLost    = 'Are you lost' in response
        loginError = 'login_error' in response
        okay       =  (not areLost) and (not loginError)
        
        if okay:
            message = 'Logged into VPNicity'
            utils.log(message)
            utils.notify(message)
            return True
            
        try:
            error = re.compile('<div id="login_error">(.+?)<br />').search(response).groups(1)[0]
            error = error.replace('<strong>',  '')
            error = error.replace('</strong>', '')
            error = error.replace('<a href="https://www.vpnicity.com/wp-login.php?action=lostpassword">Lost your password?</a>', '')
            error = error.strip()
            print error
        except:
            error = ''
            
        message = 'There was a problem logging into VPNicity'
        
        utils.log('************ VPNicity Error ************')
        utils.log(message + ' : ' + error)
        utils.log('****************************************')
        utils.dialogOK(message, error, 'Please check your account at www.vpnicity.com')
        
        KillVPN(silent=True)
        
    return False
