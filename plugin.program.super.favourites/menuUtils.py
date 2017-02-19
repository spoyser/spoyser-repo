#
#       Copyright (C) 2016-
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

GETTEXT = utils.GETTEXT 
ADDON   = utils.ADDON


def getText(title, text=''):
    if text == None:
        text = ''

    kb = xbmc.Keyboard(text.strip(), title)
    kb.doModal()

    if not kb.isConfirmed():
        return None

    text = kb.getText().strip()

    if len(text) < 1:
        return None

    return text



def getCmd(path, fanart, desc, window, filename, isFolder, meta):
    import favourite

    if path.lower().startswith('addons://user/'):
        path     = path.replace('addons://user/', 'plugin://')
        isFolder = True
        window   = 10025

    if window == 10003:#FileManager
        import sfile
        import os
        isFolder = sfile.isdir(path)
        if isFolder:
            #special paths fail to open - http://trac.kodi.tv/ticket/17333
            if path.startswith('special://'):
                path = xbmc.translatePath(path)
            path = path.replace('%s%s' % (os.sep, os.sep), os.sep)
            path = path.replace(os.sep, '/')
            folder = path
            if folder.endswith('/'):
                folder = folder[:-1]
            folder = folder.rsplit('/', 1)[-1]
            #if not utils.DialogYesNo(GETTEXT(30271) % folder, GETTEXT(30272)):
            #    return None
            
    if isFolder:
        cmd =  'ActivateWindow(%d,"%s' % (window, path)
    elif path.lower().startswith('script'):
        #if path[-1] == '/':
        #    path = path[:-1]
        cmd = 'RunScript("%s' % path.replace('script://', '')
    elif path.lower().startswith('videodb') and len(filename) > 0:
        cmd = 'PlayMedia("%s' % filename.replace('\\', '\\\\')
    #elif path.lower().startswith('musicdb') and len(filename) > 0:
    #    cmd = 'PlayMedia("%s")' % filename
    elif path.lower().startswith('androidapp'):
        cmd = 'StartAndroidActivity("%s")' % path.replace('androidapp://sources/apps/', '', 1)
    else:            
        cmd = 'PlayMedia("%s")' % path
        cmd = favourite.updateSFOption(cmd, 'winID', window)

    cmd = favourite.addFanart(cmd, fanart)
    cmd = favourite.updateSFOption(cmd, 'desc', desc)

    if meta:
        import urllib
        meta = utils.convertDictToURL(meta)
        cmd  = favourite.updateSFOption(cmd, 'meta', urllib.quote_plus(meta))

    if isFolder:
        cmd = cmd.replace('")', '",return)')

    return cmd


def copyFave(name, thumb, cmd):
    import os
    text = GETTEXT(30019)

    folder = utils.GetSFFolder(text)
    if not folder:
        return False
  
    file  = os.path.join(folder, utils.FILENAME)   

    if ADDON.getSetting('MENU_EDITFAVE') == 'true':
        name = getText(GETTEXT(30021), name)
        
    if not name:
        return False
    
    fave = [name, thumb, cmd] 
  
    return favourite.copyFave(file, fave)


def getDescription():
    labels = []
    labels.append('ListItem.Plot')
    labels.append('ListItem.Property(Addon.Description)')
    labels.append('ListItem.Property(Addon.Summary)')
    labels.append('ListItem.Property(Artist_Description)')
    labels.append('ListItem.Property(Album_Description)')
    labels.append('ListItem.Artist')
    labels.append('ListItem.Comment')

    for label in labels:
        desc = xbmc.getInfoLabel(label)
        if len(desc) > 0:
            return desc

    return ''


def addToFaves(params, meta=None):
    try:
        label    = params['label']
        thumb    = params['thumb']
        fanart   = params['fanart']
        path     = params['path']
        desc     = params['description']
        window   = params['window']
        filename = params['filename']
        isFolder = params['isfolder']

        cmd = getCmd(path, fanart, desc, window, filename, isFolder, meta)

        if cmd:
            copyFave(label, thumb, cmd)
    except Exception, e:
        utils.log('\n\nError in menuUtils.addToFaves : %s' % str(e))
        utils.outputDict(params)


def getCast():
    value = xbmc.getInfoLabel('ListItem.%s' % 'castandrole')
    if value:
        return [tuple(cr.split(' as ', 1)) for cr in value.split('\n')]

    value = xbmc.getInfoLabel('ListItem.%s' % 'cast')
    if value:
        return [tuple([cr, '']) for cr in value.split('\n')]

    castItems = []

    type = xbmc.getInfoLabel('ListItem.DBTYPE')
   
    if type == 'movie':
        castItems = getMovieCast()

    elif type == 'tvshow':
        castItems = getTVShowCast()

    elif type == 'episode':
        castItems = getEpisodeCast()

    elif type == 'season':
        castItems = getSeasonCast()

    cast = []
    for item in castItems:
        name  = item['name']
        role = item['role']
        cast.append((name, role))

    return cast


def getMovieCast():
    import json
    dbid  = xbmc.getInfoLabel('ListItem.DBID')

    if dbid < 0:
        return []

    query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "VideoLibrary.GetMovieDetails", "params": {"movieid": %s, "properties": ["cast"]}, "id": 1 }' % dbid)
    query = unicode(query, 'utf-8', errors='ignore')

    j = json.loads(query)

    return j['result']['moviedetails']['cast']

            
def getTVShowCast(dbid=None):
    import json

    if not dbid:
        dbid  = xbmc.getInfoLabel('ListItem.DBID')

    if dbid < 0:
        return []

    query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "VideoLibrary.GetTVShowDetails", "params": {"tvshowid": %s, "properties": ["cast"]}, "id": 1 }' % dbid)
    query = unicode(query, 'utf-8', errors='ignore')

    j = json.loads(query)

    return j['result']['tvshowdetails']['cast']



def getSeasonCast():
    import json

    dbid  = xbmc.getInfoLabel('ListItem.DBID')

    if dbid < 0:
        return []

    query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "VideoLibrary.GetSeasonDetails", "params": {"seasonid": %s, "properties": ["tvshowid"]}, "id": 1 }' % dbid)
    query = unicode(query, 'utf-8', errors='ignore')

    j = json.loads(query)

    if 'result' not in j: #usually caused by the 'All Seasons' item
        dbid  = str(int(dbid) + 2) #this seems to give Season 1 which will suffice
        query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "VideoLibrary.GetSeasonDetails", "params": {"seasonid": %s, "properties": ["tvshowid"]}, "id": 1 }' % dbid)
        query = unicode(query, 'utf-8', errors='ignore')

        j = json.loads(query)

        if 'result' not in j:
            return []

    seasonID = j['result']['seasondetails']['seasonid']
    tvshowID = j['result']['seasondetails']['tvshowid']

    return getTVShowCast(tvshowID)


def getEpisodeCast():
    import json

    dbid  = xbmc.getInfoLabel('ListItem.DBID')

    if dbid < 0:
        return []

    query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodeDetails", "params": {"episodeid": %s, "properties": ["cast"]}, "id": 1 }' % dbid)
    query = unicode(query, 'utf-8', errors='ignore')

    j = json.loads(query)

    return j['result']['episodedetails']['cast']


def getCurrentMeta():
    infoLabels = []

    infoLabels.append('rating')
    infoLabels.append('userrating')
    infoLabels.append('votes')
    infoLabels.append('trailer')
    infoLabels.append('duration')
    infoLabels.append('genre')
    infoLabels.append('mpaa')
    infoLabels.append('plot')
    infoLabels.append('plotoutline')
    infoLabels.append('tagline')
    infoLabels.append('title')
    infoLabels.append('originaltitle')
    infoLabels.append('label')
    infoLabels.append('writer')
    infoLabels.append('director')
    infoLabels.append('year')
    infoLabels.append('premiered')
    infoLabels.append('season')
    infoLabels.append('episode')
    infoLabels.append('imdbnumber')
    infoLabels.append('studio')

    params = {}
    for label in infoLabels:
        value = xbmc.getInfoLabel('ListItem.%s' % label)
        if value:
            if label == 'duration':
                try:    value = int(value) * 60
                except: continue
            params[label] = value

    try:
        cast = getCast()
        if cast:
            params['castandrole'] = cast
    except:
        pass

    return params
    

def getCurrentParams():    
    window   = xbmcgui.getCurrentWindowId()
    folder   = xbmc.getInfoLabel('Container.FolderPath')
    path     = xbmc.getInfoLabel('ListItem.FolderPath')     
    label    = xbmc.getInfoLabel('ListItem.Label')
    filename = xbmc.getInfoLabel('ListItem.FilenameAndPath')
    thumb    = xbmc.getInfoLabel('ListItem.Thumb')    
    icon     = xbmc.getInfoLabel('ListItem.ActualIcon')    
    #thumb   = xbmc.getInfoLabel('ListItem.Art(thumb)')
    playable = xbmc.getInfoLabel('ListItem.Property(IsPlayable)').lower() == 'true'
    #fanart   = xbmc.getInfoLabel('ListItem.Property(Fanart_Image)')
    fanart   = xbmc.getInfoLabel('ListItem.Art(fanart)')
    isFolder = xbmc.getCondVisibility('ListItem.IsFolder') == 1
    hasVideo = xbmc.getCondVisibility('Player.HasVideo') == 1
    desc     = getDescription()
   
    if not thumb:
        thumb = icon

    try:    file = xbmc.Player().getPlayingFile()
    except: file = None

    isStream = xbmc.getCondVisibility('Player.IsInternetStream') == 1
    
    #if file:
    #    isStream = file.startswith('http')

    if window == 10003: #filemanager
        import os
        control = 0
        if xbmc.getCondVisibility('Control.HasFocus(20)') == 1:
            control = 20
        elif xbmc.getCondVisibility('Control.HasFocus(21)') == 1:
            control = 21

        if control == 0:
            return None

        label    = xbmc.getInfoLabel('Container(%d).ListItem.Label' % control)
        path     = xbmc.getInfoLabel('Container(%d).ListItem.FolderPath' % control)
        filename = xbmc.getInfoLabel('Container(%d).ListItem.Filename' % control)
        folder   = path.replace(filename,  '')

        if path.endswith(os.sep):
            path = path[:-1] #.rsplit(os.sep, 1)[0]

        isFolder = True
        thumb    = 'DefaultFolder.png'
        #if not path.endswith(os.sep):
        #    path += os.sep

    if isFolder:
        path     = path.replace('\\', '\\\\')
        filename = filename.replace('\\', '\\\\')

    params                = {}
    params['label']       = label
    params['folder']      = folder
    params['path']        = path
    params['filename']    = filename
    params['thumb']       = thumb
    params['icon']        = icon
    params['fanart']      = fanart
    params['window']      = window
    params['isplayable']  = playable
    params['isfolder']    = isFolder
    params['file']        = file
    params['isstream']    = isStream
    params['description'] = desc
    params['hasVideo']    = hasVideo

    return params


def getExt(url):
    url  = url.lower()
    exts = ['.mp4', '.avi', '.mpg', '.flv', '.mkv', '.m4v', '.mov']
    for ext in exts:
        if ext in url:
            return ext

    return '.avi'


def getDownloadTitle(url):
    import re

    title = xbmc.getInfoLabel('VideoPlayer.Title')

    try:
        season = int(xbmc.getInfoLabel('VideoPlayer.Season'))
        title += ' S%02d' % season 
    except:
        pass

    try:
        episode = int(xbmc.getInfoLabel('VideoPlayer.Episode'))
        title += 'E%02d' % episode 
    except:
        pass

    title  = re.sub('[:\\/*?\<>|"]+', '', title)
    title  = title.strip()
    title += getExt(url)

    return title


def doDownload(file):
    utils.log('download url: %s' % file)
    dst = ADDON.getSetting('DOWNLOAD_FOLDER')

    import sfile
    sfile.makedirs(dst)

    if not sfile.exists(dst):
        utils.DialogOK(GETTEXT(30256), GETTEXT(30257))
        utils.openSettings(ADDONID, 2.24)
        xbmc.sleep(500)
        while(xbmc.getCondVisibility('Window.IsActive(addonsettings)') == 1):
            xbmc.sleep(100)

    dst = ADDON.getSetting('DOWNLOAD_FOLDER')
    if not sfile.exists(dst):
        utils.DialogOK(GETTEXT(30256))
        return

    import os
    dst = os.path.join(ADDON.getSetting('DOWNLOAD_FOLDER'), getDownloadTitle(file))  

    if utils.DialogYesNo(GETTEXT(30243), GETTEXT(30244)):            
        xbmc.executebuiltin('Action(Stop)')
       
    import download            
    download.download(file, dst, utils.TITLE)

