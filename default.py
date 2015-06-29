import xbmc, xbmcgui, xbmcaddon
from resources.lib import interface

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('id')
__path__ = __addon__.getAddonInfo('path')
__version__ = __addon__.getAddonInfo('version')
__LS__ = __addon__.getLocalizedString

__IconConnected__ = xbmc.translatePath(os.path.join( __path__,'resources', 'media', 'connect.png'))
__IconError__ = xbmc.translatePath(os.path.join( __path__,'resources', 'media', 'error.png'))

PLAYER = xbmc.Player()
OSD = xbmcgui.Dialog()

class switcher(object):

    def __init__(self):
        self.lg_host = __addon__.getSetting('lg_host').lower()
        self.lg_host = None if self.lg_host == 'scan' else self.lg_host
        self.lg_port = __addon__.getSetting('lg_port')
        self.lg_protocol = __addon__.getSetting('lg_protocol').lower()
        self.lg_protocol = None if self.lg_protocol == 'auto detect' else self.lg_protocol
        self.lg_pairing_key = __addon__.getSetting('lg_pairing_key').upper()

        Remote = interface.LGRemote(self.lg_host,self.lg_port, self.lg_protocol)

try:
    if sys.argv[1] == 'scan':
        print "Scanning LG Devices..."
        Remote = interface.LGRemote(host='scan', port=8080, protocol=None)

except IndexError:
    pass