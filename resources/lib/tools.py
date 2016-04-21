import xbmc
import xbmcgui
import xbmcaddon
import os

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__addonID__ = __addon__.getAddonInfo('id')
__path__ = __addon__.getAddonInfo('path')
__version__ = __addon__.getAddonInfo('version')
__LS__ = __addon__.getLocalizedString

__IconConnected__ = xbmc.translatePath(os.path.join( __path__,'resources', 'media', 'ok.png'))
__IconError__ = xbmc.translatePath(os.path.join( __path__,'resources', 'media', 'fail.png'))
__IconDefault__ = xbmc.translatePath(os.path.join( __path__,'resources', 'media', 'default.png'))

OSD = xbmcgui.Dialog()

def notifyOSD(header, message, icon=__IconDefault__):
    OSD.notification(header.encode('utf-8'), message.encode('utf-8'), icon)

def dialogOSD(message, header=__addonname__):
    OSD.ok(header.encode('utf-8'), message.encode('utf-8'))

def dialogYesNo(message, header=__addonname__):
    return OSD.yesno(header.encode('utf-8'), message.encode('utf-8'))

def notifyLog(message, level=xbmc.LOGNOTICE):
    xbmc.log('[%s %s] %s' % (__addonID__, __version__, message.encode('utf-8')), level)