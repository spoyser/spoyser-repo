#
#      Copyright (C) 2014 Richard Dean
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

import xbmc
import xbmcaddon
import os
import sfile
import vpn_utils as utils

filename  = 'VPNicity Connect.py'

sfaves = xbmcaddon.Addon('plugin.program.super.favourites')
path   = sfaves.getAddonInfo('profile')
file   = os.path.join(path, 'Plugins', filename)


def vpnConnect():
        try:
            install_file(filename)
        
            passed = (sfile.exists(file))
        
            if passed: 
                utils.log('Installing VPNicity Connect Plugin...PASSED')
            else:
                utils.log('Installing VPNicity Connect Plugin...FAILED')
        
            utils.SetSetting('SFPLUGIN', 'true')
            utils.SetSetting('CONTEXT', 'false')
        
            return passed
        
        except Exception, e:
            utils.log('Installing VPNicity Connect Plugin...EXCEPTION %s' % str(e))
        
        return False


def install_file(filename):
    vpn = utils.HOME
    src = os.path.join(vpn, 'resources', filename)
    
    if not os.path.exists(path):
        sfile.makedirs(path)
    
    sfile.copy(src, file)


if __name__ == '__main__':
    xbmc.executebuiltin('Dialog.Show(busydialog)')
    
    if vpnConnect():
        xbmc.executebuiltin('Dialog.Close(busydialog)')
        utils.dialogOK('VPNicity Connect plug-in installed ', 'into the Super Favourites Gobal Menu', 'Thank you.')
        
    else:
        xbmc.executebuiltin('Dialog.Close(busydialog)')
        utils.dialogOK('VPNicity Connect plug-in failed to install.', 'Ensure you have Super Favourites installed.', 'Thank you.')