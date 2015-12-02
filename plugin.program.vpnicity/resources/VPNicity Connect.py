
#       Copyright (C) 2015-
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


ADDONID = 'plugin.program.vpnicity'

def add(params):
    if xbmc.getCondVisibility('System.HasAddon(%s)' % ADDONID) <> 1:
        return None

    try:
        if ADDONID in params['path']:
            return None

        return 'VPNicity Connect'
    except Exception, e:
        pass

    return None


def process(option, params):
    import sys
    addon = xbmcaddon.Addon(ADDONID)
    path  = addon.getAddonInfo('path')
    sys.path.insert(0, path)

    import vpn
    import browser
    country = browser.getCountry('plugin.program.vpnicity', vpn.GetCountries())
    vpn.BestVPN(country)