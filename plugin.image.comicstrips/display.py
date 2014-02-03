
import xbmcgui
import xbmc
import xbmcaddon
import re
import common

from threading import Timer 


ACTION_PARENT_DIR    = 9
ACTION_PREVIOUS_MENU = 10
ACTION_BACK          = 92
ACTION_X             = 13

ACTION_LEFT  = 1
ACTION_RIGHT = 2
ACTION_UP    = 3
ACTION_DOWN  = 4

CTRL_STRIP    = 5001
CTRL_PREFETCH = 5002
CTRL_PREV     = 5003
CTRL_NEXT     = 5004


ADDONID = common.ADDONID
URL     = common.URL
ADDON   = xbmcaddon.Addon(ADDONID)


class Display(xbmcgui.WindowXMLDialog):
    def __new__(cls, url, slideshow):
        return super(Display, cls).__new__(cls, 'main.xml', ADDON.getAddonInfo('path'))


    def __init__(self, url, slideshow): 
        super(Display, self).__init__()
        self.timer      = None
        self.url        = url
        self.slideshow  = slideshow
        self.transition = int(ADDON.getSetting('TRANSITION'))


    def onInit(self):
        self.Clear()

        if self.slideshow:
            url = common.GetRandomURL(self.url)
        else:
            isCurrent = ADDON.getSetting('DISPLAY') == '0'

            if isCurrent:
                url = common.GetCurrentURL(self.url)
            else:
                url = common.GetRandomURL(self.url)

        self.UpdateImage(url)


    def Clear(self):
        self.title    = ''
        self.image    = None
        self.previous = None
        self.next     = None
        self.author   = ''
        self.date     = ''

        if self.timer:
            self.timer.cancel()
            del self.timer
            self.timer = None

              
    def OnClose(self):
        self.Clear()
        self.close()


    def onAction(self, action):
        actionID = action.getId()
        buttonID = action.getButtonCode()

        if actionID in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, ACTION_BACK, ACTION_X]:
            self.OnClose()

        if self.slideshow:
            return

        if actionID in [ACTION_LEFT, ACTION_UP]:
            if self.previous:
                self.UpdateImage(URL + self.previous)

        if actionID in [ACTION_RIGHT, ACTION_DOWN]:
            if self.next:
                self.UpdateImage(URL + self.next)
            
                                 
    def onClick(self, controlId):
        if controlId == CTRL_PREV:
            self.Previous()

        if controlId == CTRL_NEXT:
            self.Next()


    def Previous(self):
        if not self.previous:
            return False

        return self.UpdateImage(URL + self.previous)        


    def Next(self):
        if not self.next:
            return False

        return self.UpdateImage(URL + self.next)


    def onTimer(self):
        if self.next:
            self.UpdateImage(URL + self.next)

        self.UpdateImage(common.GetRandomURL(self.url))


    def UpdateImage(self, url):
        self.Clear()

        html  = common.GetHTML(url)
        html  = html.replace('\n', '')
        html  = html.split('<p >')[-1]
        match = re.compile('(.+?)</p>.+?<img alt=".+?" src="(.+?)".+?<strong>(.+?)</strong>(.+?)</span>').findall(html)

        self.title  = match[0][0]
        self.image  = match[0][1]
        self.author = match[0][2]
        self.date   = match[0][3]

        if 'revious' in html:
           self.previous = re.compile('<span class="archiveText"><a href="(.+?)">&lt').search(html).groups(1)[0]

        if 'ext &gt' in html:
           self.next = re.compile('<span class="archiveText"><a href=".+?">&lt.+?<a href="(.+?)"').search(html).groups(1)[0]
        
        if self.image:
            self.setControlImage(CTRL_STRIP, self.image)

        #pre-fetch previous and next images
        if self.previous:
            self.setControlImage(CTRL_PREFETCH, self.getImage(common.GetHTML(URL + self.previous)))
        if self.next:
            self.setControlImage(CTRL_PREFETCH, self.getImage(common.GetHTML(URL + self.next)))

        self.UpdateControls()

        if self.slideshow:
            self.timer = Timer(self.transition, self.onTimer)
            self.timer.start()

        return True


    def getImage(self, html):
        img = ''
        try:
            html  = html.replace('\n', '')
            html  = html.split('<p >')[-1]
            match = re.compile('(.+?)</p>.+?<img alt=".+?" src="(.+?)".+?<strong>(.+?)</strong>(.+?)</span>').findall(html)
            img   = match[0][1]
        except:
           pass

        return img
        

    def setControlImage(self, id, image):
        if image == None:
            return

        try:    self.getControl(id).setImage(image)
        except: pass


    def UpdateControls(self):
        try:
            self.getControl(CTRL_PREV).setVisible((not self.slideshow) and (self.previous != None))
            self.getControl(CTRL_NEXT).setVisible((not self.slideshow) and (self.next     != None))            
        except Exception, e:
            pass