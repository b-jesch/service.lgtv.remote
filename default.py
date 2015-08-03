import xbmc, xbmcgui, xbmcaddon
import os
import sys
import re
from resources.lib import interface

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
    xbmc.log('[%s] %s' % (__addonID__, message.encode('utf-8')), level)

class service(xbmc.Player):

    def __init__(self):

        xbmc.Player.__init__(self)
        self.Monitor = xbmc.Monitor()
        self.Remote = None
        self.getSettings()

        self.isPlaying3D = None
        self.mode3D = ''

    def getSettings(self):
        self.lg_host = __addon__.getSetting('lg_host')
        self.lg_host = None if self.lg_host == '' else self.lg_host
        self.lg_port = __addon__.getSetting('lg_port')
        self.lg_protocol = __addon__.getSetting('lg_protocol')
        self.lg_protocol = None if self.lg_protocol == __LS__(30017) else self.lg_protocol.lower()
        self.lg_pairing_key = __addon__.getSetting('lg_pairing_key')

        if self.lg_host is not None: self.Remote = interface.Interface(self.lg_host, self.lg_port, self.lg_protocol)

        self.lg_key_delay = int(re.match('\d+', __addon__.getSetting('lg_delay')).group())
        self.lg_own_seqs_enabled = True if __addon__.getSetting('use_own_seq').upper() == 'TRUE' else False
        self.lg_seq_3D_on = ' '.join(__addon__.getSetting('lg_3D_on').replace(',',' ').split()).split()
        self.lg_seq_3D_off = ' '.join(__addon__.getSetting('lg_3D_off').replace(',',' ').split()).split()

    def sendCommand(self, sequence, own_sequence):
        try:
            self.getSettings()
            if self.lg_own_seqs_enabled:
                sequence = own_sequence
                notifyLog('Sending user sequence %s' % (sequence))

            for code in sequence:
                if self.Remote.session_id is None: self.Remote.get_session_id(self.lg_pairing_key)
                notifyLog('Wait %s msec.' % (self.lg_key_delay))
                # let smart models time for response ;)
                xbmc.sleep(self.lg_key_delay)
                notifyLog('Sending keycode %s. Response: %s.' % (code, self.Remote.handle_key_input(code)))

        except self.Remote.NoConnectionToHostException:
            notifyLog('No connection to host on %s' % (self.lg_host), level=xbmc.LOGERROR)

    def onPlayBackStarted(self):
        if self.isPlayingVideo() and self.lg_protocol is not None:
            _file = self.getPlayingFile().decode('utf-8')
            if re.search(__pattern3D__, _file, re.IGNORECASE):
                if re.search(__patternSBS__, _file, re.IGNORECASE):
                    self.mode3D = 'SBS'
                    __mode3D_on__ = __mode3DSBS_on__
                elif re.search(__patternTAB__, _file, re.IGNORECASE):
                    self.mode3D = 'TAB'
                    __mode3D_on__ = __mode3DTAB_on__
                else: return

                notifyLog('Suggest that %s is a 3D %s movie.' % (_file, self.mode3D))
                self.sendCommand(__mode3D_on__[self.lg_protocol], self.lg_seq_3D_on)
                self.isPlaying3D = True
        else:
                if self.isPlaying3D:
                    if self.mode3D == 'SBS':
                        __mode3D_off__ = __mode3DSBS_off__
                    elif self.mode3D == 'TAB':
                        __mode3D_off__ = __mode3DTAB_off__
                    else: return

                    notifyLog('Turn 3D %s mode off' % (self.mode3D))
                    self.sendCommand(__mode3D_off__[self.lg_protocol], self.lg_seq_3D_off)
                    self.isPlaying3D = False
                    self.mode3D = ''

    def onPlayBackStopped(self):
        if self.isPlaying3D:
            notifyLog('Turn 3D %s mode off' % (self.mode3D))
            if self.mode3D == 'SBS':
                __mode3D_off__ = __mode3DSBS_off__
            elif self.mode3D == 'TAB':
                __mode3D_off__ = __mode3DTAB_off__
            else: return

            self.sendCommand(__mode3D_off__[self.lg_protocol], self.lg_seq_3D_off)
            self.isPlaying3D = False
            self.mode3D = ''

    def onPlayBackEnded(self):
        if self.isPlaying3D:
            notifyLog('Turn 3D %s mode off' % (self.mode3D))
            if self.mode3D == 'SBS':
                __mode3D_off__ = __mode3DSBS_off__
            elif self.mode3D == 'TAB':
                __mode3D_off__ = __mode3DTAB_off__
            else: return

            self.sendCommand(__mode3D_off__[self.lg_protocol], self.lg_seq_3D_off)
            self.isPlaying3D = False
            self.mode3D = ''

try:
    if sys.argv[1] == 'scan':
        notifyLog("Scanning for LG Smart TV Devices...")

        _host = None if __addon__.getSetting('lg_host') == '' else __addon__.getSetting('lg_host')
        Remote = interface.Interface(host=_host, port=8080, protocol=None)
        _host = Remote.host
        _protocol = Remote._protocol
        notifyLog('Device (IP %s protocol %s) found' % (_host, _protocol.upper()))
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
            notifyLog('Session with ID %s established' % (Remote.session_id))
            # we are ready

            __addon__.setSetting('lg_host', _host)
            __addon__.setSetting('lg_protocol', _protocol.upper())
            __addon__.setSetting('lg_pairing_key', _pairing_key)
            if dialogYesNo(__LS__(30031) % (_host, _protocol.upper())): xbmc.executebuiltin('RestartApp')
        else:
            notifyLog('Session not established. Try again.', xbmc.LOGERROR)
            dialogOSD(__LS__(30032))

except interface.Interface.LGinNetworkNotFoundException:
    notifyLog('LG Devices not found in network.', level=xbmc.LOGERROR)
    dialogOSD( __LS__(30050))
except interface.Interface.LGProtocolIssueException:
    notifyLog('There is an issue with the device protocol.', level=xbmc.LOGERROR)
    dialogOSD(__LS__(30051))
except interface.Interface.LGProtocollNotAcceptedException:
    notifyLog('Protocol not supported.', level=xbmc.LOGERROR)
    dialogOSD(__LS__(30052))
except interface.Interface.NoConnectionToHostException:
    notifyLog('No connection to host.', level=xbmc.LOGERROR)
    dialogOSD(__LS__(30053) % (_host))
except IndexError:
    Service = service()
    notifyLog('Service established')

    while not xbmc.abortRequested or not Service.Monitor.waitForAbort():
        xbmc.sleep(500)
        if xbmc.abortRequested or Service.Monitor.abortRequested(): break

    notifyLog('Service finished')
