# Copyright (C) 2013 
# Sean Poyser (seanpoyser@gmail.com)
#

import xbmc
import xbmcgui
import xbmcaddon

import urllib
import re

RESUME      = 800
RESUMEALL   = 900

def clean(text):
    text = text.replace('&#8211;', '-')
    text = text.replace('&#8217;', '\'')
    text = text.replace('&#8220;', '"')
    text = text.replace('&#8221;', '"')
    text = text.replace('&#39;',   '\'')
    text = text.replace('<b>',     '')
    text = text.replace('</b>',    '')
    return text


class Player(xbmc.Player):
    
    def __init__(self, *args, **kwargs):
        xbmc.Player.__init__(self)
        self.item        = []
        self.addonID     = ''
        self.chapter     = 0
        self.currChapter = 0
        self.time        = 0
        self.currTime    = 0
        self.loop        = False


    def playAll(self, url, html, name, author, image, addonID): 
        self.addonID = addonID
        self.item    = [url, str(RESUMEALL), name, author, image]

        try:
            self.chapter = int(xbmcaddon.Addon(self.addonID).getSetting('RESUME_CHAPTER'))
            self.time    = int(xbmcaddon.Addon(self.addonID).getSetting('RESUME_TIME'))
        except Exception, e:
            pass        

        match = re.compile('new Playlist\((.+?)]').findall(html)
        match = re.compile('name:"(.+?)".+?mp3:"(.+?)"}').findall(match[0])

        pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        pl.clear()    

        count = -1

        for chapter, url in match:
            count += 1
            if count < self.chapter:
                continue

            if 'Chapter' in chapter:
                chapter = 'Chapter' + chapter.split('Chapter')[1]
            chapter = clean(chapter)

            liz = xbmcgui.ListItem(name, iconImage = image, thumbnailImage = image)
            liz.setInfo('music', {'Title': name + ' - ' + chapter})
            liz.setProperty('mimetype', 'audio/mpeg')
            liz.setProperty('IsPlayable', 'true')
            pl.add(url, liz)

        self.playItem(pl)


    def playChapter(self, url, name, chapter, image, addonID): 
        self.addonID = addonID
        self.item    = [url, str(RESUME), name, chapter, image]

        try:
            self.chapter = int(xbmcaddon.Addon(self.addonID).getSetting('RESUME_CHAPTER'))
            self.time    = int(xbmcaddon.Addon(self.addonID).getSetting('RESUME_TIME'))
        except:
            pass

        chapter = chapter.replace(' [I](resume)[/I]', '')
       
        liz = xbmcgui.ListItem(name, iconImage = image, thumbnailImage = image)
        liz.setInfo('music', {'Title': name + ' - ' + chapter})
        liz.setProperty('mimetype', 'audio/mpeg')
        liz.setProperty('IsPlayable', 'true')

        pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        pl.clear()    
        pl.add(url, liz)

        self.playItem(pl)


    def playItem(self, item):                            
        try:
            self.play(item) 
            if self.time > 0:
                self.seekTime(self.time)
            self.loop = self.isPlaying()
                            
            while self.loop:
                try:
                    xbmc.sleep(1000) 
                    time = self.getTime()
                    self.currTime = int(time - 5)

                except:
                    pass

        except Exception, e:
            print str(e)


    def updateResume(self):
        item   = self.item
        resume = item[0] + urllib.quote_plus('||' + item[1] + '||' + item[2] + '||' + item[3] + '||' + item[4])
        xbmcaddon.Addon(self.addonID).setSetting('RESUME_INFO',    resume)
        xbmcaddon.Addon(self.addonID).setSetting('RESUME_CHAPTER', str(self.getChapter()))
        xbmcaddon.Addon(self.addonID).setSetting('RESUME_TIME',    str(self.currTime))


    def clearResume(self):
        xbmcaddon.Addon(self.addonID).setSetting('RESUME_INFO',    '')
        xbmcaddon.Addon(self.addonID).setSetting('RESUME_CHAPTER', '0')
        xbmcaddon.Addon(self.addonID).setSetting('RESUME_TIME',    '0')


    def getChapter(self):
        return self.chapter + self.currChapter

   
    def onPlayBackStarted(self):
        self.currChapter = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
        #print "***********B A F************"
        print "onPlayBackStarted(self):"
        self.updateResume()


    def onPlayBackPaused(self):
        #print "***********B A F************"
        #print "onPlayBackPause(self):"
        self.updateResume()


    def onPlayBackResumed(self):
        pass
        #print "***********B A F************"
        #print "onPlayBackResumed(self):"


    def onPlayBackEnded(self):
        #print "***********B A F************"
        #print "onPlayBackEnded(self):"
        #print xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
        #print len(xbmc.PlayList(xbmc.PLAYLIST_MUSIC))
        posn = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
        if posn < 0:
            self.loop = False
        else:
            self.loop = posn < len(xbmc.PlayList(xbmc.PLAYLIST_MUSIC))
        self.clearResume()


    def onPlayBackStopped(self):     
        #print "***********B A F************"
        #print "onPlayBackStopped(self):"
        #print xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
        #print len(xbmc.PlayList(xbmc.PLAYLIST_MUSIC))
        self.loop = False
        self.updateResume()


    def onPlayBackSeek(self, time, seekOffset):
        pass
        #print "***********B A F************"
        #print "onPlayBackSeek(self, time, seekOffset):"
        #print time
        #print seekOffset


    def onPlayBackSeekChapter(self, chapter):
        pass
        #print "***********B A F************"
        #print "onPlayBackSeek(self, chapter):"
        #print chapter


    def onPlayBackSpeedChanged(self, speed):
        pass
        #print "***********B A F************"
        #print "onPlayBackSeek(self, speed):"
        #print speed


    def onQueueNextItem(self):
        pass
        #print "***********B A F************"
        #print "onQueueNextItem(self):"