
#       Copyright (C) 2013-2015
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
import xbmcgui
import xbmcaddon
import os

ACTION_BACK          = 92
ACTION_PARENT_DIR    = 9
ACTION_PREVIOUS_MENU = 10

ACTION_LEFT  = 1
ACTION_RIGHT = 2
ACTION_UP    = 3
ACTION_DOWN  = 4

import vpn_utils as utils


USE_HELIX = (not utils.FRODO) and (not utils.GOTHAM)


class Browser(xbmcgui.WindowXMLDialog):

    def __new__(cls, addonID, countries):
        print xbmcaddon.Addon(addonID).getAddonInfo('path')
        if USE_HELIX:
            return super(Browser, cls).__new__(cls, 'browser-helix.xml', xbmcaddon.Addon(addonID).getAddonInfo('path'))
        else:
            return super(Browser, cls).__new__(cls, 'browser.xml', xbmcaddon.Addon(addonID).getAddonInfo('path'))

        
    def __init__(self, addonID, countries):
        super(Browser, self).__init__()
        self.countries = countries
        self.root      = os.path.join(xbmcaddon.Addon(addonID).getAddonInfo('path'), 'resources', 'images')

        
    def onInit(self):
        self.list    = self.getControl(3000)
        self.icon    = self.getControl(3002)
        self.country = ''

        label      = xbmcgui.Window(10000).getProperty('VPNICITY_LABEL')
        self.vpnON = len(label) > 0

        if self.vpnON:
            label = '[I]Disable %s %s[/I]' % (label, utils.TITLE)
            liz   = xbmcgui.ListItem(label)
            self.list.addItem(liz)

        for country in self.countries:
            title = country[0]
            liz   = xbmcgui.ListItem(title)
            self.list.addItem(liz)

        self.setFocus(self.list)

           
    def onAction(self, action):
        actionId = action.getId()

        if actionId in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, ACTION_BACK]:
            return self.close()

        self.refreshImage()


    def onClick(self, controlId):
        print '************  in browser.py country chosen, trying VPN  ************'
        if controlId != 3001:
            index = self.list.getSelectedPosition()  

            offset = 1 if self.vpnON else 0 

            if self.vpnON and index == 0:
                import threading
                threading.Timer(1, self.close).start()
                self.disable()
                return
            else:
                try:    self.country = self.countries[index-offset][1]
                except: pass

        self.close()


    def disable(self):
        try:
            import vpn
            vpn.KillVPN()
        except:
            pass


    def onFocus(self, controlId):
        self.refreshImage()


    def refreshImage(self):
        index = self.list.getSelectedPosition()

        offset = 1 if self.vpnON else 0

        if self.vpnON and index == 0:
            self.icon.setImage(utils.DISABLE)
            return

        try:    name = self.countries[index-offset][2] + '.png'
        except: return

        self.icon.setImage(os.path.join(self.root, name))


def getCountry(addonID, countries):
    dialog = Browser(addonID, countries)
    dialog.doModal()
    country = dialog.country
    del dialog
    return country