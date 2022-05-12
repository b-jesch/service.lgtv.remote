import json
import re
from resources.lib import interface
from resources.lib.tools import *

# regular expressions for 3d detection (filenames)
# see http://kodi.wiki/view/Advancedsettings.xml#video or
# http://kodi.wiki/view/3D

__pattern3D__ =   '[-. _]3d[-. _]'
__patternSBS__ =  '[-. _]h?sbs[-. _]'
__patternTAB__ =  '[-. _]h?tab[-. _]'

# Key sequences ROAP/HDCP
__mode3DSBS_on__ =     {'roap': ['400', '15', '20'], 'hdcp': ['220', '68', '6', '68']}
__mode3DSBS_off__ =    {'roap': ['400', '20', '400', '14', '20', '400'], 'hdcp': ['220', '68', '220', '68', '7', '68', '220', '68']}
__mode3DTAB_on__ =     {'roap': ['400', '15', '15', '20'], 'hdcp': ['220', '68', '6', '6', '68']}
__mode3DTAB_off__ =    {'roap': ['400', '20', '400', '14', '14', '20', '400'], 'hdcp': ['220', '68', '220', '68', '7', '7', '68', '220', '68']}

__mode3D_on__ = None
__mode3D_off__ = None

WAIT_FOR_MODE_SELECT = 60
WAIT_FOR_NEXT_CONNECT = 30
POLL_INTERVAL = 1


class Monitor(xbmc.Monitor):

    def __init__(self):

        xbmc.Monitor.__init__(self)
        self.settingsChanged = False
        self.abortRequested = False

    def onSettingsChanged(self):
        self.settingsChanged = True

    def onAbortRequested(self):
        self.abortRequested = True


class Service(xbmc.Player):

    def __init__(self):

        xbmc.Player.__init__(self)
        self.Mon = Monitor()
        self.Remote = None
        self.sessionEstablished = False
        self.getSettings()

        self.isPlaying3D = None
        self.mode3D = 'OFF'

    def getSettings(self, init=True):
        if init: self.readSettings()
        if self.lg_host is not None:
            if self.Remote is None:
                try:
                    self.Remote = interface.Interface(self.lg_host, self.lg_port, self.lg_protocol)
                    if not self.Remote.session_id:
                        self.Remote.get_session_id(self.lg_pairing_key)
                        self.sessionEstablished = True
                        notifyLog('Session established. Using session id %s.' % self.Remote.session_id, level=xbmc.LOGDEBUG)
                except self.Remote.NoConnectionToHostException:
                    self.sessionEstablished = False
                    self.Remote = None
                    notifyLog('No connection to host on %s' % (self.lg_host), level=xbmc.LOGERROR)
                    if init: notifyOSD(ADDON_NAME, LS(30054), icon=ICON_ERROR)

    def readSettings(self):
        self.lg_host = ADDON.getSetting('lg_host')
        self.lg_host = None if self.lg_host == '' else self.lg_host
        self.lg_port = ADDON.getSetting('lg_port')
        self.lg_protocol = ADDON.getSetting('lg_protocol')
        self.lg_protocol = None if self.lg_protocol == LS(30017) else self.lg_protocol.lower()
        self.lg_pairing_key = ADDON.getSetting('lg_pairing_key')

        self.lg_key_delay = int(re.match('\d+', ADDON.getSetting('lg_delay')).group())
        self.lg_own_seqs_enabled = True if ADDON.getSetting('use_own_seq').upper() == 'TRUE' else False
        self.lg_seq_3D_on = ' '.join(ADDON.getSetting('lg_3D_on').replace(',', ' ').split()).split()
        self.lg_seq_3D_off = ' '.join(ADDON.getSetting('lg_3D_off').replace(',', ' ').split()).split()

        self.Mon.settingsChanged = False
        notifyLog('Settings reloaded', level=xbmc.LOGDEBUG)

    def getStereoscopicMode(self):
        mode = {"off": 'OFF', "split_vertical": 'SBS', "split_horizontal": 'TAB',
                "row_interleaved": 'INTERLEAVE', "hardware_based": 'HW', "anaglyph_cyan_red": 'CR',
                "anaglyph_green_magenta": 'GM', "monoscopic": 'MONO'}
        query = {
                "jsonrpc": "2.0",
                "method": "GUI.GetProperties",
                "params": {"properties": ["stereoscopicmode"]},
                "id": 1
                }
        _poll = WAIT_FOR_MODE_SELECT
        while _poll > 0:
            try:
                res = json.loads(xbmc.executeJSONRPC(json.dumps(query)))
                if 'result' in res and 'stereoscopicmode' in res['result']:
                    res = res['result']['stereoscopicmode'].get('mode')
                    if self.mode3D != mode[res]:
                        notifyLog('Stereoscopic mode has changed to %s' % (mode[res]))
                        self.mode3D = mode[res]
                        return True
                    _poll -= 1
                    xbmc.sleep(1000)
                else:
                    break
            except SystemExit:
                notifyLog('System will terminate this script, closing it.', level=xbmc.LOGERROR)
                break
        notifyLog('Could not determine steroscopic mode', level=xbmc.LOGERROR)
        return False

    def sendCommand(self, sequence, own_sequence):
        try:
            self.getSettings()
            if self.lg_own_seqs_enabled:
                sequence = own_sequence
                notifyLog('Sending user sequence %s' % (sequence), level=xbmc.LOGDEBUG)

            for code in sequence:
                if self.Remote.session_id is None: self.Remote.get_session_id(self.lg_pairing_key)
                # let smart models time for response ;)
                xbmc.sleep(self.lg_key_delay)
                notifyLog('%s msec delayed, sending keycode %s. Response: %s.' % (self.lg_key_delay, code, self.Remote.handle_key_input(code)), level=xbmc.LOGDEBUG)

        except self.Remote.NoConnectionToHostException:
            self.sessionEstablished = False
            notifyLog('No connection to host on %s' % (self.lg_host), level=xbmc.LOGERROR)

    def onPlayBackStarted(self):
        if self.isPlayingVideo() and self.lg_protocol is not None:
            _file = os.path.basename(self.getPlayingFile())
            if re.search(__pattern3D__, _file, re.IGNORECASE):
                if self.getStereoscopicMode():
                    if self.mode3D == 'SBS': __mode3D_on__ = __mode3DSBS_on__
                    elif self.mode3D == 'TAB': __mode3D_on__ = __mode3DTAB_on__
                    else:
                        return

                notifyLog('Playing \'%s\'' % (_file), level=xbmc.LOGDEBUG)
                notifyLog('sending sequence for 3D %s' % self.mode3D, level=xbmc.LOGDEBUG)
                self.sendCommand(__mode3D_on__[self.lg_protocol], self.lg_seq_3D_on)
                self.isPlaying3D = True

    def onPlayBackStopped(self):
        _currentMode = self.mode3D
        if self.getStereoscopicMode() and self.isPlaying3D and self.mode3D == 'OFF':
            notifyLog('Turn 3D %s mode off' % _currentMode, level=xbmc.LOGDEBUG)
            if _currentMode == 'SBS': __mode3D_off__ = __mode3DSBS_off__
            elif _currentMode == 'TAB': __mode3D_off__ = __mode3DTAB_off__
            else: return

            self.sendCommand(__mode3D_off__[self.lg_protocol], self.lg_seq_3D_off)
            self.isPlaying3D = False

    def onPlayBackEnded(self):
        _currentMode = self.mode3D
        if self.getStereoscopicMode() and self.isPlaying3D and self.mode3D == 'OFF':
            notifyLog('Turn 3D %s mode off' % _currentMode, level=xbmc.LOGDEBUG)
            if _currentMode == 'SBS':  __mode3D_off__ = __mode3DSBS_off__
            elif _currentMode == 'TAB': __mode3D_off__ = __mode3DTAB_off__
            else: return

            self.sendCommand(__mode3D_off__[self.lg_protocol], self.lg_seq_3D_off)
            self.isPlaying3D = False

    def poll(self):
        _host = None if ADDON.getSetting('lg_host') == '' else ADDON.getSetting('lg_host')
        try:
            notifyLog('Service running (%s, %s)' % (self.lg_protocol, self.lg_pairing_key))

            while not self.Mon.abortRequested:
                _cycle = POLL_INTERVAL if self.sessionEstablished else WAIT_FOR_NEXT_CONNECT
                if self.Mon.waitForAbort(_cycle): break
                if self.Mon.settingsChanged: self.readSettings()
                if not self.sessionEstablished: self.getSettings(init=False)

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
        except Exception as e:
            pass


RemoteService = Service()
RemoteService.poll()
del RemoteService
notifyLog('Service finished')
