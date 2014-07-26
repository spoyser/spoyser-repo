
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

import os
import xbmc
import re
import HTMLParser

import utils


html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

def escape(text):
    return ''.join(html_escape_table.get(c,c) for c in text)


def unescape(text):
    text = text.replace('&amp;',  '&')
    text = text.replace('&quot;', '"')
    text = text.replace('&apos;', '\'')
    text = text.replace('&gt;',   '>')
    text = text.replace('&lt;',   '<')
    return text


def getFavourites(file):
    xml  = '<favourites></favourites>'
    if os.path.exists(file):  
        fav = open(file , 'r')
        xml = fav.read()
        fav.close()

    items = []

    faves = re.compile('<favourite(.+?)</favourite>').findall(xml)
    for fave in faves:
        fave = fave.replace('&quot;', '&_quot_;')
        fave = fave.replace('\'', '"')
        fave = unescape(fave)

        try:    name = re.compile('name="(.+?)"').findall(fave)[0]
        except: name = ''

        try:    thumb = re.compile('thumb="(.+?)"').findall(fave)[0]
        except: thumb = ''

        try:    cmd   = fave.rsplit('>', 1)[-1]
        except: cmd = ''

        name  = name.replace( '&_quot_;', '"')
        thumb = thumb.replace('&_quot_;', '"')
        cmd   = cmd.replace(  '&_quot_;', '"')


        if isValid(cmd):
            items.append([name, thumb, cmd])

    return items


def writeFavourites(file, faves):
    f = open(file, mode='w')

    f.write('<favourites>')

    for fave in faves:
        try:
            name  = 'name="%s" '  % escape(fave[0])
            thumb = 'thumb="%s">' % escape(fave[1])
            cmd   = escape(fave[2])

            f.write('\n\t<favourite ')
            f.write(name)
            f.write(thumb)
            f.write(cmd)
            f.write('</favourite>')
        except:
            pass

    f.write('\n</favourites>')            
    f.close()


def isValid(cmd):
    if len(cmd) == 0:
        return False

    if 'plugin' in cmd and not utils.verifyPlugin(cmd):
        return False

    if 'RunScript' in cmd and not utils.verifyScript(cmd):
        return False
        
    return True


def updateFave(file, update):
    cmd = update[2]
    fave, index, nFaves = findFave(file, cmd)
   
    removeFave(file, cmd)
    return insertFave(file, update, index)


def findFave(file, cmd):
    faves = getFavourites(file)
    index = -1
    for fave in faves:
        index += 1
        if fave[2] == cmd:            
            return fave, index, len(faves)

    search = os.path.join(xbmc.translatePath(utils.ROOT), 'Search', utils.FILENAME).lower()

    if file.lower() != search:
        return None, -1, 0

    index = -1
    for fave in faves:
        index += 1
        if '[%SF%]' in fave[2]:
            test = fave[2].split('[%SF%]', 1)
            if cmd.startswith(test[0]) and cmd.endswith(test[1]):
                return fave, index, len(faves)

    return None, -1, 0


def insertFave(file, newFave, index):
    copy = []
    faves = getFavourites(file)
    for fave in faves:
        if len(copy) == index:
            copy.append(newFave)
        copy.append(fave)

    if index >= len(copy):
        copy.append(newFave)

    writeFavourites(file, copy)
    return True


def moveFave(src, dst, fave):
    if not copyFave(dst, fave):
        return False
    return removeFave(src, fave[2])


def copyFave(file, copy):
    faves = getFavourites(file)

    #if it is already in there don't add again
    for fave in faves:
        if equals(fave[2], copy[2]):
            return False

    faves.append(copy)
    writeFavourites(file, faves)
    return True


def removeFave(file, cmd):
    copy = []
    faves = getFavourites(file)
    for fave in faves:
        if not equals(fave[2], cmd):
            copy.append(fave)

    if len(copy) == len(faves):
        return False

    writeFavourites(file, copy)
    return True


def shiftFave(file, cmd, up):
    fave, index, nFaves = findFave(file, cmd)
    max = nFaves - 1
    if up:
        index -= 1
        if index < 0:
            index = max
    else: #down
        index += 1
        if index > max:
            index = 0

    removeFave(file, cmd)
    return insertFave(file, fave, index)


def renameFave(file, cmd, newName):
    copy = []
    faves = getFavourites(file)
    for fave in faves:
        if equals(fave[2], cmd):
            fave[0] = newName

        copy.append(fave)

    writeFavourites(file, copy)
    return True


def equals(fave, cmd):
    if fave == cmd:
        return True

    if '[%SF%]' not in fave:
        return False

    test = fave.split('[%SF%]', 1)
    if cmd.startswith(test[0])  and cmd.endswith(test[1]):
        return True

    return False
