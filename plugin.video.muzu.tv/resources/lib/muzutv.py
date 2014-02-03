'''
    muzu.tv XBMC Plugin
    Copyright (C) 2011 t0mm0

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
import Addon
import cookielib
import os
import re
import urllib, urllib2
import xbmcgui, sys
import json

try:
    from xml.etree import ElementTree as ET
except:
    try:
        import elementtree.ElementTree as ET
    except:
        import ElementTree as ET
        
class MuzuTv:
    __BASE_URL = 'http://www.muzu.tv'
    __API_KEY  = Addon.get_setting('api')
    __GENRES   = [{'id': 'acoustic', 'name': Addon.get_string(30001)},
                  {'id': 'alternative', 'name': Addon.get_string(30002)},
                  {'id': 'blues', 'name': Addon.get_string(30003)},
                  {'id': 'celtic', 'name': Addon.get_string(30004)},
                  {'id': 'country', 'name': Addon.get_string(30005)},
                  {'id': 'dance', 'name': Addon.get_string(30006)},
                  {'id': 'electronic', 'name': Addon.get_string(30007)},
                  {'id': 'emo', 'name': Addon.get_string(30008)},
                  {'id': 'folk', 'name': Addon.get_string(30009)},
                  {'id': 'gospel', 'name': Addon.get_string(30010)},
                  {'id': 'hardcore', 'name': Addon.get_string(30011)},
                  {'id': 'hiphop', 'name': Addon.get_string(30012)},
                  {'id': 'indie', 'name': Addon.get_string(30013)},
                  {'id': 'jazz', 'name': Addon.get_string(30014)},
                  {'id': 'latin', 'name': Addon.get_string(30015)},
                  {'id': 'metal', 'name': Addon.get_string(30016)},
                  {'id': 'pop', 'name': Addon.get_string(30017)},
                  {'id': 'poppunk', 'name': Addon.get_string(30018)},
                  {'id': 'punk', 'name': Addon.get_string(30019)},
                  {'id': 'reggae', 'name': Addon.get_string(30020)},
                  {'id': 'rnb', 'name': Addon.get_string(30021)},
                  {'id': 'rock', 'name': Addon.get_string(30022)},
                  {'id': 'soul', 'name': Addon.get_string(30023)},
                  {'id': 'world', 'name': Addon.get_string(30024)},
                  {'id': 'other', 'name': Addon.get_string(30025)},                
                 ]

    def __init__(self):
          pass

    def check_API(self):

        if self.__API_KEY != '':
           return

        d = xbmcgui.Dialog()
        d.ok(Addon.get_string(30300),Addon.get_string(30303) + '\n' + Addon.get_string(30304),'','')
        Addon.addon.openSettings(sys.argv[ 0 ])

        self.__API_KEY = Addon.get_setting('api')
                            
    def get_genres(self):
        return self.__GENRES


    def get_chart(self, chart):        
        videos = []

        html = self.__get_html('top-40-charts/%s' % chart)
        #html = self.__get_html('browse/charts/chart/%s' % chart, {'country': 'gb'})
        list = html.split('<li class="top-40-video')

        for item in list:           
            try:
                pos      = int(re.compile('<div class="top-40-position">(.+?)</div>').search(item).groups(1)[0])
                last_pos = '-'  
            except:
                pass        
            try:
                move     =  re.compile('<div class="move-direction">Up <span>(.+?)</span></div>').search(item).groups(1)[0]
                last_pos = pos + int(move)
            except:               
                pass

            try:
                move     =  re.compile('<div class="move-direction">Down <span>(.+?)</span></div>').search(item).groups(1)[0]
                last_pos = pos - int(move)
            except:
                pass

            try:
                video_id = re.compile('<a href="/.+?/.+?/(.+?)/"').search(item).groups(1)[0]
            except:
                video_id = ''

            try:
                thumb = re.compile('src="(.+?)"/').search(item).groups(1)[0]
            except:
                thumb = ''

            if not thumb.startswith('http'):
                thumb = self.__BASE_URL + thumb

            try:
                title = re.compile('<div class="top-40-second-line">(.+?)</div>').search(item).groups(1)[0]
            except:
                title = '' 

            try:
                artist = re.compile('<div class="top-40-top-line">(.+?)</div>').search(item).groups(1)[0]
            except:
                artist = ''  

            title = artist + ' : ' + title         

            try:
                videos.append({'title'   : title,
                               'pos'     : str(pos),
                               'last_pos': str(last_pos),
                               'asset_id': str(video_id),
                               'thumb'   : str(thumb)})
            except:
                pass

        return videos


        
    def jukebox(self, query, country='gb', jam=False):
        assets = {'artists': [], 'artist_ids': [], 'videos': []}
        if jam:
            json = self.__get_html('jukebox/generateMixTape', {'ai': jam})
        else:
            json = self.__get_html('jukebox/findArtistAssets', {'mySearch': query, 
                                                                'country': country})
        if json.startswith('[{"'):
            for a in re.finditer('\{.+?ArtistName":"(.+?)".+?ArtistIdentity":(\d+).+?\}', json):
                name, artist_id = a.groups()
                assets['artists'].append(name)
                assets['artist_ids'].append(artist_id)
        else:
            artist_id = ''
            for s in re.finditer('src="(.+?)".+?contentTitle-(\d+)" value="(.+?)".+?value="(.+?)".+?value="(.+?)"', json, re.DOTALL):
                thumb, asset_id, title, artist, artist_id = s.groups()
                assets['videos'].append({'asset_id': asset_id,
                                         'title': title,
                                         'artist': artist,
                                         'thumb': thumb})
            assets['artist_ids'].append(artist_id)
        return assets

    def user_playlists(self, username, country='gb'):
        playlists = []
        html = self.__get_html('user/%s/playlists/' % username)
        for p in re.finditer('data-id="(\d+)" data-title="(.*?)" class="myPlaylistSelectItem', html, re.DOTALL):
            playlist_id, name = p.groups()  
            #print "Playlist ID = " + str(playlist_id)
            #print "Name = " + name

            playlists.append({'playlist_id': playlist_id,
                             'network_id': username,
                             'name': unicode(name, 'utf8'),
                             'network': '',
                             'thumb': ''})

        return playlists

    def list_toplevel_playlists(self, country = 'gb'):
        playlists = []
        html = self.__get_html('%s/browse-playlists' % country, {})
        html = html.split('<li class="content-item-playlists')

        for item in html:
            try:                
                name = re.compile('title="(.+?)">').search(item).groups(1)[0]
                link = re.compile('href="(.+?)"').search(item).groups(1)[0]
                img  = re.compile('src="(.+?)"').search(item).groups(1)[0]
                playlists.append({'playlist_id':  link,
                                  'network_id': '',
                                  'name': unicode(name, 'utf8'),
                                  'network': '',
                                  'thumb': img})
            except:
                pass

        playlists = playlists[1:]
        return playlists


    def list_playlists(self, category, country='gb'):
        playlists = []
        html = self.__get_html('browse/loadPlaylistsByCategory', {'ob': category, 'country': country})
        for p in re.finditer('data-id="(\d+)" data-network-id="(\d+)".+?title="(.*?)\|(.*?)".+?src="(.+?)"', html, re.DOTALL):
            playlist_id, network_id, name, network, thumb = p.groups()            
            playlists.append({'playlist_id': playlist_id,
                              'network_id': network_id,
                              'name': unicode(name, 'utf8'),
                              'network': unicode(network, 'utf8'),
                              'thumb': thumb})
        return playlists

    def list_playlists_by_network(self, network_id, page = 0):
        playlists    = []
        res_per_page = 30
       
        xml = self.__get_html('%smusic-videos' % network_id, {'vo': str(page*res_per_page) })
        xml = xml.split('MUZU.TV <span>')[1]
        xml = xml.split('<div class="pages">')[0]

        list   = xml.split('<li>')
        nItems = len(list) 

        for i in range(1, nItems):
            item = list[i] 
            
            try:
                name = re.compile('.+?title="(.+?)"').findall(item)[0]
            except:
                name = ''
            
            try:
                pi = re.compile('.+?href="/(.+?)/"').findall(item)[0] 
                pi = pi.rsplit('/', 1)[1]                  
            except:
                pi = ''

            try:
                thumb = re.compile('.+?src="(.+?)"').findall(item)[0]               
            except:
                thumb = ''
          
            playlists.append({'name': name, 'id': pi, 'thumb': thumb})

        return playlists    


    def escape(self, text):
        text = text.replace(' ', '%20')
        return text
    
    def get_userplaylist(self, name, playlist_id, username):
        name   = name.lower()
        name   = self.escape(name)
        videos = []
        html   = self.__get_html('user/%s/playlists/%s/%s/' % (username, name, playlist_id))         

        videos = self.__parse_playlist(html)
        return videos

    
    def get_playlist(self, network_id):
        videos = []

        html = self.__get_html(network_id)

        videos = self.__parse_playlist(html)
        return videos

    
    def search(self, query, country):
        self.check_API()

        videos = []
        xml    = self.__get_html('api/search', {'muzuid': self.__API_KEY, 'mySearch': query, 'country' : country })
        return self.__parse_videos(xml)

    def browse_videos(self, genre, sort, page, res_per_page, country, days=0):
        self.check_API()

        queries = {'muzuid': self.__API_KEY,
                   'of': page * res_per_page,
                   'l': res_per_page,
                   'vd': days,
                   'ob': sort,
                   'country' : country
                   }
        if genre is not 'all':
            queries['g'] = genre
        xml = self.__get_html('api/browse', queries)
        return self.__parse_videos(xml)
            

    def browse_networks(self, genre, sort, page, days=0, country='gb'):
        networks = []
        queries = {'no': page * 32,
                   'vd': days,
                   'ob': sort,
                   'country': country,
                   }
        html = self.__get_html('channels/%s' % genre, queries)
        
        list   = html.split('<li class="browseThumbs">')
        nItems = len(list) 

        for i in range(1, nItems):
            item = list[i]           
            
            title      = re.compile('.+?title="(.+?)"').findall(item)[0]
            thumb      = re.compile('.+?src="(.+?)"').findall(item)[0]
            network_id = re.compile('.+?<a href="/(.+?)"').findall(item)[0]
            num_vids   = re.compile('.+?>(.+?) video').findall(item)[0]

            networks.append({'title': title, 'thumb': thumb, 'network_id': network_id, 'num_vids': num_vids})

        return networks

        
    def resolve_stream(self, asset_id, hq='480p'):       
        resolved = False

        #in case user had old version of muzu addon
        if hq == 'true':
            hq = '720p'
        if hq == 'false':
            hq = '480p'         
        
        vt = int(hq.replace('p', '')) 

        while not resolved: #GJirdtz3eCmA4ubE4zoQ1RXNKU, yDh3wqYwX2fReTr6itNrrbN8yzI
            response = self.__get_html('player/requestVideo', {'viewhash': 'yDh3wqYwX2fReTr6itNrrbN8yzI', 'qv': vt, 'ai' : asset_id})

            jsn = json.loads(response)
            url = jsn['url']
           
            if vt == 240:
                vt = 0
            elif vt == 360:
                vt = 240
            elif vt == 480:
                vt = 360
            elif vt == 720:
                vt = 480
                         
            resolved = (vt == 0) or (not 'invalid' in url) 

            if 'invalidTerritory' in url:
                d = xbmcgui.Dialog()
                d.ok(Addon.get_string(30300),'We\'re Sorry :(','But the selected video cannot be','played due to licensing restrictions.')
                return None

        if 'invalid' in url:            
            return None            

        return url       


    def __parse_videos(self, xml):
        xml = xml.replace('media:',     '')
        xml = xml.replace('muzu:video', 'muzuvideo')
        xml = xml.replace('muzu:info',  'muzuinfo')

        videos  = []
        element = ET.fromstring(xml)

        for video in element.getiterator('item'):
            title       = video.findtext('title').strip()
            description = video.findtext('description').strip()

            thumbnail   = ''
            for t in video.findall('thumbnail'):
                height = int(t.attrib['height'])
                if height >= 100:                    
                    thumbnail = t.attrib['url'].strip()
                    break

            try:
                duration = int(video.find('content').attrib['duration'])
            except:
                duration = 0

            try:
                mv    = video.find('muzuvideo')
                mi    = mv.find('muzuinfo')
                id    = int(mi.attrib['id'])
                genre = mi.attrib['genre']

                artist = ''
                for c in video.findall('credit'):
                    if c.attrib['role'] == 'artist':
                        artist = c.text.strip()
                        break

                videos.append({'duration'   : duration,
                               'asset_id'   : id,
                               'genre'      : genre,
                               'title'      : title,
                               'artist'     : artist,
                               'description': description,
                               'thumb'      : thumbnail,
                               })
            except:
                return None

        return videos


    def __parse_playlist(self, html):
        videos = []
        html = html.split('activePlaylistContentUL')[1]

        list   = html.split('<li ')
        nItems = len(list) 

        for i in range(1, nItems):
            item = list[i] 

            try:
                id = re.compile('data-id="(.+?)"').findall(item)[0]
                title  = re.compile('<span class="trackNumber"></span>(.+?) </h2>').findall(item)[0]
            except:
                id    = None
                title = None

            try:
                artist = re.compile('<span class="artistTitle">(.+?) </span>').findall(item)[0]
            except:
                artist = ''

            try:
                thumb = re.compile('.+?<img.+?src="(.+?)"+.?').findall(item)[0]
            except:
                thumb = ''
       
            if id:
                videos.append({'duration': 1,
                               'asset_id': int(id),
                               'title': title,
                               'artist': artist,
                               'description' : '',
                               'thumb' : thumb
                               })
        return videos


    def __build_url(self, path, queries={}):
        query = Addon.build_query(queries)
        return '%s/%s?%s' % (self.__BASE_URL, path, query) 

    def __fetch(self, url, form_data=False):
        if form_data:
            Addon.log('posting: %s %s' % (url, str(form_data)))
            req = urllib2.Request(url, form_data)
        else:
            Addon.log('getting: ' + url)
            req = url

        try:
            response = urllib2.urlopen(url)
            return response
        except urllib2.URLError, e:
            Addon.log(str(e), True)
            return False
        
    def __get_html(self, path, queries={}):
        html = False
        url = self.__build_url(path, queries) 

        Addon.log('Fetching URL %s' % url)
        print "********** MUZU.TV **********"
        print '[plugin.video.muzu.tv] Fetching URL %s' % url

        response = self.__fetch(url)
        if response:
            html = response.read()
        else:
            html = False
        
        return html

    def __login(self):
        Addon.log('logging in')
        policy = cookielib.DefaultCookiePolicy(rfc2965=True, strict_rfc2965_unverifiable=False)    
        self.cj = cookielib.MozillaCookieJar(self.cookie_file)
        self.cj.set_policy(policy)

        if os.access(self.cookie_file, os.F_OK):
            self.cj.load(ignore_discard=True)

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        urllib2.install_opener(opener)
        self.cj.clear_session_cookies()
        
        url = self.__build_url('cgi-bin/oc/manage.cgi')
        form_data = urllib.urlencode({'a': 'do_login', 
                                      'force_direct': '0',
                                      'manage_proper': '1',
                                      'input_username': self.user,
                                      'input_password': self.password
                                      })
        response = self.__fetch(self.__LOGIN_URL, form_data)
        self.cj.save(ignore_discard=True)

