
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

import geturllib


def clean(text):
    text = text.replace('&#8211;', '-')
    text = text.replace('&#8230;', '...')
    text = text.replace('&#215;',  'x')

    text = text.replace('&#8216;', '\'')
    text = text.replace('&#8217;', '\'')
    text = text.replace('&#8220;', '"')
    text = text.replace('&#8221;', '"')
    text = text.replace('&#39;',   '\'')
    text = text.replace('&#038;',  '&')
    text = text.replace('<b>',     '')
    text = text.replace('</b>',    '')
    text = text.replace('&amp;',   '&')
    text = text.replace('\ufeff', '')
    return text


def fixup(text):
    newText    = ''
    ignoreNext = False

    for c in text:
        if ord(c) < 127:
            newText   += c
            ignoreNext = False
        elif ignoreNext:
            ignoreNext = False
        else:
            newText   += ' '
            ignoreNext = True

    newText = newText.strip('/\\')
    return newText


def getHTML(url, useCache = True):
    if useCache:
        html, cached = geturllib.GetURL(url, 86400)
    else:
        html = geturllib.GetURLNoCache(url)

    html  = html.replace('\n', '')
    return html