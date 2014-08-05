#
#       Copyright (C) 2014
#       Sean Poyser (seanpoyser@gmail.com)
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#pr
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

import utils

ADDONID = utils.ADDONID
TITLE   = utils.TITLE


def getCountries(plugin):
    file = utils.verifyPluginsFile()

    import param    
    countries = param.getParam(plugin, file)

    if len(countries) == 0:
        return []
 
    return countries.split(',')


def doMenu(plugin=None):
    if plugin == None:
        plugin = xbmc.getInfoLabel('ListItem.FolderPath')

    #if not (plugin.startswith('plugin') or plugin.startswith('script')):
    #    xbmc.executebuiltin('XBMC.Action(ContextMenu)')
    #    return

    plugin = plugin.split('://', 1)[-1]
    plugin = plugin.split('/',   1)[0]

    if len(plugin) == 0:
        xbmc.executebuiltin('XBMC.Action(ContextMenu)')
        return

    if utils.ADDONID in plugin:
        xbmc.executebuiltin('XBMC.Action(ContextMenu)')
        return
        
    choice    = 0
    label     = xbmcgui.Window(10000).getProperty('VPNICITY_LABEL')
    vpnON     = len(label) > 0
    countries = getCountries(plugin)
    hasAuto   = len(countries) > 0

    menu = []

    if hasAuto:
        menu.append('Auto %s' % TITLE)

    menu.append('Manual %s'   % TITLE)
    menu.append('%s Settings' % TITLE)

    if vpnON:
        menu.append('Disable %s %s' % (label, TITLE))

    menu.append('Standard context menu')

    choice = xbmcgui.Dialog().select('%s' % TITLE, menu)

    if choice == None or choice < 0:
        return

    if not hasAuto:
        choice += 1

    if vpnON:
        if choice == 4:
            xbmc.executebuiltin('XBMC.Action(ContextMenu)')
            return
        if choice == 3:
            off()
            return
  
    if choice == 0:
        auto(plugin, countries)

    if choice == 1:
        manual()

    if choice == 2:
        utils.ADDON.openSettings()

    if choice == 3:
        xbmc.executebuiltin('XBMC.Action(ContextMenu)')


def auto(plugin, countries):
    import vpn
    vpn.AutoSelect(plugin, countries)


def manual():
    import vpn
    import browser
    country = browser.getCountry(ADDONID, vpn.GetCountries())
    vpn.BestVPN(country)


def off():
    import vpn
    vpn.KillVPN()

plugin = None
if len(sys.argv) > 1:
    plugin = sys.argv[1]
doMenu(plugin=plugin)
