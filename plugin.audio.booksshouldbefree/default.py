
#
#      Copyright (C) 2013 Sean Poyser
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

import urllib
import urllib2

import re
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui


ADDONID = 'plugin.audio.booksshouldbefree'
ADDON   = xbmcaddon.Addon(ADDONID)
TITLE   = 'Books Should Be Free'
VERSION = '1.0.0'
URL     = 'http://www.booksshouldbefree.com/'

GENRE       = 100
GENREMENU   = 200
BOOK        = 300
MORE        = 500
SEARCH      = 600
PLAYCHAPTER = 400
PLAYALL     = 700
RESUME      = 800
RESUMEALL   = 900


def CheckVersion():
    prev = ADDON.getSetting('VERSION')
    curr = VERSION

    if prev == curr:
        return

    ADDON.setSetting('VERSION', curr)

    if curr == '1.0.0':
        d = xbmcgui.Dialog()
        d.ok(TITLE + ' - ' + VERSION, 'Welcome to Books Should Be Free', 'Free public domain audiobooks')


def clean(text):
    text = text.replace('&#8211;', '-')
    text = text.replace('&#8217;', '\'')
    text = text.replace('&#8220;', '"')
    text = text.replace('&#8221;', '"')
    text = text.replace('&#39;',   '\'')
    text = text.replace('<b>',     '')
    text = text.replace('</b>',    '')
    return text


def cleanSearch(text):
    text = clean(text)
    text = text.replace('- Books Should Be Free', '')
    text = text.replace('- Books ...',            '')
    return text


def GetHTML(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Apple-iPhone/')
    response = urllib2.urlopen(req)
    html = response.read()
    response.close()
    return html


def Genre(_url, page):
    view    = ADDON.getSetting('VIEW').lower()
    sort    = ADDON.getSetting('SORT').lower()
    results = ADDON.getSetting('RESULTS').lower()

    requestURL = _url

    if requestURL == 'http://www.booksshouldbefree.com/Top_100':
        view = 'title'
        if page > 1:
            requestURL += '/' % str(page)
    else:
        requestURL += '?'

        if view == 'author':
            requestURL += '&view=author'
        if sort == 'alphabetic':
            requestURL += '&sort=alphabet'
        if results != '30':
            requestURL += '&results=%s' % results

        if page > 1:
            requestURL += '&page=%s' % str(page)

    html = GetHTML(requestURL)
    html = html.replace('\n', '')

    if view == 'title':
        GenreTitle(html)
    if view == 'author':
        GenreAuthor(html)

    AddDir('More...', MORE, _url, 'DefaultPlaylist.png', True, page+1)


def GenreAuthor(html):
    authors = html.split('<li data-role="list-divider">')

    reAuthor = 'By: (.+?)</li>'
    reBook   = '<a href="/(.+?)"  class="list-author" rel="external"><img src="/(.+?)" .+?<p class="list-title">(.+?)</p>'

    for item in authors:
        match = re.compile(reAuthor).findall(item)
        if len(match) > 0:
            author = match[0].split(' <font')[0]
            author = clean(author)
            match  = re.compile(reBook).findall(item)
            for url, image, title in match:
                url    = clean(url)
                image  = clean(image)
                title  = clean(title)
                AddBook(title, author, URL+url, image)
            
             

    
def GenreTitle(html):
    match = re.compile('<li class="list-li"><a href="/(.+?)" class="list-link" rel="external"><img src="/(.+?)".+?<font class="title">(.+?)</font>.+?<font class="author">(.+?)</font>.+?</li>').findall(html)

    for url, image, title, author in match:
        url    = clean(url)
        image  = clean(image)
        title  = clean(title)
        author = clean(author)
        AddBook(title, author, URL+url, image)



def Book(_url, title, image, author):
    html = GetHTML(_url)
    html = html.replace('\n', '')

    match = re.compile('new Playlist\((.+?)]').findall(html)
    if len(match) < 1:
        AddDir('No Audio Book Available', 0, '', 'DefaultPlaylist.png', True)
        return

    if not author:
        author = ''

    contextMenu = []
    cmd         = 'XBMC.RunPlugin(' + sys.argv[0]
    cmd        += '?mode='  + str(PLAYALL)
    cmd        += '&menu='  + _url + urllib.quote_plus('||' + name + '||' + author + '||' + image)
    cmd        += ')'

    contextMenu.append(('Play all', cmd))
    match = re.compile('name:"(.+?)".+?mp3:"(.+?)"}').findall(match[0])
    for chapter, url in match:
        if 'Chapter' in chapter:
            chapter = 'Chapter' + chapter.split('Chapter')[1]
        AddChapter(url, title, clean(chapter), image, contextMenu)


def PlayAll(url, name, author, image):
    html = GetHTML(url)
    html = html.replace('\n', '')

    from player import Player
    Player(xbmc.PLAYER_CORE_MPLAYER).playAll(url, html, name, author, image, ADDONID)


def PlayChapter(url, name, chapter, image): 
    from player import Player
    Player(xbmc.PLAYER_CORE_MPLAYER).playChapter(url, name, chapter, image, ADDONID)


def GenreMenu(url):
    html = GetHTML(url)
    html = html.split('More Genres')[1]
    html = html.replace('\n', '')
    
    match = re.compile('<a href="/(.+?)" rel="external"><div id="(.+?)" class').findall(html)
    for url, genre in match:
        AddGenre(genre.replace('_', ' '), url)


def Search(page, keyword):
    if not keyword or keyword == '':
        keyword = GetSearch()
    if not keyword or keyword == '':
        return

    nResults = ADDON.getSetting('SEARCH')
    keyword  = urllib.quote_plus(keyword)
    start    = str((page-1) * int(nResults))

    url  = 'http://www.google.com/cse?cx=partner-pub-5879764092668092%3Awdqcfbe9xi9&cof=FORID%3A10&num=' + nResults + '&q=' + keyword + '&nojs=1&start=' + start
    html = GetHTML(url)
    html = html.replace('\n', '')
    main = re.compile('<li>(.+?)</li>').findall(html)
    for item in main:
        match = re.compile('<a class="l" href="(.+?)" onmousedown=.+?target="_top">(.+?)</a>').findall(item)
        for url, title in match:
            title = cleanSearch(title)
            AddBook(title, None, url)

    keyword = urllib.unquote_plus(keyword)
    AddDir('More...', SEARCH, 'url', 'DefaultPlaylist.png', True, page+1, None, keyword)


def GetSearch():
    kb = xbmc.Keyboard('', TITLE, False)
    kb.doModal()
    if not kb.isConfirmed():
        return None

    return kb.getText()

    
def Main():   
    CheckVersion()

    AddResume()
    AddSearch()
    AddGenre('Top Books',   'Top_100')
    AddGenre('Children',    'genre/Children')
    AddGenre('Fiction',     'genre/Fiction')
    AddGenre('Fantasy',     'genre/Fantasy')
    AddGenre('Mystery',     'genre/Mystery')
    AddGenreMenu('More...', 'genre-menu')
    

def AddResume():
    try:
        resume = ADDON.getSetting('RESUME_INFO')
        if resume == '':
            return

        resume = urllib.unquote_plus(resume)
        resume = resume.split('||')

        name  = resume[2]
        mode  = resume[1]
        url   = resume[0]
        image = resume[4]
        extra = resume[3]

        if not ' [I](resume)[/I]' in extra:
            extra += ' [I](resume)[/I]'

        AddDir(name, mode, url, image, isFolder=False, extra=extra)

    except Exception, e:
        print str(e)
        raise


def AddSearch():
    AddDir('Search', SEARCH, 'url', 'DefaultPlaylist.png', True)


def AddGenre(label, url, page=1):
    AddDir(label, GENRE, URL+url, 'DefaultPlaylist.png', True, int(page))


def AddGenreMenu(label, url):
    AddDir(label, GENREMENU, URL+url, 'DefaultPlaylist.png', True)    


def AddBook(title, author, url, image=None):
    if image:
        image = URL+image
    else:
        image = 'DefaultPlaylist.png'
    AddDir(title, BOOK, url, image, True, extra=author) 


def AddChapter(url, title, chapter, image, contextMenu=None):
    AddDir(title, PLAYCHAPTER, url, image, False, extra=chapter, contextMenu=contextMenu)
   

def AddDir(name, mode, url, image, isFolder, page=1, extra=None, keyword=None, contextMenu=None):
    label = name
    if extra:
        label = label + ' - ' + extra

    u  = sys.argv[0] 
    u += '?mode='  + str(mode)
    u += '&url='   + urllib.quote_plus(url)
    u += '&name='  + urllib.quote_plus(name) 
    u += '&image=' + urllib.quote_plus(image) 
    u += '&page='  + str(page) 

    if extra:
        u += '&extra=' + urllib.quote_plus(extra) 

    if keyword:
        u += '&keyword=' + urllib.quote_plus(keyword) 

    liz = xbmcgui.ListItem(label, iconImage=image, thumbnailImage=image)

    if contextMenu:
        liz.addContextMenuItems(contextMenu)

    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = isFolder)



def GetDownloadPath():
    downloadFolder = ADDON.getSetting('RECORD_FOLDER')

    if ADDON.getSetting('ASK_FOLDER') == 'true':
        dialog = xbmcgui.Dialog()
	downloadFolder = dialog.browse(3, 'Record to folder...', 'files', '', False, False, downloadFolder)
	if downloadFolder == '' :
	    return None

    if downloadFolder is '':
        d = xbmcgui.Dialog()
	d.ok(TITLE, '', 'You have not set the default recordings folder.', 'Please update the add-on settings and try again.')
	ADDON.openSettings() 
	downloadFolder = ADDON.getSetting('RECORD_FOLDER')

    if downloadFolder == '' and ADDON.getSetting('ASK_FOLDER') == 'true':
        dialog = xbmcgui.Dialog()
	downloadFolder = dialog.browse(3, 'Save to folder...', 'files', '', False, False, downloadFolder)	

    if downloadFolder == '' :
        return None

    if ADDON.getSetting('ASK_FILENAME') == 'true':
        kb = xbmc.Keyboard(TITLE, 'Record stream as...' )
	kb.doModal()
	if kb.isConfirmed():
	    filename = kb.getText()
	else:
	    return None
    else:
        filename = TITLE

    filename = re.sub('[:\\/*?\<>|"]+', '', filename)
    filename = filename + '.mp3'

    return os.path.join(downloadFolder, filename)


def clearResume():
    ADDON.setSetting('RESUME_INFO',    '')
    ADDON.setSetting('RESUME_CHAPTER', '0')
    ADDON.setSetting('RESUME_TIME',    '0')
    

def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
           params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param


params  = get_params()
mode    = None
url     = None
name    = None
extra   = None
image   = None
page    = None
keyword = None
menu    = None

try:
    mode = int(params['mode'])
except:
    pass

try:
    url = urllib.unquote_plus(params['url'])
except:
    pass

try:
    name = urllib.unquote_plus(params['name'])
except:
    pass

try:
    extra = urllib.unquote_plus(params['extra'])
except:
    pass

try:
    image = urllib.unquote_plus(params['image'])
except:
    pass

try:
    page = int(params['page'])
except:
    pass

try:
    keyword = urllib.unquote_plus(params['keyword'])
except:
    pass

try:
    menu = urllib.unquote_plus(params['menu'])
except:
    pass

#print TITLE
#print sys.argv[2]
#print mode
#print url
#print name
#print extra
#print image
#print page
#print keyword
#print menu


if mode == BOOK:
    Book(url, name, image, extra)

elif mode == PLAYCHAPTER:
    clearResume()
    PlayChapter(url, name, extra, image)

elif mode == GENRE:
    Genre(url, page)

elif mode == MORE:
    Genre(url, page)

elif mode == GENREMENU:
    GenreMenu(url)

elif mode == SEARCH:
    Search(page, keyword)

elif mode == PLAYALL:
    items = menu.split('||')
    clearResume()
    PlayAll(items[0], items[1], items[2], items[3])

elif mode == RESUME:
    PlayChapter(url, name, extra, image)

elif mode == RESUMEALL:
    PlayAll(url, name, extra, image)

else:
    Main()

        
try:
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
except:
    pass
