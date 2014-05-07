
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

import re
import urllib
import net


def Resolve(html):
    try:    
        html = html.split('.flv',   1)[0]
        html = html.rsplit('src="', 1)[-1]
        url  = html + '.flv'

        url = url.split('"')[0]

        if 'cizgifilmlerizle' in url:
            return DoResolve(url)

        if 'animeuploads' in url:
            return DoResolve(url)
    except:
        pass

    return []


def DoResolve(url):
    ret  = None
    text = ''
    try:        
        theNet = net.Net()

        data = {'fuck_you' : '', 'confirm' : 'Click+Here+to+Watch+Free%21%21'}
        url  = url.replace(' ', '%20')

        theNet.set_user_agent('Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')

        html  = theNet.http_POST(url, data).content
        #match = re.compile('file=(.+?)\'/>').search(html).group(1).split('file=', 1)[1].replace('&provider=http', '')
        #match = re.compile('file=(.+?)&provider=http').search(html).group(1).split('file=', 1)[-1]
        match = re.compile('file=(.+?)&provider=http').search(html).group(1).split('file=', 1)[-1]


        url = urllib.unquote(match)
        url = url.replace(' ', '%20')
        ret = url       
    except:
        text = 'Error Resolving URL'

    return [[ret, text]]

