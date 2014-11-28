
#       Copyright (C) 2013-2014
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


def iPlay():
    #add browse item
    #addDir(GETTEXT(30148), _PLAYLISTBROWSE, thumbnail='DefaultMusicPlaylists.png', isFolder=False) 

    nItems = 0

    folder = os.path.join(xbmc.translatePath(ROOT), 'PL')
    if not os.path.isdir(folder):
        os.makedirs(folder)

    #parse SF folder
    nItems += addPlaylistItems(parsePlaylistFolder(folder), 'DefaultMusicVideos.png', delete=True)

    #parse SF list 
    file = os.path.join(folder, FILENAME)

    playlists = favourite.getFavourites(file, validate=False)
    items = []
    for playlist in playlists:
        name  = playlist[0]
        thumb = playlist[1]
        cmd   = playlist[2]
        items.append([cmd, name, thumb])

    nItems += addPlaylistItems(items, delete=True)

    #parse Kodi folders    
    folder  = xbmc.translatePath('special://profile/playlists')
    nItems += addPlaylistItems(parsePlaylistFolder(os.path.join(folder, 'video')), 'DefaultMovies.png',      delete=ALLOW_PLAYLIST_DELETE)
    nItems += addPlaylistItems(parsePlaylistFolder(os.path.join(folder, 'music')), 'DefaultMusicSongs.png',  delete=ALLOW_PLAYLIST_DELETE)
    nItems += addPlaylistItems(parsePlaylistFolder(os.path.join(folder, 'mixed')), 'DefaultMusicVideos.png', delete=ALLOW_PLAYLIST_DELETE)

    return nItems > 0


def addPlaylistItems(items, thumbnail='DefaultMovies.png', delete=False):
    for item in items:
        path  = item[0]
        title = item[1]
        if len(item) > 2:
            thumbnail = item[2]

        menu = []

        #browse
        cmd = '%s?mode=%d' % (sys.argv[0], _PLAYLISTBROWSE)
        menu.append((GETTEXT(30148), 'XBMC.Container.Update(%s)' % cmd))

        #browse for URL
        cmd = '%s?mode=%d' % (sys.argv[0], _URLPLAYLIST)
        menu.append((GETTEXT(30153), 'XBMC.Container.Update(%s)' % cmd))

        menu.append((GETTEXT(30084), 'XBMC.PlayMedia(%s)' % path))

        if delete:
            menu.append((GETTEXT(30150), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _DELETEPLAYLIST, urllib.quote_plus(path))))

        menu.append((GETTEXT(30047), 'XBMC.RunPlugin(%s?mode=%d&path=%s&label=%s&thumb=%s)' % (sys.argv[0], _COPYPLAYLIST, urllib.quote_plus(path), urllib.quote_plus(title), urllib.quote_plus(thumbnail))))
        

        addDir(title, _PLAYLISTFILE, path=path, thumbnail=thumbnail, menu=menu) 

    return len(items)


def iPlaylistDelete(path):
    #delete from SF list of Playlists
    folder    = os.path.join(xbmc.translatePath(ROOT), 'PL')
    file      = os.path.join(folder, FILENAME)
    playlists = favourite.getFavourites(file, validate=False)
    updated   = []

    for playlist in playlists:
        if playlist[2] != path:
            updated.append(playlist)

    if len(updated) < len(playlists):
        favourite.writeFavourites(file, updated)
        return True

    if os.path.exists(path):
        utils.DeleteFile(path)
        return True

    return False


def iPlaylistItem(path, title='', thumb='DefaultMovies.png'):
    #if currently in program menu play directly
    if xbmcgui.getCurrentWindowId() == 10001:        
        liz = xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
        pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        pl.clear()
        pl.add(path, liz)
        xbmc.Player().play(pl)
        return

    item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def iPlaylistURL(url):
    try:    html = quicknet.getURL(url, maxSec=600, tidy=False)
    except: html = ''
    
    nItems = addItems(html.split('\n'))

    if nItems == 0:
        utils.DialogOK(GETTEXT(30155), url)
        return False

    return True


def iPlaylistFile(path):
    path = xbmc.translatePath(path)
    if not os.path.exists(path):
        return iPlaylistURL(path)

    f        = open(path , 'r')
    playlist = f.readlines()
    f.close()

    return addItems(playlist)


def addItems(playlist):
    items = parsePlaylist(playlist)

    nItem = len(items)

    for item in items:
        menu  = []
        title = item[0]
        path  = item[1]

        isAudio = title.lower().endswith('.mp3')
        if isAudio:
            title = title.replace('.mp3', '')
            thumb = 'DefaultAudio.png'
        else:
            thumb = 'DefaultFile.png'

        title = favourite.unescape(title).strip()

        menu.append((GETTEXT(30047), 'XBMC.RunPlugin(%s?mode=%d&path=%s&label=%s&thumb=%s)' % (sys.argv[0], _COPYPLAYLISTITEM, urllib.quote_plus(path), urllib.quote_plus(title), urllib.quote_plus(thumb))))

        isPlayable = xbmcgui.getCurrentWindowId() != 10001

        addDir(title, _PLAYLISTITEM, path=path, thumbnail=thumb, isFolder=False, menu=menu, totalItems=nItem, isPlayable=isPlayable)


    return nItem > 0
        

def parsePlaylistFolder(folder):
    try:    current, dirs, files = os.walk(folder).next()
    except: return []

    items = []

    for file in files:
        try:
            path = os.path.join(current, file)
            file = file.rsplit('.', 1)
            ext  = file[-1]
            file = file[0]            
            if ext in PLAYLIST_EXT:
                items.append([path, file])
        except:
            pass

    return items


def parsePlaylist(playlist):
    if len(playlist) == 0:
        return []

    items = []
    path  = ''
    title = ''
 
    try:
        for line in playlist:
            line = line.strip()
            if line.startswith('#EXTINF:'):
                path  = line.split(':', 1)[-1].split(',', 1)[-1]
            else:
                title = line.replace('rtmp://$OPT:rtmp-raw=', '')
                if len(path) > 0 and len(title) > 0:
                    items.append([path, title])
                path  = ''
                title = ''
    except:
        pass
            
    return items


def getPlaylist():
    root     = HOME.split(os.sep, 1)[0] + os.sep    
    playlist = xbmcgui.Dialog().browse(1,GETTEXT(30148), 'files', PLAYLIST_EXT, False, False, root)
    
    if playlist and playlist != root:
        return playlist

    return None


def iPlaylistURLBrowse():
    valid = False
    text  = 'http://'

    while not valid:
        text = getText(GETTEXT(30153), text)

        if not text:
            return False

        if text == 'http://':
            return

        try:    html = quicknet.getURL(text, maxSec=600, tidy=False)
        except: html = ''

        items = parsePlaylist(html.split('\n'))
        valid = len(items) > 0

        if not valid:
            utils.DialogOK(GETTEXT(30155), text)
        
    name = getText(GETTEXT(30156))

    if not name:
        return False

    if COPY_PLAYLISTS:
        name += '.m3u'
        file  = os.path.join(xbmc.translatePath(ROOT), 'PL', name)
        f = open(file, mode='w')
        f.write(html)
        f.close()
        return True

    cmd   = text
    thumb = 'DefaultFile.png'
    addPlaylistToSF(name, cmd, thumb) 

    return True


def iPlaylistBrowse():
    playlist = getPlaylist()

    if not playlist:
        return False

    folder = os.path.join(xbmc.translatePath(ROOT), 'PL')
    if not os.path.isdir(folder):
        os.makedirs(folder)

    if COPY_PLAYLISTS:
        try:
            import shutil
            shutil.copy(playlist , folder)
            return True
        except:
            return False
    
    name  = playlist.rsplit(os.sep, 1)[-1].rsplit('.', 1)[0]
    cmd   = playlist
    thumb = 'DefaultMovies.png'

    return addPlaylistToSF(name, cmd, thumb)


def addPlaylistToSF(name, cmd, thumb):
    folder = os.path.join(xbmc.translatePath(ROOT), 'PL')
    if not os.path.isdir(folder):
        os.makedirs(folder)

    file  = os.path.join(folder, FILENAME)

    cmd = favourite.convertToHome(cmd)

    if favourite.findFave(file, cmd)[0]:
        return False

    playlist = [name, thumb, cmd]

    playlists = favourite.getFavourites(file, validate=False)
    playlists.append(playlist)
    favourite.writeFavourites(file, playlists)

    return True


def iPlayCopyItemToSF(path, title, thumb):
    folder = utils.GetFolder(title)
    if not folder:
        return

    copy = ['', '', '']
    path = path

    copy[0] = title
    copy[1] = thumb
    copy[2] = 'PlayMedia("%s")' % path

    file = os.path.join(folder, FILENAME)
    favourite.copyFave(file, copy)


def iPlayCopyToSF(path, title, thumb):
    folder = utils.GetFolder(title)
    if not folder:
        return

    copy = ['', '', '']
    path = path

    copy[0] = title
    copy[1] = thumb
    copy[2] = 'ActivateWindow(10025,"%s",return)' % path

    file = os.path.join(folder, FILENAME)
    favourite.copyFave(file, copy)
