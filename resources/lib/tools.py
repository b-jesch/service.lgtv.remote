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

OSD = xbmcgui.Dialog()


def notifyOSD(header, message, icon=xbmcgui.NOTIFICATION_INFO):
    OSD.notification(header, message, icon)


def dialogOSD(message, header=ADDON_NAME):
    OSD.ok(header, message)


def dialogYesNo(message, header=ADDON_NAME):
    return OSD.yesno(header, message)


def notifyLog(message, level=xbmc.LOGDEBUG):
    xbmc.log('[%s %s] %s' % (ADDON_ID, ADDON_VERSION, message), level)


def keyboard(input, header=ADDON_NAME):
    return OSD.input(header, defaultt=input, type=xbmcgui.INPUT_ALPHANUM)


def jsonrpc(query):
    querystring = {"jsonrpc": "2.0", "id": 1}
    querystring.update(query)
    try:
        response = json.loads(xbmc.executeJSONRPC(json.dumps(querystring)))
        if 'result' in response: return response['result']
    except TypeError as e:
        notifyLog('Error executing JSON RPC: {}'.format(e.args), level=xbmc.LOGERROR)
    return False
