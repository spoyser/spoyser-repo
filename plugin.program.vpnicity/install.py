#
#       Copyright (C) 2014
#       Sean Poyser (seanpoyser@gmail.com) and Richard Dean (write2dixie@gmail.com)
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
import path
import subprocess

#-------------------------------------------------------------


def install(silent=False):
    if utils.ADDON.getSetting('OS') == 'Windows':
        return
    
    if utils.ADDON.getSetting('OS') == 'MacOS':
        installMacOS()
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

    success = path.getPath(utils.ADDON.getSetting('OS'), silent=True)

    if success:
        utils.dialogOK('VPN application successfully installed')
    else:
        utils.dialogOK('VPN application installation failed', 'Please try again later')


def installMacOS():
    import download
    import extract
    import stat
    
    url    = 'http://www.on-tapp.tv/wp-content/vpn/openvpn-macos-2.3.4.zip'
    bindir = xbmc.translatePath('special://profile/addon_data/plugin.program.vpnicity/macos/sbin/')
    dest   = os.path.join(bindir, 'openvpn-macos.zip')
    macbin = os.path.join(bindir, 'openvpn')
    
    try:
        os.makedirs(bindir)
    except:
        pass

    download.download(url, dest)
    extract.all(dest, bindir)
    
    st = os.stat(macbin)
    os.chmod(macbin, st.st_mode | stat.S_IEXEC)
    
    try:
        os.remove(dest)
    except:
        pass
        
    success = path.getPath(utils.ADDON.getSetting('OS'), silent=True)

    if success:
        utils.dialogOK('VPN application successfully installed')
    else:
        utils.dialogOK('VPN application installation failed', 'Please try again later')


if __name__ == '__main__':
    install()
    utils.ADDON.openSettings()