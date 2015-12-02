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
import xbmcgui
import os

import vpn_utils as utils

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

    if utils.GetSetting('CONTEXT')  == 'true':
        src = os.path.join(HOME, 'resources', 'keymaps', KEYMAP)
        dst = os.path.join(xbmc.translatePath('special://userdata/keymaps'), KEYMAP)

        try:
            import shutil
            shutil.copy(src, dst)
        except:
            pass

    xbmc.sleep(1000)
    xbmc.executebuiltin('Action(reloadkeymaps)')  


def getCountry(index):
    country  = ''
    abrv     = ''
    try:
        country = utils.GetSetting('VPN_%d' % index)

        if country.lower() == '-remove-' or country == '': 
            utils.SetSetting('ADDON_%d' % index, '')
            utils.SetSetting('VPN_%d'   % index, '')
            return '', ''

        filename = os.path.join(PROFILE, 'countries', country)
    
        file = open(filename, 'r')
        abrv = file.read()
        file.close()
    except:
        pass

    return country.strip(), abrv.strip().lower()


class MyMonitor(xbmc.Monitor):
    def __init__(self):
        xbmc.Monitor.__init__(self)
        self.addon   = ''
        self.context = utils.GetSetting('CONTEXT')  == 'true'
        self.context = not self.context
        self.onSettingsChanged()


    def populateAddons(self):
        self.addons = []
        for i in range(10):
            addon = utils.GetSetting('ADDON_%d' % i)
            if len(addon) > 0:
                country, abrv = getCountry(i)               
                self.addons.append([addon, country, abrv])
        
        index = 0

        for addon in self.addons:
            if len(addon[0]) > 0 and len(addon[1]) > 0:
                utils.SetSetting('ADDON_%d' % index, addon[0])
                utils.SetSetting('VPN_%d'   % index, addon[1])
                index += 1

        for i in range(index, 10):
            utils.SetSetting('ADDON_%d' % i, '')
            utils.SetSetting('VPN_%d'   % i, '')


    def onSettingsChanged(self):
        self.populateAddons()

        context = utils.GetSetting('CONTEXT')  == 'true'

        if self.context != context:
            self.context = context    
            UpdateKeymap()


    def checkForAddon(self):
        #print "____________________________________________"
        #print xbmc.getInfoLabel('Container.FolderPath')
        #print xbmc.getInfoLabel('ListItem.FolderPath')
        #print xbmc.getInfoLabel('ListItem.Label')
        #print xbmc.getInfoLabel('ListItem.FilenameAndPath')
        #print xbmc.getInfoLabel('ListItem.Label')
        #print xbmc.getInfoLabel('ListItem.Thumb')    
        #print xbmc.getInfoLabel('ListItem.Property(IsPlayable)').lower() == 'true'
        #print xbmc.getInfoLabel('ListItem.Property(Fanart_Image)')
        ##print xbmc.getCondVisibility('ListItem.IsFolder') == 1
        #print "ADDON"
        #print xbmcaddon.Addon().getAddonInfo('path')
        #print "____________________________________________"

        folder = ''

        try:    folder = xbmc.getInfoLabel('Container.FolderPath').replace('plugin://', '')
        except: pass

        if len(folder) == 0:
            return

        if (len(self.addon) > 0) and folder.startswith(self.addon):
            return

        currentVPN = xbmcgui.Window(10000).getProperty('VPNICITY_ABRV').lower()

        if len(self.addon) > 0 and len(currentVPN) > 0:
            if not xbmc.Player().isPlayingVideo():
                import kill
                import ipcheck
                kill.KillVPN()
                ipcheck.Network()
                

        self.addon = ''

        for addon in self.addons:
            plugin = addon[0]
            if folder.startswith(plugin):
                VPN        = addon[2]
                self.addon = plugin
                if VPN != currentVPN:
                    import vpn
                    utils.checkOS()
                    vpn.AutoSelect(self.addon, [VPN])
                return


def checkInstalled():
    import path
    exists = path.getPath(utils.GetSetting('OS'), silent=True)
    if not exists:
        if utils.yesno('Do you want to install the VPN application now'):
            import install
            install.install(silent=False)


# -------------------------------------------------------------------

utils.checkAutoStart()
utils.checkOS()
       
monitor = MyMonitor()


while (not xbmc.abortRequested):
    xbmc.sleep(1000)
    if xbmc.getCondVisibility('System.HasAddon(%s)' % utils.ADDONID) == 0: #i.e. not enabled/installed
        DeleteKeymap()
        xbmc.sleep(1000)
        xbmc.executebuiltin('Action(reloadkeymaps)')  
    else:
        monitor.checkForAddon()


if xbmc.getCondVisibility('System.HasAddon(%s)' % utils.ADDONID) == 0:
    DeleteKeymap()


del monitor


try:
    import kill

    kill.KillVPN()
except:
    pass