import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import os
import json

ADDON = xbmcaddon.Addon()
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
ADDON_VERSION = ADDON.getAddonInfo('version')
LS = ADDON.getLocalizedString

ICON_CONNECTED = os.path.join(ADDON_PATH, 'resources', 'media', 'ok.png')
ICON_ERROR = os.path.join(ADDON_PATH, 'resources', 'media', 'fail.png')
ICON_DEFAULT = os.path.join(ADDON_PATH, 'resources', 'media', 'default.png')

OSD = xbmcgui.Dialog()


def notifyOSD(header, message, icon=ICON_DEFAULT):
    OSD.notification(header, message, icon)


def dialogOSD(message, header=ADDON_NAME):
    OSD.ok(header, message)


def dialogYesNo(message, header=ADDON_NAME):
    return OSD.yesno(header, message)


def notifyLog(message, level=xbmc.LOGDEBUG):
    xbmc.log('[%s %s] %s' % (ADDON_ID, ADDON_VERSION, message), level)


def jsonrpc(query):
    querystring = {"jsonrpc": "2.0", "id": 1}
    querystring.update(query)
    try:
        response = json.loads(xbmc.executeJSONRPC(json.dumps(querystring)))
        if 'result' in response: return response['result']
    except TypeError as e:
        notifyLog('Error executing JSON RPC: {}'.format(e.args), level=xbmc.LOGERROR)
    return False
