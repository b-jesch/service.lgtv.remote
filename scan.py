import sys
from resources.lib import interface
from resources.lib.tools import *

host = None if ADDON.getSetting('lg_host') == '' else ADDON.getSetting('lg_host')
port = 8080 if ADDON.getSetting('lg_port') == '' else int(ADDON.getSetting('lg_port'))
try:
    if sys.argv[1] == 'scan':
        notifyLog("Scanning for LG Smart TV Devices...", level=xbmc.LOGDEBUG)
        Interface = interface.Interface(host=host, port=port, protocol=None)
        notifyLog('Device (IP %s protocol %s) found' % (Interface.host, Interface.protocol), level=xbmc.LOGDEBUG)
        #
        # input pairing key if not exists
        #
        pairing_key = None if ADDON.getSetting('lg_pairing_key') == '' else ADDON.getSetting('lg_pairing_key')
        if pairing_key is None: pairing_key = keyboard('', LS(30030))

        _conn = Interface.get_session_id()
        if _conn:
            notifyLog('Session with ID %s established' % Interface.session_id, level=xbmc.LOGDEBUG)
            # we are ready

            ADDON.setSetting('lg_host', Interface.host)
            ADDON.setSetting('lg_protocol', Interface.protocol.upper())
            ADDON.setSetting('lg_pairing_key', pairing_key)
            dialogOSD(LS(30031) % (Interface.host, pairing_key))
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
    dialogOSD(LS(30053) % host)
except IndexError:
    notifyLog('Calling this script outside of setup not allowed', xbmc.LOGERROR)
    dialogOSD(LS(30055))
