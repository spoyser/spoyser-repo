'''
    Simple XBMC Download Script
    Copyright (C) 2013 Sean Poyser (seanpoyser@gmail.com)

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

import urllib2
import xbmc
import xbmcaddon
import os

def download(url, dest):
    addon  = xbmcaddon.Addon(id='plugin.video.funniermoments')
    title  = 'Funnier Moments'
    script = os.path.join(xbmc.translatePath(addon.getAddonInfo('path')), 'download.py')
    xbmc.executebuiltin('RunScript(%s, %s, %s, %s)' % (script, title, url, dest))


def doDownload(title, url, dest):
    req = urllib2.Request(url)
    req.add_header('Referer', 'http://www.funniermoments.com/')

    f       = open(dest, mode='wb')
    resp    = urllib2.urlopen(req)
    content = int(resp.headers['Content-Length'])
    size    = content / 100
    total   = 0
    notify  = 0
    errors  = 0
    
    while True:
        percent = min(100 * total / content, 100)
        if percent >= notify:
            xbmc.executebuiltin( "XBMC.Notification(%s,%s,%i,%s)" % ( title + ' - Download Progress - ' + str(percent)+'%', dest, 5000,'DefaultFile.png'))
            notify += 10

        chunk = None
        try:
            chunk = resp.read(size)
            if not chunk:            
                f.close()
                return True
        except Exception, e:
            #print str(e)
            chunk   = None
            errors += 1

        if chunk:
            f.write(chunk)            
            total += len(chunk)

        if errors > 10:
            return False

if __name__ == '__main__': 
    if 'download.py' in sys.argv[0]:
        doDownload(sys.argv[1], sys.argv[2] ,sys.argv[3])