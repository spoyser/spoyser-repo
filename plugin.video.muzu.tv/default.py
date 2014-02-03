'''
    muzu.tv XBMC Plugin
    Copyright (C) 2011 t0mm0
    Copyright (C) 2013 Sean Poyser seanpoyser@gmail.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from resources.lib import Addon, muzutv 
import os.path
import random
import sys
import xbmc, xbmcgui, xbmcplugin
import re, urllib

CHARTS = []
CHARTS.append('')
CHARTS.append(['568952', 'top-40-charts']) #Top 40
CHARTS.append(['695693', 'uk-rock'])       #Rock Chart
CHARTS.append(['695695', ''])              #Alternative
CHARTS.append(['695696', 'uk-dance'])      #Dance Chart
CHARTS.append(['695701', 'uk-rnb'])        #RnB


Addon.plugin_url = sys.argv[0]
Addon.plugin_handle = int(sys.argv[1])
Addon.plugin_queries = Addon.parse_query(sys.argv[2][1:])

email    = Addon.get_setting('email')
password = Addon.get_setting('password')
muzu     = muzutv.MuzuTv()

Addon.log('plugin url: '     + Addon.plugin_url)
Addon.log('plugin queries: ' + str(Addon.plugin_queries))
Addon.log('plugin handle: '  + str(Addon.plugin_handle))

mode = Addon.plugin_queries['mode']
play = Addon.plugin_queries['play']


def autoPlay():
    pl = Addon.get_playlist(xbmc.PLAYLIST_VIDEO)
    xbmc.Player().play(pl)
    #try and give it time to buffer enough of stream
    xbmc.sleep(5000)
    if xbmc.getCondVisibility('player.paused') == 1:
        xbmc.Player().pause()

def isChart(title):
    return len(re.compile('(.+?) \((.+?)\): (.+?)').findall(title)) > 0

def clean(text):
    text = re.sub('[:\\/*?\<>|"]+', '', text)
    return text.strip()

def getArtistAndTrack(title):
    if isChart(title):
        title = title.split(': ', 1)[1]
        title = title.split(' : ', 1)
        return title[0].strip(), title[1].strip()

    ta = title.split('by')
    if len(ta) == 2:
        return ta[0].strip(), ta[1].strip()

    return title, title


def addToLibrary(play):
    Addon.log('Add to library: %s' % play)

    folder = Addon.get_setting('library_folder')
    if folder == '':
        d = xbmcgui.Dialog()
	d.ok(Addon.get_string(30300),'You have not set the library folder.\nPlease update the addon settings and try again.','','')
	Addon.addon.openSettings(sys.argv[0])
        folder = Addon.get_setting('library_folder')
    if folder == '':
        return

    if Addon.get_setting('download_hq') == 'true': #fix for old versions
        hq = '720p'
    else:
        hq = Addon.get_setting('hq')   

    title      = play.rsplit('@', 1)[0]
    assetID    = play.rsplit('@', 1)[1]
    stream_url = muzu.resolve_stream(assetID, hq) 

    #try and match artist and track name
    artist, track = getArtistAndTrack(title)

    kb = xbmc.Keyboard(artist, 'Enter Artist...' )
    kb.doModal()
    if not kb.isConfirmed():
        return

    artist = clean(kb.getText())

    kb = xbmc.Keyboard(track, 'Enter Track...' )
    kb.doModal()
    if not kb.isConfirmed():
        return

    track = clean(kb.getText())

    if track == '' and artist == '':
        return

    path = os.path.join(folder, artist + ' - ' + track)
    if not os.path.exists(path):
        os.mkdir(path)

    filename = os.path.join(path, track+'.strm')

    strm = stream_url
    f    = open(filename, "w")
    f.write(strm)
    f.close()


def downloadPath(title, stream_url):        		
    if not stream_url or stream_url == '':
        return None

    downloadFolder = Addon.get_setting('download_folder')

    if Addon.get_setting('ask_folder') == 'true':
        dialog = xbmcgui.Dialog()
	downloadFolder = dialog.browse(3, 'Save to folder...', 'files', '', False, False, downloadFolder)
	if downloadFolder == '' :
	    return None

    if downloadFolder is '':
        d = xbmcgui.Dialog()
	d.ok(Addon.get_string(30300),'You have not set the default download folder.\nPlease update the addon settings and try again.','','')
	Addon.addon.openSettings(sys.argv[0])
	downloadFolder = Addon.get_setting('download_folder')

    if downloadFolder == '' and Addon.get_setting('ask_folder') == 'true':
        dialog = xbmcgui.Dialog()
	downloadFolder = dialog.browse(3, 'Save to folder...', 'files', '', False, False, downloadFolder)	

    if downloadFolder == '' :
        return None

    filename = stream_url
    filename = filename.rsplit('/', 1)[1]
    filename = filename.rsplit('?', 1)[0]
    ext      = filename.rsplit('.', 1)[1]

    if isChart(title):
        title = title.split(': ', 1)[1]
   
    if Addon.get_setting('ask_filename') == 'true':
        kb = xbmc.Keyboard(title, 'Save video as...' )
	kb.doModal()
	if kb.isConfirmed():
	    filename = kb.getText()
	else:
	    return None
    else:
        filename = title

    filename = clean(filename) + '.' + ext

    return os.path.join(downloadFolder, filename)

    
if mode == 'download' and play:
    Addon.log('download: %s' % play)

    if Addon.get_setting('download_hq') == 'true': #fix for old versions
        hq = '720p'
    else:
        hq = Addon.get_setting('hq')   

    title      = play.rsplit('@', 1)[0]
    assetID    = play.rsplit('@', 1)[1]
    stream_url = muzu.resolve_stream(assetID, hq) 
    savePath   = downloadPath(title, stream_url)
   
    if savePath:
        #t = str(200*len(savePath))
        #xbmc.executebuiltin("XBMC.Notification(" + Addon.get_string(30300) + ", Downloading: " + savePath + "," + t + ")")

        try:
            import download
            download.download(stream_url, savePath)
        except Exception, e:
            #print str(e)
            pass

elif mode == 'add_library' and play:
    addToLibrary(play)

    
elif play:
    Addon.log('play: %s' % play)
   
    if mode == 'playlist':
        #network = Addon.plugin_queries['network']
        Addon.log('playlist: %s' % play)
        videos = muzu.get_playlist(play) 
        if Addon.get_setting('random_pl') == 'true':
            random.shuffle(videos)

        if Addon.get_setting('auto_pl') == 'true':
            pl = Addon.get_new_playlist(xbmc.PLAYLIST_VIDEO)
            res_dir = os.path.join(Addon.addon.getAddonInfo('path'), 
                               'resources')

            for v in videos:
                title = '%s: %s' % (v['artist'], v['title'])            
                Addon.add_video_item(str(v['asset_id']),
                                 {'title': title,
                                  #'plot': v['description'],
                                  #'duration': str(v['duration']),
                                 },
                                 img=v['thumb'],
                                 playlist=pl)  

            autoPlay()
            mode = 'toplevel_playlist'  
        else:
            for v in videos:
                title = '%s: %s' % (v['artist'], v['title'])            
                Addon.add_video_item(str(v['asset_id']),
                                 {'title': title,
                                  #'plot': v['description'],
                                  #'duration': str(v['duration']),                                  
                                 },
                                 img=v['thumb'])  

    elif mode == 'user_playlist':
        Addon.log('user_playlist: %s' % play)
        videos = muzu.get_userplaylist(Addon.plugin_queries['name'], play, Addon.plugin_queries['username']) 
        if Addon.get_setting('random_pl') == 'true':
            random.shuffle(videos)

        if Addon.get_setting('auto_pl') == 'true':
            pl = Addon.get_new_playlist(xbmc.PLAYLIST_VIDEO)
            res_dir = os.path.join(Addon.addon.getAddonInfo('path'), 
                               'resources')
            for v in videos:
                title = '%s: %s' % (v['artist'], v['title'])            
                Addon.add_video_item(str(v['asset_id']),
                                 {'title': title,
                                  #'plot': v['description'],
                                  #'duration': str(v['duration']),
                                 },
                                 img=v['thumb'],
                                 playlist=pl)  

            autoPlay()            
            mode = 'toplevel_playlist'  
        else:
            for v in videos:
                title = '%s: %s' % (v['artist'], v['title'])            
                Addon.add_video_item(str(v['asset_id']),
                                 {'title': title,
                                  #'plot': v['description'],
                                  #'duration': str(v['duration']),                                  
                                 },
                                 img=v['thumb'])  
        
    else:        
        stream_url = muzu.resolve_stream(play, Addon.get_setting('hq'))    
        if stream_url:
            Addon.resolve_url(stream_url)  
  
elif mode == 'browse':
    page = int(Addon.plugin_queries.get('page', 0))
    res_per_page = int(Addon.get_setting('res_per_page'))
    genre = Addon.plugin_queries.get('genre', '')
    sort = Addon.plugin_queries.get('sort', False)
    
    Addon.log('browse genre: %s, page: %d' % (genre, page))

    if genre:
        if not sort:
            sort = int(Addon.get_setting('sort'))

            if sort == 2:
                dialog = xbmcgui.Dialog()
                sort = dialog.select(Addon.get_string(30029),
                                     [Addon.get_string(30030),
                                      Addon.get_string(30031)])#,
                                      #Addon.get_string(30032)])
            sort = ['views', 'recent', 'alpha'][sort]
        videos = muzu.browse_videos(genre, sort, page, res_per_page, Addon.get_setting('country'))
        if videos == None:
            videos = []
            mode = 'error'

        for v in videos:
            title = '%s: %s' % (v['artist'], v['title'])
            Addon.add_video_item(str(v['asset_id']),
                                 {'title': title,
                                  'plot': v['description'],
                                  'duration': str(v['duration']),
                                 },
                                 img=v['thumb'])
        Addon.add_directory({'mode': 'browse', 'genre': genre, 
                             'page': page + 1, 'sort': sort},
                            Addon.get_string(30026))
    else:
        Addon.add_directory({'mode': 'browse', 'genre': 'all'},
                            Addon.get_string(30028))    
        genres = muzu.get_genres()
        for g in genres:
            Addon.add_directory({'mode': 'browse', 'genre': g['id']}, g['name'])    

elif mode == 'jukebox':
    Addon.log(mode)
    mode = 'main'
    dialog = xbmcgui.Dialog()
    jam = dialog.select(Addon.get_string(30038), 
                        [Addon.get_string(30039), Addon.get_string(30040)])
    kb = xbmc.Keyboard('', Addon.get_string(30035), False)
    kb.doModal()
    if (kb.isConfirmed()):
        query = kb.getText()
        if query:
            country = Addon.get_setting('country')
            assets = muzu.jukebox(query, country)
            artist_id = assets['artist_ids'][0]
            if assets['artists']:
                q = dialog.select(Addon.get_string(30036), 
                                  assets['artists'])
                query = assets['artists'][q]
                artist_id = assets['artist_ids'][q]
                assets = muzu.jukebox(query, country)
            
            if jam:
                assets = muzu.jukebox(query, country, jam=artist_id)
            
            pl = Addon.get_new_playlist(xbmc.PLAYLIST_VIDEO)
            #if Addon.get_setting('hq') == 'true':
            #    hq = True
            #else:
            #    hq = False
            videos = assets.get('videos', False)        
            random.shuffle(videos)
            res_dir = os.path.join(Addon.addon.getAddonInfo('path'), 
                                   'resources')            
            if videos:
                for v in videos:
                    title = unicode('%s: %s' % (v['artist'], v['title']), 'utf8')
                    Addon.add_video_item(str(v['asset_id']),
                                         {'title': title,
                                         },
                                         img=v['thumb'],
                                         playlist=pl)  

                autoPlay()
            else:
                Addon.show_error([Addon.get_string(30037), query])

elif mode == 'chart_up' or mode == 'chart_down':
    Addon.log(mode)
    chart_id = Addon.plugin_queries.get('chart_id', '')
    rev      = mode == 'chart_down'
    mode     = 'chart'    
    if chart_id:
        play   = 'officialtop40/playlists/official-uk-top-40-2013/%s' % chart_id
        videos = muzu.get_playlist(play) 

        if rev:           
            videos.reverse()

        pl      = Addon.get_new_playlist(xbmc.PLAYLIST_VIDEO)
        res_dir = os.path.join(Addon.addon.getAddonInfo('path'), 'resources')
        
        for v in videos:
            Addon.add_video_item(str(v['asset_id']),
                                 {'title': v['title'],},
                                 img=v['thumb'],
                                 playlist=pl)

        autoPlay()

if mode == 'chart':
    Addon.log(mode)
    chart_id  = Addon.plugin_queries.get('chart_id',  '')
    chart_url = Addon.plugin_queries.get('chart_url', '')
    if chart_id and chart_url and mode == 'chart':
        Addon.add_directory({'mode': 'chart_up',   'chart_id' : chart_id}, 'Play 1-40')
        Addon.add_directory({'mode': 'chart_down', 'chart_id' : chart_id}, 'Play 40-1')
        videos = muzu.get_chart(chart_url)        

        for v in videos:
            title = unicode('%s (%s): %s' % (v['pos'], v['last_pos'], v['title']), 'utf8')
            Addon.add_video_item(str(v['asset_id']),
                                 {'title': title,},
                                 img=v['thumb'])            
    else:
        Addon.add_directory({'mode': 'chart', 'chart_id': CHARTS[1][0], 'chart_url': CHARTS[1][1]}, 
                            Addon.get_string(30042))
        Addon.add_directory({'mode': 'chart', 'chart_id': CHARTS[2][0], 'chart_url': CHARTS[2][1]}, 
                            Addon.get_string(30043))
        #Addon.add_directory({'mode': 'chart', 'chart_id': CHARTS[3][0], 'chart_url': CHARTS[3][1]}, 
        #                    Addon.get_string(30044))
        Addon.add_directory({'mode': 'chart', 'chart_id': CHARTS[4][0], 'chart_url': CHARTS[4][1]}, 
                            Addon.get_string(30045))
        Addon.add_directory({'mode': 'chart', 'chart_id': CHARTS[5][0], 'chart_url': CHARTS[5][1]}, 
                            Addon.get_string(30046))

elif mode == 'list_playlists':
    Addon.log(mode) 

    ob = Addon.plugin_queries.get('ob', False)

    if ob and ob == Addon.get_setting('username'):
        country = Addon.get_setting('country')
        playlists = muzu.user_playlists(ob, country)
        for p in playlists:           
            label = p['name']
            if p['network']:
                label = label + ' (%s)' % p['network']
            Addon.add_directory({'play'     : p['playlist_id'],
                                 #'network'  : p['network_id'], 
                                 'mode'     : 'user_playlist',
                                 'name'     : p['name'],
                                 'username' : ob}, 
                                 label)
    elif ob:
        country = Addon.get_setting('country')
        playlists = muzu.list_playlists(ob, country)
        for p in playlists:
            label = p['name']
            if p['network']:
                label = label + ' (%s)' % p['network']
            Addon.add_directory({'play': p['playlist_id'],
                                 'network': p['network_id'], 
                                 'mode': 'playlist'}, 
                                 label)
    else:
        mode = 'toplevel_playlist'

if mode == 'toplevel_playlist':
    Addon.log(mode)

    username = Addon.get_setting('username')

    if username:
        Addon.add_directory({'mode': 'list_playlists', 'ob': username}, username)

    country     = Addon.get_setting('country')
    playlists   = muzu.list_toplevel_playlists(country)
    total_items = len(playlists)
   
    for p in playlists:
        label = Addon.unescape(p['name'])
        thumb = p['thumb']
        Addon.add_directory({'play': p['playlist_id'],
                                 'network': p['network'], 
                                 'mode': 'playlist'}, 
                                 label, thumb, total_items=total_items)

elif mode == 'channels':
    Addon.log(mode)

    network_id  = Addon.plugin_queries.get('network_id', False)    
    page        = int(Addon.plugin_queries.get('page', 0))
    sort        = Addon.plugin_queries.get('sort', False)

    if network_id:
        playlists = muzu.list_playlists_by_network(network_id, page)
        for p in playlists:
            try:
                #Addon.add_directory({'play': p['id'], 'network': network_id,
                #                     'mode': 'playlist'},
                #                    p['name'], p['thumb'])
                Addon.add_video_item(p['id'], {'title': p['name']}, img=p['thumb'])
            except:
               pass

        Addon.add_directory({'mode': mode, 'network_id': network_id, 
                                 'page': page + 1, 'sort': sort},
                                Addon.get_string(30026))
    else:        
        #page = int(Addon.plugin_queries.get('page', 0))
        genre = Addon.plugin_queries.get('genre', '')
        #sort = Addon.plugin_queries.get('sort', False)
        country = Addon.get_setting('country')

        if genre:
            if not sort:
                sort = int(Addon.get_setting('sort'))
                if sort == 2:
                    dialog = xbmcgui.Dialog()
                    sort = dialog.select(Addon.get_string(30029),
                                         [Addon.get_string(30030),
                                          Addon.get_string(30031)])#,
                                          #Addon.get_string(30032)])
                sort = ['views', 'recent', 'alpha'][sort]
            networks = muzu.browse_networks(genre, sort, page, country=country)
            for n in networks:
                title = '%s (%s videos)' % (n['title'], n['num_vids'])
                title = Addon.unescape(title)
                Addon.add_directory({'mode': 'channels', 
                                     'network_id': n['network_id']},
                                    title, 
                                    img=n['thumb'])
            Addon.add_directory({'mode': mode, 'genre': genre, 
                                 'page': page + 1, 'sort': sort},
                                Addon.get_string(30026))
        else:
            Addon.add_directory({'mode': 'channels', 'genre': 'all'},
                                Addon.get_string(30028))    
            genres = muzu.get_genres()
            for g in genres:
                Addon.add_directory({'mode': 'channels', 'genre': g['id']}, 
                                    g['name'])    

    
elif mode == 'search':
    Addon.log(mode)
    kb = xbmc.Keyboard('', Addon.get_string(30027), False)
    kb.doModal()
    if (kb.isConfirmed()):
        query = kb.getText()
        if query:
            videos = muzu.search(query, Addon.get_setting('country'))
            if videos == None:
                videos = []
                mode = 'error'

            for v in videos:
                title = '%s: %s' % (v['artist'], v['title'])
                Addon.add_video_item(str(v['asset_id']),
                                     {'title': title,
                                      'plot': v['description'],
                                      'duration': str(v['duration']),
                                     },
                                     img=v['thumb'])
        else:
            mode = 'main'
    else:
        mode = 'main'

elif mode == 'new_releases_all':
    Addon.log(mode)

    network_id = 'newreleases/'
    mode       = 'new_releases'
    page       = int(Addon.plugin_queries.get('page', 0))
    sort       = Addon.plugin_queries.get('sort', False)

    if network_id: 
        playlists = muzu.list_playlists_by_network(network_id, page)


        pl      = Addon.get_new_playlist(xbmc.PLAYLIST_VIDEO)
        res_dir = os.path.join(Addon.addon.getAddonInfo('path'), 'resources')

        for p in playlists:
            Addon.add_video_item(p['id'], {'title': p['name']}, img=p['thumb'], playlist=pl)
            
        autoPlay()
        
if mode == 'new_releases':
    Addon.log(mode)

    network_id = 'newreleases/'
    page       = int(Addon.plugin_queries.get('page', 0))
    sort       = Addon.plugin_queries.get('sort', False)

    if network_id: 
        #Addon.add_directory({'mode': 'new_releases_all', 'page' : page}, 'Play All')  
        playlists = muzu.list_playlists_by_network(network_id, page)
        for p in playlists:
            try:      
                title = p['name']      
                if title.startswith('Watch '):
                    title = title[6:]
                Addon.add_video_item(p['id'], {'title': title}, img=p['thumb'])                
            except:
               pass

        Addon.add_directory({'mode': mode, 'network_id': network_id, 
                                 'page': page + 1, 'sort': sort},
                                Addon.get_string(30026))

if mode == 'main':
    Addon.log(mode)
    Addon.add_directory({'mode': 'browse'},         Addon.get_string(30000))
    Addon.add_directory({'mode': 'new_releases'},   'New Releases')
    Addon.add_directory({'mode': 'jukebox'},        Addon.get_string(30034))
    Addon.add_directory({'mode': 'chart'},          Addon.get_string(30041))
    Addon.add_directory({'mode': 'list_playlists'}, Addon.get_string(30047))
    Addon.add_directory({'mode': 'channels'},       Addon.get_string(30052))
    Addon.add_directory({'mode': 'search'},         Addon.get_string(30027))


try:
    Addon.end_of_directory()
except:
    pass
      

