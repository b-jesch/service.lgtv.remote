import xbmc, xbmcgui, xbmcaddon
from resources.lib import interface

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__addonID__ = __addon__.getAddonInfo('id')
__path__ = __addon__.getAddonInfo('path')
__version__ = __addon__.getAddonInfo('version')
__LS__ = __addon__.getLocalizedString

__IconConnected__ = xbmc.translatePath(os.path.join( __path__,'resources', 'media', 'connect.png'))
__IconError__ = xbmc.translatePath(os.path.join( __path__,'resources', 'media', 'error.png'))
__IconDefault__ = xbmc.translatePath(os.path.join( __path__,'resources', 'media', 'default.png'))

PLAYER = xbmc.Player()
OSD = xbmcgui.Dialog()

def notifyOSD(header, message, icon=__IconDefault__):
    OSD.notification(header.encode('utf-8'), message.encode('utf-8'), icon)

def dialogOSD(header, message):
    OSD.ok(header.encode('utf-8'), message.encode('utf-8'))

def notifyLog(message, level=xbmc.LOGNOTICE):
    xbmc.log('[%s] %s' % (__addonID__, message.encode('utf-8')), level)

class switcher(object):

    def __init__(self):
        self.lg_host = __addon__.getSetting('lg_host').lower()
        self.lg_host = None if self.lg_host == 'scan' else self.lg_host
        self.lg_port = __addon__.getSetting('lg_port')
        self.lg_protocol = __addon__.getSetting('lg_protocol').lower()
        self.lg_protocol = None if self.lg_protocol == 'auto detect' else self.lg_protocol
        self.lg_pairing_key = __addon__.getSetting('lg_pairing_key')

        Remote = interface.LGRemote(self.lg_host,self.lg_port, self.lg_protocol)

try:
    if sys.argv[1] == 'scan':
        notifyLog("Scanning for LG Devices...")
        try:
            Remote = interface.LGRemote(host=None, port=8080, protocol=None)
        except interface.LGRemote.LGinNetworkNotFoundException:
            notifyLog('LG Devices not found in network.'
                      '')
            dialogOSD(__addonname__, __LS__(30050))

except IndexError:
    pass