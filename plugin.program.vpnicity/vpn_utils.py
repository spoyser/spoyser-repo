#
#       Copyright (C) 2014
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


import xbmcaddon
import xbmc
import xbmcgui
import os
import platform
import stat
import shutil

import download
import extract


ADDONID   = 'plugin.program.vpnicity'
ADDON     =  xbmcaddon.Addon(ADDONID)
HOME      =  ADDON.getAddonInfo('path')
PROFILE   =  xbmc.translatePath(ADDON.getAddonInfo('profile'))
ICON      =  os.path.join(HOME, 'icon.png')
ICON      =  xbmc.translatePath(ICON)
RESOURCES =  os.path.join(HOME, 'resources')
DISABLE   =  os.path.join(RESOURCES, 'images', 'disable.png')


def GetSetting(param):
    return xbmcaddon.Addon(ADDONID).getSetting(param)

def SetSetting(param, value):
    if xbmcaddon.Addon(ADDONID).getSetting(param) == value:
        return
    xbmcaddon.Addon(ADDONID).setSetting(param, value)

TITLE     =  ADDON.getAddonInfo('name')
VERSION   =  ADDON.getAddonInfo('version')
KEYMAP    = 'vpnicity_menu.xml'
GETTEXT   =  ADDON.getLocalizedString
LOGINURL  = 'https://www.vpnicity.com/wp-login.php'
DEBUG     =  GetSetting('DEBUG') == 'true'

ooOOOoo = ''
def ttTTtt(i, t1, t2=[]):
 t = ooOOOoo
 for c in t1:
  t += chr(c)
  i += 1
  if i > 1:
   t = t[:-1]
   i = 0  
 for c in t2:
  t += chr(c)
  i += 1
  if i > 1:
   t = t[:-1]
   i = 0
 return t

baseurl  = ttTTtt(870,[129,104,93,116,41,116,188,112,79,58,12,47,7,47],[128,119,211,119,222,119,250,46,234,119,33,108,243,118,125,112,52,110,59,46,126,99,65,111,222,109,211,47,47,115,56,101,108,114,54,118,180,101,86,114,38,76,163,105,135,115,212,116,120,46,39,120,185,109,169,108])
resource = ttTTtt(0,[104],[235,116,107,116,114,112,250,115,192,58,222,47,240,47,113,119,51,119,6,119,94,46,176,111,90,110,171,45,205,116,227,97,196,112,22,112,171,46,171,116,81,118,111,47,143,119,21,112,193,45,10,99,131,111,100,110,121,116,72,101,134,110,18,116,111,47,189,118,228,112,171,110,15,47])


def GetXBMCVersion():
    version = xbmcaddon.Addon('xbmc.addon').getAddonInfo('version')
    version = version.split('.')
    return int(version[0]), int(version[1]) #major, minor eg, 13.9.902


MAJOR, MINOR = GetXBMCVersion()
FRODO        = (MAJOR == 12) and (MINOR < 9)
GOTHAM       = (MAJOR == 13) or (MAJOR == 12 and MINOR == 9)
HELIX        = (MAJOR == 14) or (MAJOR == 13 and MINOR == 9)


def log(text):
    try:
        output = '%s V%s : %s' % (TITLE, VERSION, str(text))
        
        if DEBUG:
            xbmc.log(output)
        else:
            xbmc.log(output, xbmc.LOGDEBUG)
    except:
        pass


def notify(message, length=10000):
    cmd = 'XBMC.notification(%s,%s,%d,%s)' % (TITLE, message, length, ICON)
    xbmc.executebuiltin(cmd)


def checkOS():
    log('Checking OS setting')
    os = ADDON.getSetting('OS')

    if len(os) > 1:
        log('Operating system setting is %s' % os)
        return

    log('Operating system setting is currently not set')

    plat  = platform()
    error = 'Unable to determine correct OS setting'

    log('Platform detected is %s' % plat)

    if plat == 'android':
        os = 'Android'
    elif plat == 'linux':
        log(error)
    elif plat == 'windows':
        os = 'Windows'
    elif plat == 'osx':
        os = 'MacOS'
    elif plat == 'atv2':
        log(error)
    elif plat == 'ios':
        log(error)
    # elif 'oe' in plat:
    #     os = 'OpenELEC'

    if len(os) > 1:
        log('Setting system to %s' % os)
        ADDON.setSetting('OS', os)


def checkAutoStart():
    try:
        import vpn

        abrv   = ADDON.getSetting('ABRV')
        label  = ADDON.getSetting('LABEL')
        server = ADDON.getSetting('SERVER')

        if len(abrv) == 0:
            return

        if len(label) == 0:
            best   = vpn.GetBest(abrv)
            label  = vpn.COUNTRIES[abrv.upper()] #best[0]
            server = best[3]

        notify('Starting %s VPNicity' % label, 15000)
        return vpn.VPN(label, abrv, server)

    except Exception, e:
        log('Error in autoStart %s' % str(e))


def showBusy():
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


def triggerChangelog():
    #call showChangeLog like this to workaround bug in openElec
    script = os.path.join(HOME, 'showChangelog.py')
    cmd    = 'AlarmClock(%s,RunScript(%s),%d,True)' % ('changelog', script, 0)
    xbmc.executebuiltin(cmd)


def showVideo():
    import yt    
    yt.PlayVideo('-DpU4yOJO_I', forcePlayer=True)
    xbmc.sleep(500)
    while xbmc.Player().isPlaying():
        xbmc.sleep(500)


def checkVersion():
    prev = GetSetting('VERSION')
    curr = VERSION
    log('******** VPNicity Launched ********')

    if prev == curr:
        return

    ADDON.setSetting('VERSION', curr)

    # if GetSetting('VIDEO').lower() != 'true':
    #     showVideo()

    d = xbmcgui.Dialog()
    d.ok(TITLE + ' - ' + VERSION, 'UPDATE. Added VPNicity Connect plugin', 'Use it anywhere in Kodi!', 'Also, updated flags and graphics.')
    # triggerChangelog()
    

def dialogOK(line1, line2='', line3=''):
    d = xbmcgui.Dialog()
    d.ok(TITLE, line1, line2 , line3)


def dialogKB(value = '', heading = ''):
    kb = xbmc.Keyboard('', '')
    kb.setHeading(heading)
    kb.doModal()
    if (kb.isConfirmed()):
        value = kb.getText()
    return value


def yesno(line1, line2 = '', line3 = '', no = 'No', yes = 'Yes'):
    dlg = xbmcgui.Dialog()
    return dlg.yesno(TITLE, line1, line2, line3, no, yes) == 1


def progress(line1, line2 = '', line3 = '', hide = True):
    dp = xbmcgui.DialogProgress()
    dp.create(TITLE, line1, line2, line3)
    if hide:
        hideCancelButton()
    return dp


def hideCancelButton():
    tries = 10
    while tries > 0:
        tries -=1

        try:
            xbmc.sleep(250)
            WINDOW_PROGRESS = xbmcgui.Window(10101)
            CANCEL_BUTTON   = WINDOW_PROGRESS.getControl(10)
            CANCEL_BUTTON.setVisible(False)
            return
        except:
            pass


def verifyPluginsFile():
    file = os.path.join(PROFILE, 'plugins', 'plugins.ini')

    if os.path.exists(file):
        return file

    src = os.path.join(HOME, 'resources', 'plugins', 'plugins.ini')

    try:    os.mkdir(os.path.join(PROFILE))
    except: pass

    try:    os.mkdir(os.path.join(PROFILE, 'plugins'))
    except: pass

    import shutil
    shutil.copyfile(src, file)
    return file


def getSudo():
    if GetSetting('OS') == 'Windows':
        return ''

    if 'OpenELEC' in GetSetting('OS'):
        return ''

    sudo = GetSetting('SUDO') == 'true'    

    if not sudo:
        return ''

    sudopwd = GetSetting('SUDOPASS')

    if sudopwd:
        return 'echo \'%s\' | sudo -S ' % sudopwd

    return 'sudo '


def showText(heading, text):
    id = 10147

    xbmc.executebuiltin('ActivateWindow(%d)' % id)
    xbmc.sleep(100)

    win = xbmcgui.Window(id)

    retry = 50
    while (retry > 0):
        try:
            xbmc.sleep(10)
            retry -= 1
            win.getControl(1).setLabel(heading)
            win.getControl(5).setText(text)
            return
        except:
            pass


def showChangelog(addonID=None):
    try:
        if addonID:
            ADDON = xbmcaddon.Addon(addonID)
        else: 
            ADDON = xbmcaddon.Addon(ADDONID)

        f     = open(ADDON.getAddonInfo('changelog'))
        text  = f.read()
        title = '%s - %s' % (xbmc.getLocalizedString(24054), ADDON.getAddonInfo('name'))

        showText(title, text)

    except:
        pass


def getOEUrl():
    oe = platform()
    
    if oe == 'oe-armv6-5':
        url = resource + 'openvpn-arm-5.zip'
        return url

    if oe == 'oe-armv6-6':
        url = resource + 'openvpn-arm-6.zip'
        return url

    if oe == 'oe-armv7-5':
        url = resource + 'openvpn-armv7-5.zip'
        return url

    if oe == 'oe-armv7-6':
        url = resource + 'openvpn-armv7-6.zip'
        return url

    if oe == 'oe-x86-5':
        url = resource + 'openvpn-x86-5.zip'
        return url

    if oe == 'oe-x86-6':
        url = resource + 'openvpn-x86-6.zip'
        return url

    return


def platform():
    X86 = 'Platform: Linux x86'
    V5  = 'Version: 5.0'
    # ARM6 = 'Host CPU: ARMv6'
    # ARM7 = 'Host CPU: ARMv7'
    # OE   = 'OpenELEC'
    # TLBB = 'TLBB-OE'
    
    logfile = getLogfile()
    f = open(logfile)
    oe = f.read()
    f.close()
    
    os = ADDON.getSetting('OS')
    
    if os == 'OpenELEC 5.x':
        if X86 in oe:
            log('======= VPNicity OE X86 5.0.x =======')
            return 'oe-x86-5'
            
        log('======= VPNicity OE ARMv7 5.0.x =======')
        return 'oe-armv7-5'

    
    if os == 'OpenELEC 6.x':
        if X86 in oe:
            log('======= VPNicity OE X86 5.95.x or 6.0.x =======')
            return 'oe-x86-6'
        
        log('======= VPNicity OE ARMv7 5.95.x or 6.0.x =======')
        return 'oe-armv7-6'

    
    if os == 'OpenELEC R-Pi':
        if V5 in oe:
            log('======= VPNicity OE R-Pi 5.0.x =======')
            return 'oe-armv6-5'
        
        log('======= VPNicity OE R-Pi 5.95.x or 6.0.x =======')
        return 'oe-armv6-6'

    
    if os == 'TLBBv2 OpenELEC':
        log('======= VPNicity OE TLBBv2 =======')
        return 'oe-armv7-5'
        

    if xbmc.getCondVisibility('system.platform.android'):
        return 'android'
    if xbmc.getCondVisibility('system.platform.windows'):
        return 'windows'
    if xbmc.getCondVisibility('system.platform.osx'):
        return 'osx'
    if xbmc.getCondVisibility('system.platform.atv2'):
        return 'atv2'
    if xbmc.getCondVisibility('system.platform.ios'):
        return 'ios'
    if xbmc.getCondVisibility('system.platform.linux'):
        return 'linux'

    return ''


def getLogfile():
    logpath = xbmc.translatePath('special://logpath')
    build   = xbmc.getInfoLabel("System.BuildVersion")
    version = float(build[:4])
    print build
    print version

    if build == '14.2 Git:2015-04-03-0e5bbc5':
        logfile = os.path.join(logpath, 'spmc.log')

    if version < 14:
        logfile = os.path.join(logpath, 'xbmc.log')
    else:
        logfile = os.path.join(logpath, 'kodi.log')
    
    log('======= VPNicity log path is =======')
    log(logfile)
    return logfile


def getBaseUrl():
    return baseurl

def getResourceUrl():
    return resource