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
__mode3D_on__ =     {'roap': ['400', '20'], 'hdcp': ['220', '68', '68', '68']}
__mode3D_off__ =    {'roap': ['400'], 'hdcp': ['220', '68']}

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__addonID__ = __addon__.getAddonInfo('id')
__path__ = __addon__.getAddonInfo('path')
__version__ = __addon__.getAddonInfo('version')
__LS__ = __addon__.getLocalizedString

__IconConnected__ = xbmc.translatePath(os.path.join( __path__,'resources', 'media', 'connect.png'))
__IconError__ = xbmc.translatePath(os.path.join( __path__,'resources', 'media', 'error.png'))
__IconDefault__ = xbmc.translatePath(os.path.join( __path__,'resources', 'media', 'default.png'))

OSD = xbmcgui.Dialog()

def notifyOSD(header, message, icon=__IconDefault__):
    OSD.notification(header.encode('utf-8'), message.encode('utf-8'), icon)

def dialogOSD(message, header=__addonname__):
    OSD.ok(header.encode('utf-8'), message.encode('utf-8'))

def notifyLog(message, level=xbmc.LOGNOTICE):
    xbmc.log('[%s] %s' % (__addonID__, message.encode('utf-8')), level)

class service(xbmc.Player):

    def __init__(self):

        xbmc.Player.__init__(self)
        self.Monitor = xbmc.Monitor()
        self.Remote = None

        self.getSettings()

    def getSettings(self):
        self.lg_host = __addon__.getSetting('lg_host')
        self.lg_host = None if self.lg_host == '' else self.lg_host
        self.lg_port = __addon__.getSetting('lg_port')
        self.lg_protocol = __addon__.getSetting('lg_protocol')
        self.lg_protocol = None if self.lg_protocol == __LS__(30017) else self.lg_protocol.lower()
        self.lg_pairing_key = __addon__.getSetting('lg_pairing_key')

        self.isPlaying3D = None

        if self.lg_host is not None: self.Remote = interface.Interface(self.lg_host, self.lg_port, self.lg_protocol)

    def sendCommand(self, code):
        if self.lg_host is None: self.getSettings()
        if self.Remote is None: return False
        try:
            if self.Remote.session_id is None: self.Remote.get_session_id(self.lg_pairing_key)
            notifyLog('Sending keycode %s. Response: %s' % (code, self.Remote.handle_key_input(code)))
            xbmc.sleep(500)
        except self.Remote.NoConnectionToHostException:
            notifyLog('No connection to host on %s' % (self.lg_host), level=xbmc.LOGERROR)

    def onPlayBackStarted(self):
        if self.isPlayingVideo():
            _file = self.getPlayingFile()
            if re.search(__pattern3D__, _file).group(0) and (re.search(__patternSBS__, _file).group(0) or re.search(__patternTAB__, _file).group(0)):
                # turn TV into 3D Mode
                if self.lg_protocol:
                    for keycode in __mode3D_on__[self.lg_protocol]: self.sendCommand(keycode)
                    self.isPlaying3D = True
            else:
                if self.isPlaying3D:
                    # turn TV into normal Mode
                    if self.lg_protocol:
                        for keycode in __mode3D_off__[self.lg_protocol]: self.sendCommand(keycode)
                        self.isPlaying3D = False

    def onPlayBackStopped(self):
        if self.isPlaying3D:
            # turn TV into normal Mode
            if self.lg_protocol:
                for keycode in __mode3D_off__[self.lg_protocol]: self.sendCommand(keycode)
                self.isPlaying3D = False

    def onPlayBackEnded(self):
        if self.isPlaying3D:
            # turn TV into normal Mode
            if self.lg_protocol:
                for keycode in __mode3D_off__[self.lg_protocol]: self.sendCommand(keycode)
                self.isPlaying3D = False

try:
    if sys.argv[1] == 'scan':
        notifyLog("Scanning for LG Smart TV Devices...")

        _host = None if __addon__.getSetting('lg_host') == '' else __addon__.getSetting('lg_host')
        Remote = interface.Interface(host=_host, port=8080, protocol=None)
        _host = Remote.host
        _protocol = Remote._protocol
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
                dialogOSD(__LS__(30021) % (_host, _protocol))
                __addon__.setSetting('lg_host', _host)
                __addon__.setSetting('lg_protocol', _protocol.upper())
                __addon__.setSetting('lg_pairing_key', _pairing_key)


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
