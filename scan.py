import sys
from resources.lib import interface
from resources.lib.tools import *

try:
    if sys.argv[1] == 'scan':
        notifyLog("Scanning for LG Smart TV Devices...", level=xbmc.LOGDEBUG)

        _host = None if ADDON.getSetting('lg_host') == '' else ADDON.getSetting('lg_host')
        _port = 8080 if ADDON.getSetting('lg_port') == '' else int(ADDON.getSetting('lg_port'))
        Remote = interface.Interface(host=_host, port=_port, protocol=None)
        _host = Remote.host
        _protocol = Remote._protocol
        notifyLog('Device (IP %s protocol %s) found' % (_host, _protocol.upper()), level=xbmc.LOGDEBUG)
        #
        # input pairing key if not exists
        #
        _pairing_key = None if ADDON.getSetting('lg_pairing_key') == '' else ADDON.getSetting('lg_pairing_key')
        if _pairing_key is None:
            kb = xbmc.Keyboard('', LS(30030))
            kb.doModal()
            if kb.isConfirmed() and kb.getText() != '':  _pairing_key = kb.getText()

        _conn = Remote.get_session_id(_pairing_key)
        if _conn:
            notifyLog('Session with ID %s established' % (Remote.session_id), level=xbmc.LOGDEBUG)
            # we are ready

            ADDON.setSetting('lg_host', _host)
            ADDON.setSetting('lg_protocol', _protocol.upper())
            ADDON.setSetting('lg_pairing_key', _pairing_key)
            if dialogYesNo(LS(30031) % (_host, _protocol.upper())):
                notifyLog('Restart Application', level=xbmc.LOGDEBUG)
                xbmc.executebuiltin('RestartApp')
            else:
                notifyLog('User decided not to restart application...', level=xbmc.LOGDEBUG)
        else:
            notifyLog('Session not established. Try again.', xbmc.LOGERROR)
            dialogOSD(LS(30032))

except interface.Interface.LGinNetworkNotFoundException:
    notifyLog('LG Devices not found in network.', level=xbmc.LOGERROR)
    dialogOSD( LS(30050))
except interface.Interface.LGProtocolWebOSException:
    notifyLog('Device use WebOS on port 3000. Not supported.', level=xbmc.LOGERROR)
    dialogOSD(LS(30051))
except interface.Interface.LGProtocolNotAcceptedException:
    notifyLog('Protocol not supported.', level=xbmc.LOGERROR)
    dialogOSD(LS(30052))
except interface.Interface.NoConnectionToHostException:
    notifyLog('No connection to host.', level=xbmc.LOGERROR)
    dialogOSD(LS(30053) % (_host))
except IndexError:
    notifyLog('Calling this script outside of setup not allowed', xbmc.LOGERROR)
    dialogOSD(LS(30055))
