
#       Copyright (C) 2013-
#       Sean Poyser (seanpoyser@gmail.com)
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Progr`am is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#


import xbmcvfs
import os


def exists(filename):
    if xbmcvfs.exists(filename):
        return True
    return os.path.exists(filename)


def isfile(filename):
    if not exists(filename):
        #raise Exception('sfile.isfile error %s does not exists' % filename)
        return False

    import stat
    return stat.S_ISREG(xbmcvfs.Stat(filename).st_mode())
    

def isdir(folder):
    if not exists(folder):
        #raise Exception('sfile.isdir error %s does not exists' % folder)
        return False

    import stat
    return stat.S_ISDIR(xbmcvfs.Stat(folder).st_mode())
   

def file(filename, type):
    return xbmcvfs.File(filename, type)


def size(filename):
    return xbmcvfs.File(filename).size()


def read(filename):
    f = file(filename, 'r')
    content = f.read()
    f.close()
    return content


def write(filename, content):
    if not content:
        return

    f = file(filename, 'w')
    f.write(content)
    f.close()


def readlines(filename):
    lines = read(filename)
    lines = lines.replace('\r', '')
    lines = lines.split('\n')
    return lines


def walk(folder):
    list = xbmcvfs.listdir(folder)
    return folder, list[0], list[1]


def glob(folder):
    import os
    current, dirs, files = walk(folder)
    full = []
    for file in files:
        full.append(os.path.join(current, file))
    return full


def related(filename):
    found  = []
    folder = filename.rsplit(os.sep, 1)[0]
    files  = glob(folder)
    match  = filename.rsplit('.', 1)[0].lower()

    for file in files:
        if file.rsplit('.', 1)[0].lower() == match:
            found.append(file)

    return found


def makedirs(path):
    xbmcvfs.mkdirs(path)


def delete(filename):
    return remove(filename)


def remove(filename):
    if isdir(filename):
        return rmtree(filename)

    return xbmcvfs.delete(filename)


def rmtree(folder):
    import os
    current, dirs, files = walk(folder)

    for file in files:
        remove(os.path.join(current, file))

    for dir in dirs:
        rmtree(os.path.join(current, dir))

    xbmcvfs.rmdir(folder)


def copytree(src, dst):
    import os
    current, dirs, files = walk(src)

    if not exists(dst):
        makedirs(dst)

    for file in files:
        copy(os.path.join(current, file), os.path.join(dst, file))

    for dir in dirs:
        copytree(os.path.join(src, dir), os.path.join(dst, dir))


def copy(src, dst):
    return xbmcvfs.copy(src, dst)


def rename(src, dst):
    if src == dst:
        return

    if not exists(src):
        return

    if isdir(src):
        if src.lower() == dst.lower():
            newSrc = src +'sfile_temp_name'
            rename(src, newSrc)
            src = newSrc
        
        copytree(src, dst)
        rmtree(src)
        return

    return xbmcvfs.rename(src, dst)



def mtime(filename):
    if not exists(filename):
        raise Exception('sfile.mtime error %s does not exists')

    status = xbmcvfs.Stat(filename)
    return status.st_mtime()


def ctime(filename):
    if not exists(filename):
        raise Exception('sfile.ctime error %s does not exists')

    status = xbmcvfs.Stat(filename)
    return status.st_ctime()


def getfolder(path, sep=os.sep):
    path = path.replace('/', sep)
    if path.endswith(sep):
        path += 'filename'

    try:    return path.rsplit(sep, 1)[0]       
    except: return ''


def getfilename(path, sep=os.sep):
    path = path.replace('/', sep)
    try:    return path.rsplit(sep, 1)[-1]
    except: return ''


def removeextension(path):
    try:    return path.rsplit('.', 1)[0]
    except: path


def getextension(path):
    try:    return path.rsplit('.')[-1]
    except: return ''


def isempty(folder):
    current, dirs, files = walk(folder)

    if len(dirs) > 0:
        return False

    if len(files) > 0:
        return False

    return True




#def status(filename):
#    if not exists(filename):
#        raise Exception('sfile.status error %s does not exists' % filename)
#
#    status = xbmcvfs.Stat(filename)
#    return status