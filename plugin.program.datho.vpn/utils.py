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

ADDONID  = 'plugin.program.datho.vpn'
ADDON    =  xbmcaddon.Addon(ADDONID)
HOME     =  ADDON.getAddonInfo('path')
PROFILE  =  xbmc.translatePath(ADDON.getAddonInfo('profile'))
EXTERNAL = 0
TITLE    = 'Datho-Digital VPN'
VERSION  = '1.0.0'



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