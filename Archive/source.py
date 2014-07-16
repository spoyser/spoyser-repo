#
#      Copyright (C) 2013 Tommy Winther
#      http://tommy.winther.nu
#
#  This Program is free software; you can redistribute it and/or modifye
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
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import StringIO
import os
import threading
import datetime
import time
import urllib2
import urllib

from xml.etree import ElementTree

import buggalo
import xbmcaddon
import xbmcplugin
from strings import *
import xbmc
import xbmcgui
import xbmcvfs
import sqlite3

import dixie

from program import Channel
from program import Program

SOURCE     = ADDON.getSetting('source')
DIXIEURL   = ADDON.getSetting('dixie.url').upper()
DIXIELOGOS = ADDON.getSetting('dixie.logo.folder')
GMTOFFSET  = dixie.GetGMTOffset()

datapath   = xbmc.translatePath('special://profile/addon_data/script.tvguidedixie/')
extras     = os.path.join(datapath, 'extras')
logopath   = os.path.join(extras, 'logos')


import tribune
tribune.setCacheDir(os.path.join(datapath, 'cache'))


if len (DIXIELOGOS):
    logos = os.path.join(logopath, DIXIELOGOS)
else:
    logos = None

USE_DB_FILE = True


SETTINGS_TO_CHECK = ['source', 'dixie.url', 'dixie.logo.folder', 'categories.xml']

# channel URL
# http://tvguidedixie.fileburstcdn.com/tvgdatafiles/databases/dixie/chan.xml



def GetDixieUrl():
    return dixie.GetDixieUrl(DIXIEURL)


class SourceException(Exception):
    pass


class SourceUpdateCanceledException(SourceException):
    pass


class SourceNotConfiguredException(SourceException):
    pass


class DatabaseSchemaException(sqlite3.DatabaseError):
    pass


class Database(object):
    SOURCE_DB  = 'source.db'
    PROGRAM_DB = 'program.db'

    def __init__(self, nChannel):
        self.connS = None
        self.connP = None

        self.eventQueue = list()
        self.event = threading.Event()
        self.eventResults = dict()

        self.needChannels = True

        self.categoriesList = None

        self.source = instantiateSource()

        self.updateInProgress = False
        self.updateFailed = False
        self.settingsChanged = None

        buggalo.addExtraData('source', self.source.KEY)
        for key in SETTINGS_TO_CHECK:
           buggalo.addExtraData('setting: %s' % key, ADDON.getSetting(key))

        self.channelList = list()

        profilePath = xbmc.translatePath(ADDON.getAddonInfo('profile'))
        if not os.path.exists(profilePath):
            os.makedirs(profilePath)

        self.sourcePath  = os.path.join(profilePath, Database.SOURCE_DB)
        self.programPath = os.path.join(profilePath, Database.PROGRAM_DB)

        threading.Thread(name='Database Event Loop', target=self.eventLoop).start()


    def eventLoop(self):
        print 'Database.eventLoop() >>>>>>>>>> starting...'
        while True:
            self.event.wait()
            self.event.clear()

            event = self.eventQueue.pop(0)

            command = event[0]
            callback = event[1]

            print 'Database.eventLoop() >>>>>>>>>> processing command: ' + command.__name__

            try:
                result = command(*event[2:])
                self.eventResults[command.__name__] = result

                if callback:
                    if self._initializeS == command:
                        threading.Thread(name='Database callback', target=callback, args=[result]).start()
                    elif self._initializeP == command:
                        threading.Thread(name='Database callback', target=callback, args=[result]).start()
                    else:
                        threading.Thread(name='Database callback', target=callback).start()

                if self._close == command:
                    del self.eventQueue[:]
                    break

            except Exception:
                print 'Database.eventLoop() >>>>>>>>>> exception!'
                buggalo.onExceptionRaised()

        print 'Database.eventLoop() >>>>>>>>>> exiting...'


    def _invokeAndBlockForResult(self, method, *args):
        event = [method, None]
        event.extend(args)
        self.eventQueue.append(event)
        self.event.set()

        while not self.eventResults.has_key(method.__name__):
            time.sleep(0.1)

        result = self.eventResults.get(method.__name__)
        del self.eventResults[method.__name__]
        return result


    def initializeS(self, callback, cancel_requested_callback=None):
        self.eventQueue.append([self._initializeS, callback, cancel_requested_callback])
        self.event.set()


    def initializeP(self, callback, cancel_requested_callback=None):
        self.eventQueue.append([self._initializeP, callback, cancel_requested_callback])
        self.event.set()


    def _initializeS(self, cancel_requested_callback):
        sqlite3.register_adapter(datetime.datetime, self.adapt_datetime)
        sqlite3.register_converter('timestamp', self.convert_datetime)

        self.alreadyTriedUnlinking = False
        while True:
            if cancel_requested_callback is not None and cancel_requested_callback():
                break

            try:
                self.connS = sqlite3.connect(self.sourcePath, detect_types=sqlite3.PARSE_DECLTYPES)
                #self.connS.execute('PRAGMA foreign_keys = ON')
                self.connS.row_factory = sqlite3.Row

                # create and drop dummy table to check if database is locked
                c = self.connS.cursor()
                c.execute('CREATE TABLE IF NOT EXISTS database_lock_check(id TEXT PRIMARY KEY)')
                c.execute('DROP TABLE database_lock_check')
                c.close()

                #self._createTableS()
                #self.settingsChanged = self._wasSettingsChanged(ADDON)
                break

            except sqlite3.OperationalError:
                if cancel_requested_callback is None:
                    xbmc.log('[script.tvguidedixie] Database is locked, bailing out...', xbmc.LOGDEBUG)
                    break
                else:  # ignore 'database is locked'
                    xbmc.log('[script.tvguidedixie] Database is locked, retrying...', xbmc.LOGDEBUG)

            except sqlite3.DatabaseError:
                self.connS = None
                if self.alreadyTriedUnlinking:
                    xbmc.log('[script.tvguidedixie] Database is broken and unlink() failed', xbmc.LOGDEBUG)
                    break
                else:
                    try:
                        os.unlink(self.sourcePath)
                    except OSError:
                        pass
                    self.alreadyTriedUnlinking = True
                    xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), strings(DATABASE_SCHEMA_ERROR_1),
                                        strings(DATABASE_SCHEMA_ERROR_2), strings(DATABASE_SCHEMA_ERROR_3))

        return self.connS is not None


    def _initializeP(self, cancel_requested_callback):
        sqlite3.register_adapter(datetime.datetime, self.adapt_datetime)
        sqlite3.register_converter('timestamp', self.convert_datetime)

        self.alreadyTriedUnlinking = False
        while True:
            if cancel_requested_callback is not None and cancel_requested_callback():
                break

            try:
                self.openP()

                # create and drop dummy table to check if database is locked
                c = self.connP.cursor()
                c.execute('CREATE TABLE IF NOT EXISTS database_lock_check(id TEXT PRIMARY KEY)')
                c.execute('DROP TABLE database_lock_check')
                c.close()

                #self._createTableP()
                self._createTable()
                self.settingsChanged = self._wasSettingsChanged(ADDON)
                break

            except sqlite3.OperationalError:
                if cancel_requested_callback is None:
                    xbmc.log('[script.tvguidedixie] EPG Database is locked, bailing out...', xbmc.LOGDEBUG)
                    break
                else:  # ignore 'database is locked'
                    xbmc.log('[script.tvguidedixie] EPG Database is locked, retrying...', xbmc.LOGDEBUG)

            except sqlite3.DatabaseError:
                self.connP = None
                if self.alreadyTriedUnlinking:
                    xbmc.log('[script.tvguidedixie] EPG Database is broken and unlink() failed', xbmc.LOGDEBUG)
                    break
                else:
                    try:
                        os.unlink(self.programPath)
                    except OSError:
                        pass
                    self.alreadyTriedUnlinking = True
                    xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), strings(DATABASE_SCHEMA_ERROR_1),
                                        strings(DATABASE_SCHEMA_ERROR_2), strings(DATABASE_SCHEMA_ERROR_3))

        return self.connP is not None


    def close(self, callback=None):
        self.eventQueue.append([self._close, callback])
        self.event.set()


    def _close(self):
        self.closeS()
        self.closeP()


    def closeS(self):
        try:
            # rollback any non-commit'ed changes to avoid database lock
            if self.connS:
                self.connS.rollback()
        except sqlite3.OperatiaonalError:
            pass  # no transaction is active

        if self.connS:
            self.connS.close()
            del self.connS


    def closeP(self):
        try:
            # rollback any non-commit'ed changes to avoid database lock
            if self.connP:
                self.connP.rollback()
        except sqlite3.OperatiaonalError:
            pass  # no transaction is active
        if self.connP:
            self.connP.close()
            del self.connP


    def openP(self):
        self.connP = sqlite3.connect(self.programPath, detect_types=sqlite3.PARSE_DECLTYPES)
        #self.connP.execute('PRAGMA foreign_keys = ON')
        self.connP.row_factory = sqlite3.Row
        self.calcUpdateLimit()


    def parseDate(self, dateString):
        try:
            if type(dateString) in [str, unicode]:
                dt = dateString.split('-')
                return datetime.date(int(dt[0]), int(dt[1]) ,int(dt[2]))
        except:
            pass
        return datetime.date(1900, 1, 1)


    def calcUpdateLimit(self):
        self.updateLimit = datetime.date(1900, 1, 1)
        try:
            c = self.connP.cursor()
            c.execute('SELECT date FROM updates WHERE source=?', [self.source.KEY])
            for row in c:
                when = self.parseDate(row['date'])
                if when > self.updateLimit:
                    self.updateLimit = when
        except:
            pass
        c.close()


    def removeProgramDB(self):
        self.closeP()
        try:
            os.remove(self.programPath)
        except Exception, e:
            pass


    def _wasSettingsChanged(self, addon):
        settingsChanged = False
        noRows = True
        count = 0

        c = self.connS.cursor()
        c.execute('SELECT * FROM settings')
        for row in c:
            noRows = False
            key = row['key']
            if SETTINGS_TO_CHECK.count(key):
                count += 1
                if row['value'] != addon.getSetting(key):
                    settingsChanged = True

        if count != len(SETTINGS_TO_CHECK):
            settingsChanged = True

        if settingsChanged or noRows:
            for key in SETTINGS_TO_CHECK:
                value = addon.getSetting(key).decode('utf-8', 'ignore')
                c.execute('INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)', [key, value])
                if not c.rowcount:
                    c.execute('UPDATE settings SET value=? WHERE key=?', [value, key])
            self.connS.commit()

        c.close()
        print 'Settings changed: ' + str(settingsChanged)
        return settingsChanged


    def _isCacheExpired(self, date):
        return self.needChannels
            
        if self.settingsChanged:
            return True

        channelsLastUpdated = datetime.datetime.fromtimestamp(0)
        programsLastUpdated = datetime.datetime.fromtimestamp(0)

        # check if channel data is up-to-date in database
        try:
            c = self.connS.cursor()
            c.execute('SELECT channels_updated FROM sources WHERE id=?', [self.source.KEY])
            row = c.fetchone()
            if not row:
                return True
            channelsLastUpdated = row['channels_updated']
        except TypeError:
            return True
        c.close()

        try:
            dateStr = date.strftime('%Y-%m-%d')
            c = self.connP.cursor()
            c.execute('SELECT programs_updated FROM updates WHERE source=? AND date=?', [self.source.KEY, dateStr])
            row = c.fetchone()
            if row:
                programsLastUpdated = row['programs_updated']
        except:
            pass        
        c.close()

        return self.source.isUpdated(channelsLastUpdated, programsLastUpdated)


    def updateChannelAndProgramListCaches(self, callback, date = datetime.datetime.now(), progress_callback = None, clearExistingProgramList = True):
        self.eventQueue.append([self._updateChannelAndProgramListCaches, callback, date, progress_callback, clearExistingProgramList])
        self.event.set()


    def _updateChannelAndProgramListCaches(self, date, progress_callback, clearExistingProgramList):
        # todo workaround service.py 'forgets' the adapter and convert set in _initialize.. wtf?!
        sqlite3.register_adapter(datetime.datetime, self.adapt_datetime)
        sqlite3.register_converter('timestamp', self.convert_datetime)

        if not self._isCacheExpired(date):
            return

        self.updateInProgress = True
        self.updateFailed = False
        dateStr = date.strftime('%Y-%m-%d')

        cs = self.connS.cursor()
        cp = self.connP.cursor()

        try:
            xbmc.log('[script.tvguidedixie] Updating caches...', xbmc.LOGDEBUG)
            if progress_callback:
                progress_callback(0)

            if self.settingsChanged:
                self.source.doSettingsChanged(cs, cp)
            self.settingsChanged = False # only want to update once due to changed settings


            #if clearExistingProgramList:
            #    cp.execute("DELETE FROM updates WHERE source=?", [self.source.KEY])
            #else:
            #    cp.execute("DELETE FROM updates WHERE source=? AND date=?", [self.source.KEY, dateStr])
            #cp.execute("DELETE FROM updates WHERE source=?", [self.source.KEY])

           
            #updatesId = c.lastrowid
            #cp.execute("DELETE FROM programs WHERE source=?", [self.source.KEY])

            startDates = []

            #clear existing channels
            cs.execute("DELETE FROM channels WHERE source=?", [self.source.KEY])

            imported = imported_channels = imported_programs = 0
            for item in self.source.getDataFromExternal(date, progress_callback):
                imported += 1

                if imported % 10000 == 0:
                    self.connS.commit()

                if isinstance(item, Channel):
                    imported_channels += 1
                    channel = item
                    cs.execute('INSERT OR IGNORE INTO channels(tribuneID, lineup, id, title, categories, logo, stream_url, visible, weight, source) VALUES(?, ?, ?, ?, ?, ?, ?, ?, (CASE ? WHEN -1 THEN (SELECT COALESCE(MAX(weight)+1, 0) FROM channels WHERE source=?) ELSE ? END), ?)', [channel.tribuneID, channel.lineup, channel.id, channel.title, channel.categories, channel.logo, channel.streamUrl, channel.visible, channel.weight, self.source.KEY, channel.weight, self.source.KEY])
                    if not cs.rowcount:
                        cs.execute('UPDATE channels SET tribuneID=?, lineup=?, title=?, categories=?, logo=?, stream_url=?, visible=(CASE ? WHEN -1 THEN visible ELSE ? END), weight=(CASE ? WHEN -1 THEN weight ELSE ? END) WHERE id=? AND source=?',
                            [channel.tribuneID, channel.lineup, channel.title, channel.categories, channel.logo, channel.streamUrl, channel.weight, channel.visible, channel.weight, channel.weight, channel.id, self.source.KEY])

                elif isinstance(item, Program):
                    imported_programs += 1
                    program = item
                    if isinstance(program.channel, Channel):
                        channel = program.channel.id
                    else:
                        channel = program.channel

                    if program.startDate.date() not in startDates:
                        startDates.append(program.startDate.date())
                        
                    #cp.execute('INSERT INTO programs(channel, title, start_date, end_date, description, subTitle, image_large, image_small, source) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    #    [channel, program.title, program.startDate, program.endDate, program.description, program.subTitle, program.imageLarge, program.imageSmall, self.source.KEY])

            # programs updated
            #startDates.sort()
            #startDates = startDates[:-1]
            #for date in startDates:        
            #    dateStr = date.strftime('%Y-%m-%d')
            #    cp.execute("INSERT INTO updates(source, date, programs_updated) VALUES(?, ?, ?)", [self.source.KEY, dateStr, datetime.datetime.now()])

            # channels updated
            cs.execute("UPDATE sources SET channels_updated=? WHERE id=?", [datetime.datetime.now(), self.source.KEY])

            self.connS.commit()
            self.connP.commit()

            if imported_channels == 0:
                self.updateFailed = True
            if imported_programs == 0:
                self.updateFailed = (not USE_DB_FILE)
  
        except SourceUpdateCanceledException:
            # force source update on next load
            cs.execute('UPDATE sources SET channels_updated=? WHERE id=?', [0, self.source.KEY])
            #cp.execute("DELETE FROM updates WHERE source=?", [self.source.KEY]) # cascades and deletes associated programs records
            self.connS.commit()
            self.connP.commit()

        except Exception:
            import traceback as tb
            import sys
            (etype, value, traceback) = sys.exc_info()
            tb.print_exception(etype, value, traceback)

            try:
                self.connS.rollback()
                self.connP.rollback()
            except sqlite3.OperationalError:
                pass # no transaction is active

            try:
                # invalidate cached data
                cs.execute('UPDATE sources SET channels_updated=? WHERE id=?', [0, self.source.KEY])
                self.connS.commit()
                self.connP.commit()
            except sqlite3.OperationalError:
                pass # database is locked

            self.updateFailed = True
        finally:            
            cs.close()
            cp.close()
            update = ADDON.getSetting('updated.channels')
            dixie.SetSetting('current.channels', update)
            #if USE_DB_FILE:
            #    self.fetchProgramDatabase()
            self.updateInProgress = False
            self.needChannels = False


    def getEPGView(self, channelStart, date = datetime.datetime.now(), progress_callback = None, clearExistingProgramList = True, categories = None, nmrChannels=9, cacheOnly=False):

        date  -= GMTOFFSET

        result = self._invokeAndBlockForResult(self._getEPGView, channelStart, date, progress_callback, clearExistingProgramList, categories, nmrChannels, cacheOnly)

        if self.updateFailed:
            raise SourceException('No channels or programs imported')

        return result


    def _getEPGView(self, channelStart, date, progress_callback, clearExistingProgramList, categories, nmrChannels, cacheOnly):
        update = xbmcgui.Window(10000).getProperty('TVDIXIE_UPDATE')
        if len(update) > 0:
            self.removeProgramDB()
            import update
            update.newEPGAvailable()
            self.openP()
            

        self._updateChannelAndProgramListCaches(date, progress_callback, clearExistingProgramList)
        
        channels = self._getChannelList(onlyVisible = True, categories = categories)

        if channelStart < 0:
            channelStart = len(channels) - 1
        elif channelStart > len(channels) - 1:
            channelStart = 0
        channelEnd = channelStart + nmrChannels
        channelsOnPage = channels[channelStart : channelEnd]

        programs = self._getProgramList(channelsOnPage, date, cacheOnly)

        return [channelStart, channelsOnPage, programs]


    def getNextChannel(self, currentChannel):
        channels = self.getChannelList()
        idx = channels.index(currentChannel)
        idx += 1
        if idx > len(channels) - 1:
            idx = 0
        return channels[idx]


    def getPreviousChannel(self, currentChannel):
        channels = self.getChannelList()
        idx = channels.index(currentChannel)
        idx -= 1
        if idx < 0:
            idx = len(channels) - 1
        return channels[idx]


    def saveChannelList(self, callback, channelList):
        self.eventQueue.append([self._saveChannelList, callback, channelList])
        self.event.set()


    def _saveChannelList(self, channelList):
        c = self.connS.cursor()
        for idx, channel in enumerate(channelList):
            c.execute('INSERT OR IGNORE INTO channels(tribuneID, lineup, id, title, categories, logo, stream_url, visible, weight, source) VALUES(?, ?, ?, ?, ?, ?, ?, ?, (CASE ? WHEN -1 THEN (SELECT COALESCE(MAX(weight)+1, 0) FROM channels WHERE source=?) ELSE ? END), ?)', [channel.tribuneID, channel.lineup, channel.id, channel.title,  channel.categories, channel.logo, channel.streamUrl, channel.visible, channel.weight, self.source.KEY, channel.weight, self.source.KEY])
            if not c.rowcount:
                c.execute('UPDATE channels SET tribuneID=?, lineup=?, title=?, categories=?, logo=?, stream_url=?, visible=?, weight=(CASE ? WHEN -1 THEN weight ELSE ?  END) WHERE id=? AND source=?', [channel.tribuneID, channel.lineup, channel.title, channel.categories, channel.logo, channel.streamUrl, channel.visible, channel.weight,  channel.weight, channel.id, self.source.KEY])

        c.execute("UPDATE sources SET channels_updated=? WHERE id=?", [datetime.datetime.now(), self.source.KEY])
        self.channelList = None
        self.connS.commit()


    def getChannelList(self, onlyVisible = True):
        if not self.channelList or not onlyVisible:
            result = self._invokeAndBlockForResult(self._getChannelList, onlyVisible)

            if not onlyVisible:
                return result

            self.channelList = result
        return self.channelList


    def _getChannelList(self, onlyVisible, categories = None):
        if categories and len(categories) > 0:
            return self._getChannelListFilteredByCategory(onlyVisible, categories)
        c = self.connS.cursor()
        channelList = list()
        if onlyVisible:
            c.execute('SELECT * FROM channels WHERE source=? AND visible=? ORDER BY weight', [self.source.KEY, True])
        else:
            c.execute('SELECT * FROM channels WHERE source=? ORDER BY weight', [self.source.KEY])
        for row in c:
            channel = Channel(row['id'], row['title'], row['logo'], row['stream_url'], row['visible'], row['weight'], row['categories'], tribuneID=row['tribuneID'], lineup=row['lineup'])
            channelList.append(channel)
        c.close()
        return channelList


    def _getChannelListFilteredByCategory(self, onlyVisible, categories):
        channelList = list()

        c = self.connS.cursor()
        if onlyVisible:
            c.execute('SELECT * FROM channels WHERE source=? AND visible=? ORDER BY weight', [self.source.KEY, True])
        else:
            c.execute('SELECT * FROM channels WHERE source=? ORDER BY weight', [self.source.KEY])

        for row in c:
            channelCats = row['categories']
            channelCats = channelCats.split('|')
            for category in channelCats:
                if category in categories:
                    channel = Channel(row['id'], row['title'], row['logo'], row['stream_url'], row['visible'], row['weight'], row['categories'], tribuneID=row['tribuneID'], lineup=row['lineup'])      
                    channelList.append(channel)
                    break
        c.close()
        return channelList


    def getCategoriesList(self):
        if not self.categoriesList:
           self.categoriesList = self._invokeAndBlockForResult(self._getCategoriesList)
        return self.categoriesList


    def _getCategoriesList(self):
        c = self.connS.cursor()
        categoriesList = list()
        c.execute('SELECT * FROM channels WHERE source=? ORDER BY categories', [self.source.KEY])

        for row in c:
            categories = row['categories']
            categories = categories.split('|')
            for category in categories:
                if category not in categoriesList:
                    categoriesList.append(category)

        c.close()
        return categoriesList


    def getCurrentProgram(self, channel):
        return self._invokeAndBlockForResult(self._getCurrentProgram, channel)


    def _getCurrentProgram(self, channel):
        program = None
        now = datetime.datetime.now()
        c = self.connP.cursor()
        c.execute('SELECT * FROM programs WHERE channel=? AND source=? AND start_date <= ? AND end_date >= ?', [channel.id, self.source.KEY, now, now])
        row = c.fetchone()
        if row:
            program = Program(channel, row['title'], row['start_date'], row['end_date'], row['description'], row['subTitle'], row['image_large'], row['image_small'])
        c.close()

        return program


    def getNextProgram(self, channel):
        return self._invokeAndBlockForResult(self._getNextProgram, channel)


    def _getNextProgram(self, program):
        nextProgram = None
        c = self.connP.cursor()
        c.execute('SELECT * FROM programs WHERE channel=? AND source=? AND start_date >= ? ORDER BY start_date ASC LIMIT 1', [program.channel.id, self.source.KEY, program.endDate])
        row = c.fetchone()
        if row:
            nextProgram = Program(program.channel, row['title'], row['start_date'], row['end_date'], row['description'], row['subTitle'], row['image_large'], row['image_small'])
        c.close()

        return nextProgram


    def getPreviousProgram(self, channel):
        return self._invokeAndBlockForResult(self._getPreviousProgram, channel)


    def _getPreviousProgram(self, program):
        previousProgram = None
        c = self.connP.cursor()
        c.execute('SELECT * FROM programs WHERE channel=? AND source=? AND end_date <= ? ORDER BY start_date DESC LIMIT 1', [program.channel.id, self.source.KEY, program.startDate])
        row = c.fetchone()
        if row:
            previousProgram = Program(program.channel, row['title'], row['start_date'], row['end_date'], row['description'], row['subTitle'], row['image_large'], row['image_small'])
        c.close()

        return previousProgram


    def _getProgramList(self, channels, startTime, cacheOnly):
        endTime = startTime + datetime.timedelta(hours = 2)
        programList = list()

        channelMap = dict()
        for c in channels:
            if c.id:
                channelMap[c.id] = c

        if not channels:
            return []

        '''
        c = self.connP.cursor()
        strCh = '(\'' + '\',\''.join(channelMap.keys()) + '\')'
        c.execute('SELECT channel, title, start_date, end_date, description, subTitle, image_large, image_small FROM programs WHERE channel IN ' + strCh + ' AND end_date > ? AND start_date < ? AND source = ?', (startTime, endTime, self.source.KEY))
        for row in c:
            program = Program(channelMap[row['channel']], row["title"], row["start_date"], row["end_date"], row["description"], row["subTitle"], row['image_large'], row['image_small'])
            program.notificationScheduled = self._isNotificationRequiredForProgram(program)
            programList.append(program)

        if len(programList) > 0:      
            return programList
        '''

        return self._getTribuneList(channels, startTime, cacheOnly)


    def _getTribuneList(self, channels, startTime, cacheOnly):
        endTime = startTime + datetime.timedelta(hours = 2)

        allPrograms = tribune.getPrograms(channels, startTime, endTime, cacheOnly)
        
        for p in allPrograms:
            p.notificationScheduled = self._isNotificationRequiredForProgram(p)

        return allPrograms


    def setCustomStreamUrl(self, channel, stream_url):
        if stream_url is not None:
            self._invokeAndBlockForResult(self._setCustomStreamUrl, channel, stream_url)
        # no result, but block until operation is done


    def _setCustomStreamUrl(self, channel, stream_url):
        if stream_url is not None:
            c = self.connS.cursor()
            c.execute("DELETE FROM custom_stream_url WHERE channel=?", [channel.id])
            c.execute("INSERT INTO custom_stream_url(channel, stream_url) VALUES(?, ?)", [channel.id, stream_url.decode('utf-8', 'ignore')])
            self.connS.commit()
            c.close()


    def getCustomStreamUrl(self, channel):
        return self._invokeAndBlockForResult(self._getCustomStreamUrl, channel)


    def _getCustomStreamUrl(self, channel):
        c = self.connS.cursor()
        c.execute("SELECT stream_url FROM custom_stream_url WHERE channel=?", [channel.id])
        stream_url = c.fetchone()
        c.close()

        if stream_url:
            return stream_url[0]
        else:
            return None


    def deleteCustomStreamUrl(self, channel):
        self.eventQueue.append([self._deleteCustomStreamUrl, None, channel])
        self.event.set()


    def _deleteCustomStreamUrl(self, channel):
        c = self.connS.cursor()
        c.execute("DELETE FROM custom_stream_url WHERE channel=?", [channel.id])
        self.connS.commit()
        c.close()


    def getStreamUrl(self, channel):
        customStreamUrl = self.getCustomStreamUrl(channel)
        if customStreamUrl:
            customStreamUrl = customStreamUrl.encode('utf-8', 'ignore')
            return customStreamUrl

        elif channel.isPlayable():
            streamUrl = channel.streamUrl.encode('utf-8', 'ignore')
            return streamUrl

        return None


    def adapt_datetime(self, ts):
        # http://docs.python.org/2/library/sqlite3.html#registering-an-adapter-callable
        return time.mktime(ts.timetuple())


    def convert_datetime(self, ts):
        try:
            return datetime.datetime.fromtimestamp(float(ts))
        except ValueError:
            return None


    def _createTable(self):
        self._createTableS()
        self._createTableP()


    def _createTableS(self):
        c = self.connS.cursor()
        try:
            c.execute('SELECT major, minor, patch FROM version')
            (major, minor, patch) = c.fetchone()
            version = [major, minor, patch]
        except sqlite3.OperationalError:
            version = [0, 0, 0]

        try:
            if version < [1, 3, 0]:
                c.execute('CREATE TABLE IF NOT EXISTS custom_stream_url(channel TEXT, stream_url TEXT)')
                c.execute('CREATE TABLE version (major INTEGER, minor INTEGER, patch INTEGER)')
                c.execute('INSERT INTO version(major, minor, patch) VALUES(1, 3, 0)')

                # For caching data
                c.execute('CREATE TABLE sources(id TEXT PRIMARY KEY, channels_updated TIMESTAMP)')
                c.execute('CREATE TABLE updates(id INTEGER PRIMARY KEY, source TEXT, date TEXT, programs_updated TIMESTAMP)')
                c.execute('CREATE TABLE channels(id TEXT, title TEXT, logo TEXT, stream_url TEXT, source TEXT, visible BOOLEAN, weight INTEGER, PRIMARY KEY (id, source), FOREIGN KEY(source) REFERENCES sources(id) ON DELETE CASCADE)')
                c.execute('CREATE TABLE programs(channel TEXT, title TEXT, start_date TIMESTAMP, end_date TIMESTAMP, description TEXT, image_large TEXT, image_small TEXT, source TEXT, updates_id INTEGER, FOREIGN KEY(channel, source) REFERENCES channels(id, source) ON DELETE CASCADE, FOREIGN KEY(updates_id) REFERENCES updates(id) ON DELETE CASCADE)')
                c.execute('CREATE INDEX program_list_idx ON programs(source, channel, start_date, end_date)')
                c.execute('CREATE INDEX start_date_idx ON programs(start_date)')
                c.execute('CREATE INDEX end_date_idx ON programs(end_date)')

                # For active setting
                c.execute('CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT)')

                # For notifications
                c.execute("CREATE TABLE notifications(channel TEXT, program_title TEXT, source TEXT, FOREIGN KEY(channel, source) REFERENCES channels(id, source) ON DELETE CASCADE)")

            if version < [1, 3, 1]:
                # Recreate tables with FOREIGN KEYS as DEFERRABLE INITIALLY DEFERRED
                c.execute('UPDATE version SET major=1, minor=3, patch=1')
                c.execute('DROP TABLE channels')
                c.execute('DROP TABLE programs')
                c.execute('CREATE TABLE channels(id TEXT, title TEXT, logo TEXT, stream_url TEXT, source TEXT, visible BOOLEAN, weight INTEGER, PRIMARY KEY (id, source), FOREIGN KEY(source) REFERENCES sources(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED)')
                c.execute('CREATE TABLE programs(channel TEXT, title TEXT, start_date TIMESTAMP, end_date TIMESTAMP, description TEXT, image_large TEXT, image_small TEXT, source TEXT, updates_id INTEGER, FOREIGN KEY(channel, source) REFERENCES channels(id, source) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED, FOREIGN KEY(updates_id) REFERENCES updates(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED)')
                c.execute('CREATE INDEX program_list_idx ON programs(source, channel, start_date, end_date)')
                c.execute('CREATE INDEX start_date_idx ON programs(start_date)')
                c.execute('CREATE INDEX end_date_idx ON programs(end_date)')

            if version < [1, 4, 0]:
                c.execute('UPDATE version SET major=1, minor=4, patch=0')
                c.execute('DROP TABLE programs')
                c.execute('DROP TABLE updates')
                c.execute("ALTER TABLE channels add column 'categories' 'TEXT'")

            if version < [1, 5, 0]: #addition of TribuneID and Lineup
                c.execute('UPDATE version SET major=1, minor=5, patch=0')
                c.execute("ALTER TABLE channels add column 'tribuneID' 'TEXT'")
                c.execute("ALTER TABLE channels add column 'lineup'    'TEXT'")

            # make sure we have a record in sources for this Source
            c.execute("INSERT OR IGNORE INTO sources(id, channels_updated) VALUES(?, ?)", [self.source.KEY, 0])

            self.connS.commit()
            c.close()

        except sqlite3.OperationalError, ex:
            raise DatabaseSchemaException(ex)


    def _createTableP(self):
        c = self.connP.cursor()
        try:
            c.execute('SELECT major, minor, patch FROM version')
            (major, minor, patch) = c.fetchone()
            version = [major, minor, patch]
        except sqlite3.OperationalError:
            version = [0, 0, 0]

        try:
            if version < [1, 4, 0]:
                c.execute('CREATE TABLE version (major INTEGER, minor INTEGER, patch INTEGER)')
                c.execute('INSERT INTO version(major, minor, patch) VALUES(1, 4, 0)')

                c.execute('CREATE TABLE updates(id INTEGER PRIMARY KEY, source TEXT, date TEXT, programs_updated TIMESTAMP)')

                c.execute('CREATE TABLE programs(channel TEXT, title TEXT, start_date TIMESTAMP, end_date TIMESTAMP, description TEXT, image_large TEXT, image_small TEXT, source TEXT, subTitle TEXT)')

            self.connP.commit()
            c.close()

        except sqlite3.OperationalError, ex:
            raise DatabaseSchemaException(ex)


    def addNotification(self, program):
        self._invokeAndBlockForResult(self._addNotification, program)
        # no result, but block until operation is done


    def _addNotification(self, program):       
        c = self.connS.cursor()
        c.execute("INSERT INTO notifications(channel, program_title, source) VALUES(?, ?, ?)", [program.channel.id, program.title, self.source.KEY])
        self.connS.commit()
        c.close()


    def removeNotification(self, program):
        self._invokeAndBlockForResult(self._removeNotification, program)


    def _removeNotification(self, program):
        c = self.connS.cursor()
        c.execute("DELETE FROM notifications WHERE channel=? AND program_title=? AND source=?", [program.channel.id, program.title, self.source.KEY])
        self.connS.commit()
        c.close()


    def getNotifications(self, daysLimit = 2):
        return self._invokeAndBlockForResult(self._getNotifications, daysLimit)

    def _getNotifications(self, daysLimit):
        start = datetime.datetime.now() - GMTOFFSET
        end   = start + datetime.timedelta(days = daysLimit)
        c     = self.connS.cursor()
        c.execute("SELECT DISTINCT c.title, p.title, p.start_date FROM notifications n, channels c, programs p WHERE n.channel = c.id AND p.channel = c.id AND n.program_title = p.title AND n.source=? AND p.start_date >= ? AND p.end_date <= ?", [self.source.KEY, start, end])
        programs = c.fetchall()
        c.close()

        return programs


    def isNotificationRequiredForProgram(self, program):
        return self._invokeAndBlockForResult(self._isNotificationRequiredForProgram, program)


    def _isNotificationRequiredForProgram(self, program):   
        c = self.connS.cursor()
        c.execute("SELECT 1 FROM notifications WHERE channel=? AND program_title=? AND source=?", [program.channel.id, program.title, self.source.KEY])
        result = c.fetchone()
        c.close()

        return result


    def clearAllNotifications(self):
        self._invokeAndBlockForResult(self._clearAllNotifications)
        # no result, but block until operation is done


    def _clearAllNotifications(self):
        c = self.connS.cursor()
        c.execute('DELETE FROM notifications')
        self.connS.commit()
        c.close()    

    
#--------------------------------------------------------------------------------------------------------------


class Source(object):
    KEY = 'dixie'


    def __init__(self, addon):
        self.logoFolder = None
        if logos:
            if os.path.exists(logos):
                self.logoFolder = logos
        self.KEY += '.' + DIXIEURL
        self.xml = None

        gmt = addon.getSetting('gmtfrom').replace('GMT', '')
        if gmt == '':
            self.offset = 0
        else:
            self.offset = int(gmt)


    def getChannels(self):
        path = ADDON.getAddonInfo('path')
        path = os.path.join(path, 'resources', 'chan.xml')

        f = open(path, 'r')
        xml = f.read();
        f.close

        return xml

        #return self._downloadUrl(GetDixieUrl() + 'chan.xml')


    def getDataFromExternal(self, date, progress_callback = None): 
        categories = self.getCategories()
        xml = 'chan.xml'
        if not self.xml:
            self.xml = self.getChannels()

        io = StringIO.StringIO(self.xml)
        
        context = ElementTree.iterparse(io, events=("start", "end"))
        return parseXMLTV(context, io, len(self.xml), self.logoFolder, progress_callback, self.offset, categories)


    def doSettingsChanged(self, cs, cp):
        return
        # cs.execute('DELETE FROM channels WHERE source=?', [self.KEY])
        #cp.execute('DELETE FROM programs WHERE source=?', [self.KEY])
        #cp.execute("DELETE FROM updates WHERE source=?", [self.KEY])


    def isUpdated(self, channelsLastUpdated, programsLastUpdated):
        zero = datetime.datetime.fromtimestamp(0)
        if channelsLastUpdated is None or channelsLastUpdated == zero:
            return True

        current = ADDON.getSetting('current.channels')
        update  = ADDON.getSetting('updated.channels')

        # print "current = %s" % current
        # print "update  = %s" % update

        return int(current) != int(update)


    def _downloadUrl(self, url):
        u = urllib2.urlopen(url, timeout=30)
        content = u.read()
        u.close()

        return content


    def getCategories(self):        
        cat  = dict()
        path = os.path.join(datapath, 'cats.xml')        
        try:
            if os.path.exists(path):
                f = open(path)
                xml = f.read()
                f.close()
        except: pass
        
        xml = xml.replace('&', '&amp;')
        xml = StringIO.StringIO(xml)
        xml = ElementTree.iterparse(xml, events=("start", "end"))

        for event, elem in xml:
            try:
                if event == 'end':
                   if elem.tag == 'cats':
                       channel  = elem.findtext('channel')
                       category = elem.findtext('category')
                       if channel != '' and category != '':
                           cat[channel] = category
            except:
                pass

        return cat


#---------------------------------------------------------------------------------------------------------

class FileWrapper(object):
    def __init__(self, filename):
        self.vfsfile = xbmcvfs.File(filename)
        self.size = self.vfsfile.size()
        self.bytesRead = 0


    def close(self):
        self.vfsfile.close()


    def read(self, bytes):
        self.bytesRead += bytes
        return self.vfsfile.read(bytes)


    def tell(self):
        return self.bytesRead

#---------------------------------------------------------------------------------------------------------
        

def parseXMLTVDate(dateString, offset):
    if dateString is not None:
        if dateString.find(' ') != -1:
            # remove timezone information
            dateString = dateString[:dateString.find(' ')]
        t = time.strptime(dateString, '%Y%m%d%H%M%S')
        d = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
        d += datetime.timedelta(hours = offset)
        return d
    else:
        return None


def parseXMLTV(context, f, size, logoFolder, progress_callback, offset=0, categories=None):
    event, root = context.next()
    elements_parsed = 0

    for event, elem in context:
        if event == "end":
            result = None
            if elem.tag == "programme":
                channel = elem.get("channel")
                title = elem.findtext("title")
                subTitle = elem.findtext("sub-title")
                category = elem.findtext("category")
                description = elem.findtext("desc")
                mergeTitle = elem.findtext("sub-title")
                if not description:
                    description = subTitle
                if subTitle:
                    title += " " + "- " + mergeTitle
                    
                result = Program(channel, title, parseXMLTVDate(elem.get('start'), offset), parseXMLTVDate(elem.get('stop'), offset), description, elem.findtext("sub-title"))

            elif elem.tag == "channel":
                id        = elem.get("id")
                title     = elem.findtext("display-name")
                tribuneID = elem.findtext("TribuneID")
                lineup    = elem.findtext("Lineup")
                logo      = None

                if logoFolder:
                    folder   = 'special://profile/addon_data/script.tvguidedixie/extras/logos/'
                    logoFile = os.path.join(folder + DIXIELOGOS + '/' + title + '.png')

                    if xbmcvfs.exists(logoFile):
                        logo = logoFile

                result = Channel(id, title, logo, tribuneID=tribuneID, lineup=lineup)

                if categories:
                    try:
                        category = categories[title]
                        result.categories = category
                        #print 'The category for %s is %s' % (title, category)
                    except:
                        pass

                        #print 'Couldn't find %s in the categories' % title

            if result:
                elements_parsed += 1
                if progress_callback and elements_parsed % 500 == 0:
                    if not progress_callback(100.0 / size * f.tell()):
                        raise SourceUpdateCanceledException()
                yield result

        root.clear()
    f.close()
    

def parseCATEGORIES(self, f, context):
    path = os.path.join(datapath, 'cats.xml')
    if os.path.exists(path):
        f = open(path)
        xml = f.read()
        f.close()

    for event, elem in context:
        if event == "end":
            result = None
            if elem.get == "channel":
                categories = elem.findtext("category")
                result = Channel(categories)
            return self.categories
        else:
            return None


def instantiateSource():
    return Source(ADDON)