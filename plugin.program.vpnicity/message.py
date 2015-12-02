#
#      Copyright (C) 2015 Sean Poyser
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

import xbmcgui

import vpn_utils as utils

import urllib2
import json
import datetime


URL = 'https://on-tapp.tv/wp-content/uploads/resources/vpnmessage.txt'

def parseDate(dateString):
    try:
        return datetime.datetime.strptime(dateString, '%d/%m/%Y')
    except Exception, e:
        utils.log('Error in parseDate %s' % str(dateString))
        utils.log(e)
    return datetime.datetime.now()


def check():
    try:
        return _check()
    except Exception, e:
        utils.log('Error in message.check %s' % str(e))
        return False


def _check():
    response = urllib2.urlopen(URL).read()

    utils.log('Response in message._check %s' % str(response))

    response = json.loads(u"" + (response))

    try:
        currentID = utils.GetSetting('messageID')
        currentID = float(currentID)
    except Exception, e:
        print str(e)
        currentID = 0

    newID = float(response['ID'])

    if newID <= currentID:
        return False

    utils.SetSetting('messageID', str(newID))

    live    = parseDate(response['Live'])
    expires = parseDate(response['Expires'])

    now = datetime.datetime.now()

    if live > now:
        return False

    if now > expires:
        return False

    try:    title = response['Title']
    except: title = getString(1)

    try:    line1 = response['Line1']
    except: line1 = ''

    try:    line2 = response['Line2']
    except: line2 = ''

    try:    line3 = response['Line3']
    except: line3 = ''    

    utils.log('Displaying announcement %s' % str(newID))
    utils.log(title)
    utils.log(line1)
    utils.log(line2)
    utils.log(line3)

    dlg = xbmcgui.Dialog()
    dlg.ok(title, line1, line2, line3)
    return True