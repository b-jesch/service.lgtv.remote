import xbmc, xbmcgui, xbmcaddon
import os
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

supported_protocols = {__LS__(30015): '30015', __LS_(30016): '30016'}

def notifyOSD(header, message, icon=__IconDefault__):
    OSD.notification(header.encode('utf-8'), message.encode('utf-8'), icon)

def dialogOSD(message, header=__addonname__):
    OSD.ok(header.encode('utf-8'), message.encode('utf-8'))

def notifyLog(message, level=xbmc.LOGNOTICE):
    xbmc.log('[%s] %s' % (__addonID__, message.encode('utf-8')), level)

class switcher(object):

    def __init__(self):
        self.lg_host = __addon__.getSetting('lg_host')
        self.lg_host = None if self.lg_host == 'scan...' else self.lg_host
        self.lg_port = __addon__.getSetting('lg_port')
        self.lg_protocol = __addon__.getSetting('lg_protocol')
        self.lg_protocol = None if self.lg_protocol == __LS__(30017) else self.lg_protocol.lower()
        self.lg_pairing_key = __addon__.getSetting('lg_pairing_key')

        Remote = interface.LGRemote(self.lg_host, self.lg_port, self.lg_protocol)

try:
    if sys.argv[1] == 'scan':
        notifyLog("Scanning for LG Smart TV Devices...")
        try:
            _host = None if __addon__.getSetting('lg_host').lower() == 'scan' else __addon__.getSetting('lg_host')
            Remote = interface.LGRemote(host=_host, port=8080, protocol=None)
            _host = Remote.host
            _protocol = Remote.protocol
            notifyLog('Device (IP %s protocol %s) found' % (_host, _protocol.upper()))
            #
            # input pairing key:
            kb = xbmc.Keyboard('', __LS__(30020))
            kb.doModal()
            if kb.isConfirmed() and kb.getText() != '':
                _pairing_key = kb.getText()
                _conn = Remote.get_session_id(_pairing_key)
                if _conn:
                    notifyLog('Session with ID %s established' % (Remote.session_id))
                    # we are ready
                    notifyOSD(__LS__(30021) % (_host), __LS__(30022))
                    __addon__.setSetting('lg_host', _host)
                    __addon__.setSetting('lg_protocol', _protocol.upper())
                    __addon__.setSetting('lg_pairing_key', _pairing_key)

        except interface.LGRemote.LGinNetworkNotFoundException:
            notifyLog('LG Devices not found in network.', level=xbmc.LOGERROR)
            dialogOSD( __LS__(30050))
        except interface.LGRemote.LGProtocolIssueException:
            notifyLog('There is an issue with the device protocol.', level=xbmc.LOGERROR)
            dialogOSD(__LS__(30051))
        except interface.LGRemote.LGProtocollNotAcceptedException:
            notifyLog('Protocol not supported.', level=xbmc.LOGERROR)
            dialogOSD(__LS__(30052))
        except interface.LGRemote.NoConnectionToHostException:
            notifyLog('No connection to host.', level=xbmc.LOGERROR)
            dialogOSD(__LS__(30053))
except IndexError:
    pass