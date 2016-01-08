import xbmc, xbmcaddon
import os
import json
import re
from resources.lib import interface
from resources.lib import tools

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

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__addonID__ = __addon__.getAddonInfo('id')
__path__ = __addon__.getAddonInfo('path')
__version__ = __addon__.getAddonInfo('version')
__LS__ = __addon__.getLocalizedString

__IconConnected__ = xbmc.translatePath(os.path.join( __path__,'resources', 'media', 'ok.png'))
__IconError__ = xbmc.translatePath(os.path.join( __path__,'resources', 'media', 'fail.png'))
__IconDefault__ = xbmc.translatePath(os.path.join( __path__,'resources', 'media', 'default.png'))

class Service(xbmc.Player):

    def __init__(self):

        xbmc.Player.__init__(self)
        self.Monitor = xbmc.Monitor()
        self.Remote = None
        self.getSettings()

        self.isPlaying3D = None
        self.mode3D = 'OFF'
        self.modeHasChanged = False

    def getSettings(self):
        self.lg_host = __addon__.getSetting('lg_host')
        self.lg_host = None if self.lg_host == '' else self.lg_host
        self.lg_port = __addon__.getSetting('lg_port')
        self.lg_protocol = __addon__.getSetting('lg_protocol')
        self.lg_protocol = None if self.lg_protocol == __LS__(30017) else self.lg_protocol.lower()
        self.lg_pairing_key = __addon__.getSetting('lg_pairing_key')

        if self.lg_host is not None:
            if self.Remote is None:
                try:
                    self.Remote = interface.Interface(self.lg_host, self.lg_port, self.lg_protocol)
                    if not self.Remote.session_id:
                        self.Remote.get_session_id(self.lg_pairing_key)
                        tools.notifyLog('Session established. Using session id %s.' % (self.Remote.session_id))
                except self.Remote.NoConnectionToHostException:
                    tools.notifyLog('No connection to host on %s' % (self.lg_host), level=xbmc.LOGERROR)
                    tools.notifyOSD(__addonname__, __LS__(30054), icon=__IconError__)

        self.lg_key_delay = int(re.match('\d+', __addon__.getSetting('lg_delay')).group())
        self.lg_own_seqs_enabled = True if __addon__.getSetting('use_own_seq').upper() == 'TRUE' else False
        self.lg_seq_3D_on = ' '.join(__addon__.getSetting('lg_3D_on').replace(',',' ').split()).split()
        self.lg_seq_3D_off = ' '.join(__addon__.getSetting('lg_3D_off').replace(',',' ').split()).split()

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
            res = json.loads(xbmc.executeJSONRPC(json.dumps(query, encoding='utf-8')))
            if 'result' in res and 'stereoscopicmode' in res['result']:
                res = res['result']['stereoscopicmode'].get('mode')
                if self.mode3D != mode[res]:
                    self.modeHasChanged = True
                    tools.notifyLog('Stereoscopic mode has changed to %s' % (mode[res]))
                    self.mode3D = mode[res]
                    return True
                _poll -= 1
                xbmc.sleep(1000)
            else:
                break
        tools.notifyLog('Could not determine steroscopic mode', level=xbmc.LOGERROR)
        return False

    def sendCommand(self, sequence, own_sequence):
        try:
            self.getSettings()
            if self.lg_own_seqs_enabled:
                sequence = own_sequence
                tools.notifyLog('Sending user sequence %s' % (sequence))

            for code in sequence:
                if self.Remote.session_id is None: self.Remote.get_session_id(self.lg_pairing_key)
                tools.notifyLog('Wait %s msec.' % (self.lg_key_delay))
                # let smart models time for response ;)
                xbmc.sleep(self.lg_key_delay)
                tools.notifyLog('Sending keycode %s. Response: %s.' % (code, self.Remote.handle_key_input(code)))

        except self.Remote.NoConnectionToHostException:
            tools.notifyLog('No connection to host on %s' % (self.lg_host), level=xbmc.LOGERROR)

    def onPlayBackStarted(self):
        if self.isPlayingVideo() and self.lg_protocol is not None:
            _file = self.getPlayingFile().decode('utf-8')
            if re.search(__pattern3D__, _file, re.IGNORECASE):
                if self.getStereoscopicMode():
                    if self.mode3D == 'SBS': __mode3D_on__ = __mode3DSBS_on__
                    elif self.mode3D == 'TAB': __mode3D_on__ = __mode3DTAB_on__
                    else:
                        return

                tools.notifyLog('Playing \'%s\', initiate command sequence for 3D %s' % (_file, self.mode3D))
                self.sendCommand(__mode3D_on__[self.lg_protocol], self.lg_seq_3D_on)
                self.isPlaying3D = True
        '''
        else:
                if self.isPlaying3D:
                    if self.mode3D == 'SBS':
                        __mode3D_off__ = __mode3DSBS_off__
                    elif self.mode3D == 'TAB':
                        __mode3D_off__ = __mode3DTAB_off__
                    else: return

                    tools.notifyLog('Turn 3D %s mode off' % (self.mode3D))
                    self.sendCommand(__mode3D_off__[self.lg_protocol], self.lg_seq_3D_off)
                    self.isPlaying3D = False
                    self.mode3D = ''
        '''
    def onPlayBackStopped(self):
        _currentMode = self.mode3D
        if self.getStereoscopicMode() and self.isPlaying3D and self.mode3D == 'OFF':
            tools.notifyLog('Turn 3D %s mode off' % (_currentMode))
            if _currentMode == 'SBS':
                __mode3D_off__ = __mode3DSBS_off__
            elif _currentMode == 'TAB':
                __mode3D_off__ = __mode3DTAB_off__
            else:
                return

            self.sendCommand(__mode3D_off__[self.lg_protocol], self.lg_seq_3D_off)
            self.isPlaying3D = False

    def onPlayBackEnded(self):
        _currentMode = self.mode3D
        if self.getStereoscopicMode() and self.isPlaying3D and self.mode3D == 'OFF':
            tools.notifyLog('Turn 3D %s mode off' % (_currentMode))
            if _currentMode == 'SBS':
                __mode3D_off__ = __mode3DSBS_off__
            elif _currentMode == 'TAB':
                __mode3D_off__ = __mode3DTAB_off__
            else:
                return

            self.sendCommand(__mode3D_off__[self.lg_protocol], self.lg_seq_3D_off)
            self.isPlaying3D = False

service = None

try:
    _host = None if __addon__.getSetting('lg_host') == '' else __addon__.getSetting('lg_host')
    service = Service()
    tools.notifyLog('Service running')

    while not service.Monitor.abortRequested():
        if service.Monitor.waitForAbort(1000): break

except interface.Interface.LGinNetworkNotFoundException:
    tools.notifyLog('LG Devices not found in network.', level=xbmc.LOGERROR)
    tools.dialogOSD( __LS__(30050))
except interface.Interface.LGProtocolIssueException:
    tools.notifyLog('There is an issue with the device protocol.', level=xbmc.LOGERROR)
    tools.dialogOSD(__LS__(30051))
except interface.Interface.LGProtocollNotAcceptedException:
    tools.notifyLog('Protocol not supported.', level=xbmc.LOGERROR)
    tools.dialogOSD(__LS__(30052))
except interface.Interface.NoConnectionToHostException:
    tools.notifyLog('No connection to host.', level=xbmc.LOGERROR)
    tools.dialogOSD(__LS__(30053) % (_host))
except Exception, e:
    pass

if service is not None: del service
tools.notifyLog('Service finished')