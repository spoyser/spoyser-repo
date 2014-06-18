
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

import utils
import subprocess

#-------------------------------------------------------------


def install(silent=False):
    if utils.ADDON.getSetting('OS') == 'Windows':
        return

    cmdLine  = utils.getSudo()
    cmdLine +='apt-get update;'
    cmdLine +='sudo apt-get -y install openvpn;'
    cmdLine +='sudo apt-get -y install psmisc'

    dp = None
    if not silent:
        dp = utils.progress('Installing VPN application', 'Please be patient this may take a few minutes')

    p = subprocess.Popen(cmdLine, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    (stdout, stderr) = p.communicate()

    if silent:
        return

    import xbmc
    xbmc.sleep(100)
    dp.close()

    import path
    success = path.getPath(utils.ADDON.getSetting('OS'), silent=True)

    if success:
        utils.dialogOK('VPN application successfully installed')
    else:
        utils.dialogOK('VPN application installation failed', 'Please try again later')
 
       
if __name__ == '__main__':
    install()
    utils.ADDON.openSettings()