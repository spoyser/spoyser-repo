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
import stat
import shutil

import download
import extract

ADDONID   = 'plugin.program.vpnicity'
ADDON     =  xbmcaddon.Addon(ADDONID)
HOME      =  ADDON.getAddonInfo('path')
PROFILE   =  xbmc.translatePath(ADDON.getAddonInfo('profile'))
RESOURCES =  os.path.join(HOME, 'resources')
TITLE     = 'VPNicity'
VERSION   = '1.1.0'
KEYMAP    = 'vpnicity_menu.xml'


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


def dialogOK(line1, line2='', line3=''):
    d = xbmcgui.Dialog()
    d.ok(TITLE, line1, line2 , line3)


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
    xbmc.sleep(250)
    WINDOW_PROGRESS = xbmcgui.Window(10101)
    CANCEL_BUTTON   = WINDOW_PROGRESS.getControl(10)
    CANCEL_BUTTON.setVisible(False)


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
    if ADDON.getSetting('OS') == 'Windows':
        return ''

    sudo = ADDON.getSetting('SUDO') == 'true'    

    if not sudo:
        return ''

    sudopwd = ADDON.getSetting('SUDOPASS')

    if sudopwd:
        return 'echo \'%s\' | sudo -S ' % sudopwd

    return 'sudo '


def platform():
    if xbmc.getCondVisibility('system.platform.android'):
        return 'android'
    elif xbmc.getCondVisibility('system.platform.linux'):
        return 'linux'
    elif xbmc.getCondVisibility('system.platform.windows'):
        return 'windows'
    elif xbmc.getCondVisibility('system.platform.osx'):
        return 'osx'
    elif xbmc.getCondVisibility('system.platform.atv2'):
        return 'atv2'
    elif xbmc.getCondVisibility('system.platform.ios'):
        return 'ios'

