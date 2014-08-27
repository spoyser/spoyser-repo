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
import xbmcaddon
import os

import utils

ADDONID =  utils.ADDONID
ADDON   =  utils.ADDON
HOME    =  utils.HOME
PROFILE =  utils.PROFILE
KEYMAP  =  utils.KEYMAP


def DeleteKeymap():
    path = os.path.join(xbmc.translatePath('special://userdata/keymaps'), KEYMAP)

    tries = 5
    while os.path.exists(path) and tries > 0:
        tries -= 1 
        try: 
            os.remove(path) 
            return
        except: 
            xbmc.sleep(500)


def UpdateKeymap():
    DeleteKeymap()

    if ADDON.getSetting('CONTEXT')  == 'true':
        src = os.path.join(HOME, 'resources', 'keymaps', KEYMAP)
        dst = os.path.join(xbmc.translatePath('special://userdata/keymaps'), KEYMAP)

        try:
            import shutil
            shutil.copy(src, dst)
        except:
            pass

    xbmc.sleep(1000)
    xbmc.executebuiltin('Action(reloadkeymaps)')  



class MyMonitor(xbmc.Monitor):
    def __init__(self):
        xbmc.Monitor.__init__(self)
        self.context = ADDON.getSetting('CONTEXT')  == 'true'
        self.context = not self.context
        self.onSettingsChanged()


    def onSettingsChanged(self):
        context = ADDON.getSetting('CONTEXT')  == 'true'

        if self.context == context:
            return

        self.context = context
        
        UpdateKeymap()


def checkInstalled():
    import path
    exists = path.getPath(utils.ADDON.getSetting('OS'), silent=True)
    if not exists:
        if utils.yesno('Do you want to install the VPN application now'):
            import install
            install.install(silent=False)


# -------------------------------------------------------------------

#checkInstalled()
       
monitor = MyMonitor()


while (not xbmc.abortRequested):
    xbmc.sleep(1000)

del monitor


try:
    import kill
    kill.KillVPN()
except:
    pass