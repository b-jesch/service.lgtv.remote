from resources.lib import interface
from resources.lib.tools import *


cmd_seq = dict({'split_vertical':   {'on':  {'ROAP': [400, 15, 20],
                                             'HDCP': [220, 68, 6, 68]},
                                     'off': {'ROAP': [400, 20, 400, 14, 20, 400],
                                             'HDCP': [220, 68, 220, 68, 7, 68, 220, 68]}},
                'split_horizontal': {'on':  {'ROAP': [400, 15, 15, 20],
                                             'HDCP': [220, 68, 6, 6, 68]},
                                     'off': {'ROAP': [400, 20, 400, 14, 14, 20, 400],
                                             'HDCP': [220, 68, 220, 68, 7, 7, 68, 220, 68]}}
                })

mode_3d = False


def determine_mode():
    query = {"method": "GUI.GetProperties", "params": {"properties": ["stereoscopicmode"]}}
    res = jsonrpc(query)
    if res.get('stereoscopicmode', False) and res['stereoscopicmode']['mode'] in ['split_vertical',
                                                                                  'split_horizontal',
                                                                                  'off']:
        return res['stereoscopicmode']['mode']
    return False


def err(method, data):
    notifyLog("Discard notification: %s" % method)


class EventMonitor(xbmc.Monitor):
    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)

        self.mode_3d = None
        self.getSettings()

        self.methodDict = {'Player.OnAVStart': self.switch_on,
                           'Player.OnStop': self.switch_off}

        self.Interface = interface.Interface(host=self.lg_host, port=self.lg_port, protocol=self.lg_protocol, key=self.lg_pairing_key)
        if self.Interface.session_id is None: notifyOSD(ADDON_NAME, LS(30054), xbmcgui.NOTIFICATION_ERROR)

    def getSettings(self):
        self.lg_host = None if ADDON.getSetting('lg_host') == '' else ADDON.getSetting('lg_host')
        self.lg_port = 8080 if ADDON.getSetting('lg_port') == '' else int(ADDON.getSetting('lg_port'))
        self.lg_protocol = None if ADDON.getSetting('lg_protocol') not in [LS(30015), LS(30016)] else ADDON.getSetting('lg_protocol')
        self.lg_pairing_key = None if ADDON.getSetting('lg_pairing_key') == '' else ADDON.getSetting('lg_pairing_key')
        self.lg_key_delay = int(ADDON.getSetting('lg_delay'))

    def onSettingsChanged(self):
        notifyLog('Settings changed, reload...')
        self.getSettings()

    def onNotification(self, sender, method, data):
        notifyLog("Notification received: %s: %s - %s" % (sender, method, data))
        self.methodDict.get(method, err)(method, data)

    def switch_on(self, method, data):
        notifyLog('%s: %s' % (method, data))
        mode = determine_mode()
        if mode and (self.mode_3d is None or not self.mode_3d):
            self.send_sequence(cmd_seq[mode]['on'][ADDON.getSetting('lg_protocol')], 'on')
            self.mode_3d = True

    def switch_off(self, method, data):
        notifyLog('%s: %s' % (method, data))
        mode = determine_mode()
        if mode and self.mode_3d:
            self.send_sequence(cmd_seq[mode]['off'][ADDON.getSetting('lg_protocol')], 'off')
            self.mode_3d = False

    def send_sequence(self, sequence, onoff):
        if not self.Interface.session_id: return False
        if ADDON.getSetting('use_own_seq').lower() == 'true': sequence = ADDON.getSetting('lg_3D_%s' % onoff).split()
        for code in sequence:
            notifyLog('%s msec delay, sending keycode %s (%s): %s.' % (self.lg_key_delay, code, hex(code),
                                                                       self.Interface.handle_key_input(code)))
            xbmc.sleep(self.lg_key_delay)

    def main(self):
        while not self.waitForAbort(30):
            if self.Interface.session_id is None:
                self.Interface = interface.Interface(host=self.lg_host, port=self.lg_port, protocol=self.lg_protocol)


if __name__ == '__main__':
    notifyLog('Start Service', xbmc.LOGINFO)

    EvMon = EventMonitor()
    EvMon.main()

    notifyLog('Finish Service', xbmc.LOGINFO)
    del EvMon
