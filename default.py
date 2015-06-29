import xbmc, xbmcgui
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