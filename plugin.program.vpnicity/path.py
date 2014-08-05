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

import xbmc
import utils
import os


#-------------------------------------------------------------


def getWindows(silent):
    path = 'C:/Program Files/OpenVPN/bin/openvpn.exe'
    if check(path):
        return path

    path = 'C:/Program Files (x86)/OpenVPN/bin/openvpn.exe'
    if check(path):
        return path

    return error(silent)


#-------------------------------------------------------------


def getLinux(silent):
    path = '/usr/sbin/openvpn'
    if check(path):
        return path

    return error(silent)


#-------------------------------------------------------------


def getMacOS(silent):
    path = xbmc.translatePath('special://profile/addon_data/plugin.program.vpnicity/macos/sbin/openvpn')
    if check(path):
        return path

    return error(silent)


#-------------------------------------------------------------


def getAndroid(silent):
    path = '/data/app/de.blinkt.openvpn-1.apk'
    if check(path):
        return path

    return error(silent)


#-------------------------------------------------------------


def getOpenElec(silent):
    path = '/usr/sbin/openvpn'
    if check(path):
        return path

    return error(silent)


#-------------------------------------------------------------


def getIOS(silent):
    # path = '/private/var/stash/_.tN42y0/Applications/GuizmOVPN.app/openvpn'
    path = '/usr/sbin/openvpn'
    if check(path):
        return path

    return error(silent)


#-------------------------------------------------------------


def getRaspBMC(silent):
    path = '/usr/sbin/openvpn'
    if check(path):
        return path

    return error(silent)


#-------------------------------------------------------------


def getPath(os, silent=False):
    if os == 'Windows':
        return getWindows(silent)

    if os == 'Linux':
        return getLinux(silent)

    if os == 'MacOS':
        return getMacOS(silent)

    if os == 'Android':
        return getAndroid(silent)

    if os == 'OpenELEC':
        return getOpenElec(silent)

    if os == 'iOS':
        return getIOS(silent)

    if os == 'RaspBMC':
        return getRaspBMC(silent)

    return error(silent)



def error(silent):
    if silent:
        return None

    import utils
    import xbmcgui
    xbmcgui.Dialog().ok(utils.TITLE + ' - ' + utils.VERSION, 'Could not find a VPN application.', 'Please check your settings and try again.')
    return None


def check(path):
    path = path.replace('/', os.sep)
    return os.path.exists(path)