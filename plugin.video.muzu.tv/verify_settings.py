
import xbmcaddon
import xbmcgui
import urllib2

ADDON = xbmcaddon.Addon(id = 'plugin.video.muzu.tv')

def verify(argv, silent):
    apiKey = ADDON.getSetting('api') 

    dialog = xbmcgui.Dialog()

    if apiKey == '':
        if not silent:
            dialog.ok('MUZU.TV', 'Please ensure API key is set')
        return False

    url = 'http://www.muzu.tv/api/browse?muzuid=%s&l=1&format=xml' % apiKey

    response = urllib2.urlopen(url).read()

    error = 'Invalid MUZU Id' in response

    if silent:
        return not error

    if error:
        dialog.ok('MUZU.TV', 'API key is not valid')
    else:
        dialog.ok('MUZU.TV', 'API key has successfully been verified')

    return not error
        
if __name__ == '__main__':  
    verify(sys.argv, False)
    ADDON.openSettings() 