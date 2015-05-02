
#
#      Copyright (C) 2014 Sean Poyser
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
import shutil


ADDONID = 'plugin.video.watchcartoononline'
ADDON   = xbmcaddon.Addon(ADDONID)
PROFILE = ADDON.getAddonInfo('profile')
CACHE   = xbmc.translatePath(os.path.join(PROFILE, 'cache'))


try:
    shutil.rmtree(CACHE)

    d = xbmcgui.Dialog()
    d.ok('Watch Cartoon Online', '', 'Cache successfully cleared')

except:
    
    d = xbmcgui.Dialog()
    d.ok('Watch Cartoon Online', '', 'Cache already clear')
