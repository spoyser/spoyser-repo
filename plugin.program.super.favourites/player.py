#
#       Copyright (C) 2014-
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


import favourite
import utils

ADDON   = utils.ADDON
ADDONID = utils.ADDONID
FRODO   = utils.FRODO


PLAYMEDIA_MODE      = utils.PLAYMEDIA_MODE
ACTIVATEWINDOW_MODE = utils.ACTIVATEWINDOW_MODE
RUNPLUGIN_MODE      = utils.RUNPLUGIN_MODE
ACTION_MODE         = utils.ACTION_MODE

PLAY_PLAYLISTS = ADDON.getSetting('PLAY_PLAYLISTS') == 'true'


def playCommand(originalCmd, contentMode=False):
    try:
        xbmc.executebuiltin('Dialog.Close(busydialog)') #Isengard fix

        cmd = favourite.tidy(originalCmd)
        
        #if a 'Super Favourite' favourite just do it
        if ADDONID in cmd:
             return xbmc.executebuiltin(cmd)

        #if in contentMode just do it
        if contentMode:
            xbmc.executebuiltin('ActivateWindow(Home)') #some items don't play nicely if launched from wrong window
            if cmd.lower().startswith('activatewindow'):
                cmd = cmd.replace('")', '",return)') #just in case return is missing                
            return xbmc.executebuiltin(cmd)

        if cmd.startswith('RunScript'):    
            #workaround bug in Frodo that can cause lock-up
            #when running a script favourite
            if FRODO:
                xbmc.executebuiltin('ActivateWindow(Home)')
    
        if isPlaylist(cmd):
            if PLAY_PLAYLISTS:
                return playPlaylist(cmd)      

        if 'ActivateWindow' in cmd:
            return activateWindowCommand(cmd) 

        if 'PlayMedia' in cmd:
            return playMedia(originalCmd)

        if cmd.lower().startswith('executebuiltin'):
            try:    
                cmd = cmd.split('"', 1)[-1]
                cmd = cmd.rsplit('")')[0]
            except:
                pass


        xbmc.executebuiltin(cmd)


    except Exception, e:
        utils.log('Error in playCommand')
        utils.log('Command: %s' % cmd)
        utils.log('Error:   %s' % str(e))    


def isPlaylist(cmd):
    if cmd.lower().replace(',return', '').endswith('.m3u")'):
        return True

    if cmd.lower().replace(',return', '').endswith('.m3u8")'):
        return True

    return False

    
def playPlaylist(cmd):
    if cmd.lower().startswith('activatewindow'):
        playlist = cmd.split(',', 1)
        playlist = playlist[-1][:-1]
        cmd      = 'PlayMedia(%s)' % playlist

    elif sfile.exists(cmd):
        #cmd = 'PlayMedia(%s)' % cmd
        playPlaylistFile(cmd)
        return

    xbmc.executebuiltin(cmd)


def playPlaylistFile(path):
    items = parsePlaylist(sfile.readlines(path))

    pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    pl.clear()        

    start = 0
        
    for i in range(start,len(items)):
        item   = items[i]
        title  = item[0]
        image  = ICON
        url    = item[1]
        
        liz = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)

        liz.setInfo(type='Video', infoLabels={'Title': title})

        pl.add(url, liz)

    xbmc.Player().play(pl)


def activateWindowCommand(cmd):
    cmds = cmd.split(',', 1)

    #special case for filemanager
    if '10003' in cmds[0] or 'filemanager' in cmds[0].lower():
        xbmc.executebuiltin(cmd)
        return   

    plugin   = None
    activate = None

    if len(cmds) == 1:
        activate = cmds[0]
    else:
        activate = cmds[0]+',return)'
        plugin   = cmds[1][:-1]

    #check if it is a different window and if so activate it
    id = str(xbmcgui.getCurrentWindowId())    

    if id not in activate:
        xbmc.executebuiltin(activate)

    if plugin: 
        xbmc.executebuiltin('Container.Update(%s)' % plugin)


def playMedia(original): 
    import re
    cmd = favourite.tidy(original).replace(',', '') #remove spurious commas
    
    try:    mode = int(favourite.getOption(original, 'mode'))
    except: mode = 0

    if mode == PLAYMEDIA_MODE:       
        xbmc.executebuiltin(cmd)
        return

    plugin = re.compile('"(.+?)"').search(cmd).group(1)


    if len(plugin) < 1:
        xbmc.executebuiltin(cmd)
        return

    if mode == ACTIVATEWINDOW_MODE:   
        try:    winID = int(favourite.getOption(original, 'winID'))
        except: winID = 10025

        #check if it is a different window and if so activate it
        id = xbmcgui.getCurrentWindowId()

        if id != winID :
            xbmc.executebuiltin('ActivateWindow(%d)', winID)

        cmd = 'Container.Update(%s)' % plugin

        xbmc.executebuiltin(cmd)
        return

    if mode == RUNPLUGIN_MODE:
        cmd = 'RunPlugin(%s)' % plugin

        xbmc.executebuiltin(cmd)
        return

    #if all else fails just execute it
    xbmc.executebuiltin(cmd)
