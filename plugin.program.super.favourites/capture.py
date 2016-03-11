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
import xbmcaddon
import os


_STD_MENU     = 0
_ADDTOFAVES   = 100
_SF_SETTINGS  = 200
_SETTINGS     = 250
_LAUNCH_SF    = 300
_SEARCH       = 400
_SEARCHDEF    = 500
_RECOMMEND    = 600
_DOWNLOAD     = 700
_PLAYLIST     = 800
_COPYIMAGES   = 900
_SHOWIMAGE    = 1000
_QUICKLAUNCH  = 1100

_EXTRABASE    = 10000

try:
    import utils
    ADDON   = utils.ADDON
    ADDONID = utils.ADDONID
    ROOT    = utils.ROOT

    GETTEXT = utils.GETTEXT

    MENU_ADDTOFAVES     = ADDON.getSetting('MENU_ADDTOFAVES')     == 'true'
    MENU_DEF_ISEARCH    = ADDON.getSetting('MENU_DEF_ISEARCH')    == 'true'
    MENU_ISEARCH        = ADDON.getSetting('MENU_ISEARCH')        == 'true'
    MENU_IRECOMMEND     = ADDON.getSetting('MENU_IRECOMMEND')     == 'true'
    MENU_COPY_PROPS     = ADDON.getSetting('MENU_COPY_PROPS')     == 'true'
    MENU_VIEW_IMAGES    = ADDON.getSetting('MENU_VIEW_IMAGES')    == 'true'
    MENU_SF_SETTINGS    = ADDON.getSetting('MENU_SF_SETTINGS')    == 'true'
    MENU_ADDON_SETTINGS = ADDON.getSetting('MENU_ADDON_SETTINGS') == 'true'
    MENU_STD_MENU       = ADDON.getSetting('MENU_STD_MENU')       == 'true'
    MENU_EDITFAVE       = ADDON.getSetting('MENU_EDITFAVE')       == 'true'
    MENU_PLUGINS        = ADDON.getSetting('MENU_PLUGINS')        == 'true'
    MENU_QUICKLAUNCH    = ADDON.getSetting('MENU_QUICKLAUNCH')    == 'true'
    MENU_DOWNLOADS      = ADDON.getSetting('MENU_DOWNLOADS')      == 'true'
except Exception, e:
    utils.log('Error initialising global menu : %s' % str(e))
    ADDON = None


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


def getDefaultSearch():
    import search

    fave = search.getDefaultSearch()
    if fave:
        return fave[0]

    return ''


def activateWindow(window):
    xbmc.executebuiltin('Dialog.Close(all, true)')
    xbmc.executebuiltin('ActivateWindow(%s)' % window)


def doStandard(useScript=True):
    window = xbmcgui.getCurrentWindowId()

    if window == 10000: #home
        if xbmc.getCondVisibility('Window.IsActive(favourites)') <> 1:
            return

    if window == 12005: #video playing
        return activateWindow('videoplaylist')
        
    if useScript:
        #open menu via script to prevent animation locking up (due to bug in XBMC)
        path   = utils.HOME
        script = os.path.join(path, 'standardMenu.py')
        cmd    = 'AlarmClock(%s,RunScript(%s),%d,True)' % ('menu', script, 0)
        xbmc.executebuiltin(cmd)  
    else:
        xbmc.executebuiltin('Action(ContextMenu)')
    

def copyFave(name, thumb, cmd):
    import favourite

    text = GETTEXT(30019)

    folder = utils.GetFolder(text)
    if not folder:
        return False
  
    file  = os.path.join(folder, utils.FILENAME)   

    if MENU_EDITFAVE:
        name = getText(GETTEXT(30021), name)
        
    if not name:
        return False
    
    fave = [name, thumb, cmd] 
  
    return favourite.copyFave(file, fave)


def activateCommand(cmd):
    cmds = cmd.split(',', 1)

    activate = cmds[0]+',return)'
    plugin   = cmds[1][:-1]

    #check if it is a different window and if so activate it
    id = str(xbmcgui.getCurrentWindowId())

    if id not in activate:
        xbmc.executebuiltin(activate)
    
    xbmc.executebuiltin('Container.Update(%s)' % plugin)


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


def getPlugins():
    if not MENU_PLUGINS:
        return []

    import os

    path = xbmc.translatePath(os.path.join(ROOT, 'Plugins'))
    sys.path.insert(0, path)

    plugin  = []

    import sfile
    files = sfile.glob(path)

    for name in files:
        name = name.rsplit(os.sep, 1)[1]
        if name.rsplit('.', 1)[-1] == 'py':
            plugin.append(name .rsplit('.', 1)[0])

    plugins = map(__import__, plugin)

    return plugins 


def addPlugins(menu, plugins, params, base):
    offset = 0
    for plugin in plugins:
        items = None
        if hasattr(plugin, 'add') and hasattr(plugin, 'process'):
            try :   items = plugin.add(params)
            except: items = None

        if items:
            if not isinstance(items, list):
                items = [items]
            for item in items:
                menu.append((item, base+offset))
                offset += 1


        offset = 0
        base  += 1000


def quickLaunch():
    import chooser
    
    if not chooser.GetFave('SF_QL'):
        return False
    
    path = xbmc.getInfoLabel('Skin.String(SF_QL.Path)')

    if len(path) == 0 or path == 'noop':
        return

    if path.lower().startswith('activatewindow') and ',' in path: #i.e. NOT like ActivateWindow(filemanager)
        xbmc.executebuiltin(path)
        return

    import player
    player.playCommand(path)


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


def whitelisted():   
    #folder = xbmc.getInfoLabel('Container.FolderPath')
    #if not folder.startswith('addons'):
    #    return False

    filename = xbmc.getInfoLabel('ListItem.FilenameAndPath')

    try:
        addon = filename.split('://', 1)[-1].split('/', 1)[0]  
        addon = xbmcaddon.Addon(addon).getAddonInfo('path')
        addon = addon.rsplit(os.path.sep, 1)[-1]     
     
        return addon in ADDON.getSetting('WHITELIST')
    except:
        pass
   
    return False


def launchDefaultSearch(keyword):
    import search
    fave = search.getDefaultSearch()
    if not fave:
        return

    cmd = fave[2]
    cmd = cmd.replace('[%SF%]',  keyword)
    cmd = cmd.replace('[%SF+%]', keyword.replace('+', '%2b'))

    if cmd.startswith('RunScript'):
        #special fix for GlobalSearch, use local launcher (globalsearch.py) to bypass keyboard
        cmd = cmd.replace('script.globalsearch', os.path.join(HOME, 'globalsearch.py'))
        #cmd = 'AlarmClock(%s,%s,%d,True)' % ('Default iSearch', cmd, 0)
        xbmc.executebuiltin(cmd) 
    else:
        import re       
        cmd = re.compile('"(.+?)"').search(cmd).group(1)
        xbmc.executebuiltin('XBMC.Container.Update(%s)' % cmd)
         
def doMenu(mode):
    utils.log('**** Context Menu Information ****')

    window = xbmcgui.getCurrentWindowId()

    DEBUG = ADDON.getSetting('DEBUG') == 'true'
    if DEBUG:
        utils.DialogOK('Current Window ID %d' % window)

    utils.log('Capture window\t: %d' % window)

    #active = [0, 1, 2, 3, 25, 40, 500, 501, 502, 601, 2005]
    #if window-10000 not in active:
    #    doStandard(useScript=False)
    #    return

    if window > 12999:
        doStandard(useScript=False)
        return

    # to prevent master profile setting being used in other profiles
    if mode == 0 and ADDON.getSetting('CONTEXT') != 'true':
        doStandard(useScript=False)
        return

    folder = xbmc.getInfoLabel('Container.FolderPath')
    path   = xbmc.getInfoLabel('ListItem.FolderPath')

    #ignore if in Super Favourites
    if (ADDONID in folder) or (ADDONID in path):
        doStandard(useScript=False)
        return

    if mode == 0 and whitelisted():
        doStandard(useScript=False)
        return
        
    choice   = 0
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
            return doStandard(useScript=False)

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


    for key in params:
        utils.log('%s\t\t: %s' % (key, params[key]))

    menu       = []
    localAddon = None

    if MENU_QUICKLAUNCH:
        menu.append((GETTEXT(30219), _QUICKLAUNCH))

    plugins    = []
    try:
        plugins = getPlugins()
        addPlugins(menu, plugins, params, _EXTRABASE)
    except Exception, e:
        utils.log('Error adding plugins : %s' % str(e))
        
    if len(path) > 0:

        if MENU_ADDTOFAVES:
            menu.append((GETTEXT(30047), _ADDTOFAVES))


        if MENU_ADDON_SETTINGS:          
            localAddon = utils.findAddon(path)           
            if localAddon:
                name = utils.getSettingsLabel(localAddon)
                menu.append((name, _SETTINGS))
       

        if MENU_DEF_ISEARCH:           
            default = getDefaultSearch()
            if len(default) > 0:
                menu.append((GETTEXT(30098) % default, _SEARCHDEF))


        if MENU_ISEARCH: menu.append((GETTEXT(30054), _SEARCH))

        if MENU_IRECOMMEND: menu.append((GETTEXT(30088), _RECOMMEND))


        if MENU_COPY_PROPS:
            if len(thumb) > 0 or len(fanart) > 0:
                menu.append((GETTEXT(30209), _COPYIMAGES))   
                if MENU_VIEW_IMAGES: menu.append((GETTEXT(30216), _SHOWIMAGE))
            else:
                if len(description) > 0: menu.append((GETTEXT(30209), _COPYIMAGES))   
   

    if MENU_SF_SETTINGS:
        menu.append((GETTEXT(30049), _SF_SETTINGS))

    stdMenu = False
    if MENU_STD_MENU:
        if (len(path) > 0) or (window == 10034): #10034 is profile dialog
            stdMenu = True
            menu.append((GETTEXT(30048), _STD_MENU))
        else:
            if hasVideo:  
                menu.append((xbmc.getLocalizedString(31040), _PLAYLIST)) #Now Playing
                if MENU_DOWNLOADS and isStream:  
                    menu.append((GETTEXT(30241), _DOWNLOAD))
                    
    if len(menu) == 0 or (len(menu) == 1 and stdMenu):
        doStandard(useScript=False)
        return

    xbmcgui.Window(10000).setProperty('SF_MENU_VISIBLE', 'true')

    dialog = ADDON.getSetting('CONTEXT_STYLE') == '1' 

    import menus

    if dialog:
        choice = menus.selectMenu(utils.TITLE, menu)
    else:
        choice = menus.showMenu(ADDONID, menu)

    utils.log('selection\t\t: %s' % choice)
    
    if choice >= _EXTRABASE:       
        module = (choice - _EXTRABASE) / 1000
        option = (choice - _EXTRABASE) % 1000

        utils.log('plugin\t\t: %s' % module)
        utils.log('option\t\t: %s' % option)

        try:    
            plugins[module].process(option, params)
        except Exception, e:
            utils.log('Error processing plugin: %s' % str(e))


    if choice == _QUICKLAUNCH:
        try:    quickLaunch()
        except: pass


    if choice == _STD_MENU:
        doStandard(useScript=True)


    if choice == _PLAYLIST:
        activateWindow('videoplaylist')


    if choice == _DOWNLOAD:
        utils.log('download url: %s' % file)
        dst = os.path.join(ADDON.getSetting('DOWNLOAD_FOLDER'), getDownloadTitle(file))  

        if utils.DialogYesNo(GETTEXT(30243), GETTEXT(30244)):            
            xbmc.Player().stop()
       
        import download            
        download.download(file, dst, 'Super Favourites')


    if choice == _SF_SETTINGS:
        utils.ADDON.openSettings()


    if choice == _SETTINGS:
        xbmcaddon.Addon(localAddon).openSettings()


    if choice == _ADDTOFAVES:
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

        copyFave(label, thumb, cmd)


    if choice == _LAUNCH_SF:
        utils.LaunchSF()


    if choice in [_SEARCH, _SEARCHDEF, _RECOMMEND]:
        if utils.ADDON.getSetting('STRIPNUMBERS') == 'true':
            label = utils.Clean(label)

        thumb  = thumb  if len(thumb)  > 0 else 'null'
        fanart = fanart if len(fanart) > 0 else 'null'

        #declared in default.py
        _SUPERSEARCH    =    0
        _SUPERSEARCHDEF =   10
        _RECOMMEND_KEY  = 2700

        valid = [10001, 10002, 10025, 10502]

        if window not in valid:
            window = 10025 #video window

        import urllib   

        if choice == _RECOMMEND:
            mode = _RECOMMEND_KEY
        else:
            mode = _SUPERSEARCH if (choice == _SEARCH) else _SUPERSEARCHDEF

        if mode == _SUPERSEARCHDEF:
            return launchDefaultSearch(label)
            
        cmd = 'ActivateWindow(%d,"plugin://%s/?mode=%d&keyword=%s&image=%s&fanart=%s")' % (window, ADDONID, mode, urllib.quote_plus(label), urllib.quote_plus(thumb), urllib.quote_plus(fanart))

        activateCommand(cmd)

    if choice == _COPYIMAGES:  
        if not fanart:
            fanart = thumb
      
        xbmcgui.Window(10000).setProperty('SF_THUMB',       thumb)
        xbmcgui.Window(10000).setProperty('SF_FANART',      fanart)
        xbmcgui.Window(10000).setProperty('SF_DESCRIPTION', desc)


    if choice == _SHOWIMAGE:
        if not fanart:
            fanart = thumb

        import viewer
        viewer.show(fanart, thumb, ADDONID)


def menu(mode):
    if xbmcgui.Window(10000).getProperty('SF_MENU_VISIBLE') == 'true':
        return

    if ADDON.getSetting('MENU_MSG') == 'true':
        ADDON.setSetting('MENU_MSG', 'false')
        if utils.DialogYesNo(GETTEXT(35015), GETTEXT(35016), GETTEXT(35017)):
            utils.openSettings(ADDONID, 2.6)
            return
    
    #xbmc.executebuiltin('Dialog.Close(all, true)')
    doMenu(mode) 


def main():
    if xbmc.getCondVisibility('Window.IsActive(favourites)') == 1:
        return doStandard(useScript=False)

    mode = 0
    if len(sys.argv) > 0 and sys.argv[0] == '':
        mode = 1 #launched via std context menu
    
    try:        
        menu(mode)
    except Exception, e:
        utils.log('Exception in capture.py %s' % str(e))


progress = xbmc.getCondVisibility('Window.IsActive(progressdialog)') == 1
if ADDON and not progress:
    main()
    xbmc.sleep(1000)
    xbmcgui.Window(10000).clearProperty('SF_MENU_VISIBLE')
else:
    xbmc.executebuiltin('Action(ContextMenu)')