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


def getCmd(path, fanart, desc, window, filename, isFolder):
    import favourite

    if path.lower().startswith('addons://user/'):
        path     = path.replace('addons://user/', 'plugin://')
        isFolder = True
        window   = 10025

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

    if isFolder:
        cmd = cmd.replace('")', '",return)')

    return cmd


def copyFave(name, thumb, cmd):
    import os
    text = GETTEXT(30019)

    startFolder = ''
    if ADDON.getSetting('MENU_PREV_LOCN') == 'true':
        startFolder = xbmcgui.Window(10000).getProperty('SF_CAPTURE_FOLDER')

    if len(startFolder) == 0:
        startFolder = None

    folder = utils.GetFolder(text, startFolder)
    if not folder:
        return False

    xbmcgui.Window(10000).setProperty('SF_CAPTURE_FOLDER', folder)
  
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


def add(params):
    try:
        label    = params['label']
        thumb    = params['thumb']
        fanart   = params['fanart']
        path     = params['path']
        desc     = params['description']
        window   = params['window']
        filename = params['filename']
        isFolder = params['isfolder']

        cmd = getCmd(path, fanart, desc, window, filename, isFolder)
        copyFave(label, thumb, cmd)
    except Exception, e:
        utils.log('\n\nError in addToFaves.add : %s' % str(e))
        if params:
            for key in params:
                utils.log('%s\t\t: %s' % (key, params[key]))
    


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

    isStream = False
   
    #if hasattr(xbmc.Player(), 'isInternetStream'):
    #    isStream = xbmc.Player().isInternetStream()
    #elif file:
    if file:
        isStream = file.startswith('http')

    if window == 10003: #filemanager
        control = 0
        if xbmc.getCondVisibility('Control.HasFocus(20)') == 1:
            control = 20
        elif xbmc.getCondVisibility('Control.HasFocus(21)') == 1:
            control = 21

        if control == 0:
            return None

        label    = xbmc.getInfoLabel('Container(%d).ListItem.Label' % control)
        root     = xbmc.getInfoLabel('Container(%d).ListItem.Path'  % control)
        path     = root + label
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

