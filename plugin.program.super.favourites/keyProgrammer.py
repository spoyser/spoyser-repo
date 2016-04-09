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
#  KeyListener class based on XBMC Keymap Editor by takoi


import xbmc
import xbmcgui
from threading import Timer

import utils

GETTEXT = utils.GETTEXT
ICON    = utils.ICON

TIMEOUT = 10

class KeyListener(xbmcgui.WindowXMLDialog):

    def __new__(cls):
        try: 
            ret = super(KeyListener, cls).__new__(cls, 'DialogProgress.xml', '')
        except:
            ret   = super(KeyListener, cls).__new__(cls, 'DialogConfirm.xml', '')
        return ret 


    def __init__(self):
        self.key     = 0
        self.timeout = TIMEOUT
        self.setTimer()


    def close(self):
        self.timer.cancel()
        xbmcgui.WindowXML.close(self)


    def onInit(self):
        try:
            self.getControl(20).setVisible(False)
            self.getControl(10).setLabel(xbmc.getLocalizedString(222))
            self.setFocus(self.getControl(10))
            self.getControl(11).setVisible(False)
            self.getControl(12).setVisible(False)
        except:
            pass


        self.onUpdate()



    def onUpdate(self):
        text  = GETTEXT(30110) + '[CR]'
        text += GETTEXT(30109) % self.timeout
        self.getControl(9).setText(text)

        #percent = 100 * (1 - float(self.timeout) / float(TIMEOUT))
        #self.getControl(20).setPercent(int(percent))


    def onAction(self, action):
        actionId = action.getId()     

        if actionId in [1, 2, 3, 4, 7, 100, 103, 107]:
            return

        if actionId in [9, 10, 92, 100]:
            return self.close()
       
        self.key = action.getButtonCode()
        self.close()


    def onClick(self, controlId):
        self.close()


    def onTimer(self):
        self.timeout -= 1
        if self.timeout < 0:
            return self.close()

        self.onUpdate()
        self.setTimer()


    def setTimer(self):
        self.timer = Timer(1, self.onTimer)
        self.timer.start()


def recordKey():
    dialog  = KeyListener()

    dialog.doModal()

    key = dialog.key

    del dialog
    return key


def main():
    if utils.isATV():
        utils.DialogOK(GETTEXT(30118), GETTEXT(30119))
        return False

    key = recordKey()
    if key < 1:
        return

    start = 'key id="%d"' % key
    end   = 'key'

    if utils.WriteKeymap(start, end):
        xbmc.sleep(1000)
        xbmc.executebuiltin('Action(reloadkeymaps)')  

    
if __name__ == '__main__':
    main()