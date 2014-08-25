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
import xbmcgui
import utils


class MyMonitor(xbmc.Monitor):
    def __init__(self):
        xbmc.Monitor.__init__(self)
        self.auto = utils.ADDON.getSetting('AUTO') == 'true'


    def onSettingsChanged(self):
        auto = utils.ADDON.getSetting('AUTO') == 'true'

        if self.auto == auto:
            return

        self.auto = auto


monitor = MyMonitor()

xbmcgui.Window(10000).setProperty('script.image.music.slideshow.running', 'false')

while (not xbmc.abortRequested):
    check = xbmcgui.Window(10000).getProperty('script.image.music.slideshow.running') == 'false'

    if check and monitor.auto: 
        if xbmc.Player().isPlayingAudio():
            #xbmc.executebuiltin('ActivateWindow(10025)')
            xbmc.executebuiltin('RunScript(%s)' % utils.ADDONID)

    xbmc.sleep(1000)

del monitor