import xbmc, xbmcaddon
import os
import sys
from resources.lib import interface
from resources.lib import tools

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__addonID__ = __addon__.getAddonInfo('id')
__path__ = __addon__.getAddonInfo('path')
__version__ = __addon__.getAddonInfo('version')
__LS__ = __addon__.getLocalizedString

__IconConnected__ = xbmc.translatePath(os.path.join( __path__,'resources', 'media', 'ok.png'))
__IconError__ = xbmc.translatePath(os.path.join( __path__,'resources', 'media', 'fail.png'))
__IconDefault__ = xbmc.translatePath(os.path.join( __path__,'resources', 'media', 'default.png'))

try:
    if sys.argv[1] == 'scan':
        tools.notifyLog("Scanning for LG Smart TV Devices...", level=xbmc.LOGDEBUG)

        _host = None if __addon__.getSetting('lg_host') == '' else __addon__.getSetting('lg_host')
        _port = 8080 if __addon__.getSetting('lg_port') == '' else int(__addon__.getSetting('lg_port'))
        Remote = interface.Interface(host=_host, port=_port, protocol=None)
        _host = Remote.host
        _protocol = Remote._protocol
        tools.notifyLog('Device (IP %s protocol %s) found' % (_host, _protocol.upper()), level=xbmc.LOGDEBUG)
        #
        # input pairing key if not exists
        #
        _pairing_key = None if __addon__.getSetting('lg_pairing_key') == '' else __addon__.getSetting('lg_pairing_key')
        if _pairing_key is None:
            kb = xbmc.Keyboard('', __LS__(30030))
            kb.doModal()
            if kb.isConfirmed() and kb.getText() != '':  _pairing_key = kb.getText()

        _conn = Remote.get_session_id(_pairing_key)
        if _conn:
            tools.notifyLog('Session with ID %s established' % (Remote.session_id), level=xbmc.LOGDEBUG)
            # we are ready

            __addon__.setSetting('lg_host', _host)
            __addon__.setSetting('lg_protocol', _protocol.upper())
            __addon__.setSetting('lg_pairing_key', _pairing_key)
            if tools.dialogYesNo(__LS__(30031) % (_host, _protocol.upper())):
                tools.notifyLog('Restart Application', level=xbmc.LOGDEBUG)
                xbmc.executebuiltin('RestartApp')
            else:
                tools.notifyLog('User decided not to restart application...', level=xbmc.LOGDEBUG)
        else:
            tools.notifyLog('Session not established. Try again.', xbmc.LOGERROR)
            tools.dialogOSD(__LS__(30032))

except interface.Interface.LGinNetworkNotFoundException:
    tools.notifyLog('LG Devices not found in network.', level=xbmc.LOGERROR)
    tools.dialogOSD( __LS__(30050))
except interface.Interface.LGProtocolWebOSException:
    tools.notifyLog('Device use WebOS on port 3000. Not supported.', level=xbmc.LOGERROR)
    tools.dialogOSD(__LS__(30051))
except interface.Interface.LGProtocollNotAcceptedException:
    tools.notifyLog('Protocol not supported.', level=xbmc.LOGERROR)
    tools.dialogOSD(__LS__(30052))
except interface.Interface.NoConnectionToHostException:
    tools.notifyLog('No connection to host.', level=xbmc.LOGERROR)
    tools.dialogOSD(__LS__(30053) % (_host))
except IndexError:
    tools.notifyLog('Calling this script outside of setup not allowed', xbmc.LOGERROR)
    tools.dialogOSD(__LS__(30055))