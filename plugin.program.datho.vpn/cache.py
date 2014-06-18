
#       Copyright (C) 2013-2014
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

import os
import time
import glob
import urllib2

gCacheDir  = ''
gCacheSize = 100


def SetDir(cacheDir):
    global gCacheDir
    gCacheDir = cacheDir
    if not os.path.isdir(gCacheDir):
        os.makedirs(gCacheDir)


def CheckDir():
    if gCacheDir == '':
        raise Exception('CacheDir not defined')


def GetURLNoCache(url, agent):
    req = urllib2.Request(url)
    req.add_header('User-Agent', agent)

    response = urllib2.urlopen(req)
    html     = response.read()
    response.close()
    return html


def GetURL(url, maxSecs = 0, agent=''): #'Apple-iPhone/'
    CacheTrim()
    
    if url == None:
        return None

    CheckDir()
    if maxSecs > 0:
        #is URL cached?
        timestamp = Timestamp(url)
    if timestamp > 0:
        if (time.time() - timestamp) <= maxSecs:
            return CacheData(url)
			
    data = GetURLNoCache(url, agent)
    CacheAdd(url, data)
    return data


def Timestamp(url):
    cacheKey          = CacheCreateKey(url)
    cacheFileFullPath = os.path.join(gCacheDir, cacheKey)

    if os.path.isfile(cacheFileFullPath):
        return os.path.getmtime(cacheFileFullPath)

    return 0


def CacheData(url):
    cacheKey          = CacheCreateKey(url)
    cacheFileFullPath = os.path.join(gCacheDir, cacheKey)
    theFile           = file(cacheFileFullPath, "r")

    data = theFile.read()
    theFile.close()

    return data


def CacheAdd(url, data):
    cacheKey          = CacheCreateKey(url)
    cacheFileFullPath = os.path.join(gCacheDir, cacheKey)
    theFile           = file(cacheFileFullPath, "w")

    theFile.write(data)
    theFile.close()

    CacheTrim()


def CacheCreateKey(url):
    try:
        from hashlib import md5
        return md5(url).hexdigest()
    except:
        import md5
        return md5.new(url).hexdigest()

        
def CacheTrim():
    files  = glob.glob(os.path.join(gCacheDir, '*'))
    nFiles = len(files)

    try:
        while nFiles > gCacheSize:            
            oldestFile        = GetOldestFile(files)
            cacheFileFullPath = os.path.join(gCacheDir, oldestFile)
 
            while os.path.exists(cacheFileFullPath):
                os.remove(cacheFileFullPath)

            files  = glob.glob(os.path.join(gCacheDir, '*'))
            nFiles = len(files)
    except:
        pass


def GetOldestFile(files):
    if not files:
        return None
    
    now    = time.time()
    oldest = files[0], now - os.path.getctime(files[0])

    for f in files[1:]:
        age = now - os.path.getctime(f)
        if age > oldest[1]:
            oldest = f, age

    return oldest[0]