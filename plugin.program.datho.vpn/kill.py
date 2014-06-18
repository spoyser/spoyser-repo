#
#      Copyright (C) 2014 Datho-Digital
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
import subprocess

def KillVPN(): 
    if os.name == 'nt':
        try:
            si = subprocess.STARTUPINFO
            si.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess._subprocess.SW_HIDE

            ps  = subprocess.Popen('TASKKILL /F /IM openvpn.exe', shell=True, stdout=subprocess.PIPE, startupinfo=None)
            ps.wait()
        except:
            pass
        return

    #LINUX
    try:
        import utils
        cmd = utils.getSudo() + 'killall -9 openvpn'

        ps  = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        ps.wait()
    except:
        pass

