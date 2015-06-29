# import xbmc
import re,httplib
import xml.etree.ElementTree as etree

lgtv = {}
lgtv["ipaddress"] = "141.55.92.113"
lgtv["pairingKey"] = "045855"
headers = {"Content-Type": "application/atom+xml"}

def getSessionid():
    conn = httplib.HTTPConnection( lgtv["ipaddress"], port=8080)
    pairCmd = "<?xml version=\"1.0\" encoding=\"utf-8\"?><auth><type>AuthReq</type><value>" \
            + lgtv["pairingKey"] + "</value></auth>"
    conn.request("POST", "/hdcp/api/auth", pairCmd, headers=headers)
    httpResponse = conn.getresponse()
    if httpResponse.reason != "OK" :
        print httpResponse.reason
        return False
    tree = etree.XML(httpResponse.read())
    return tree.find('session').text


def handleCommand(cmdcode):
    conn = httplib.HTTPConnection( lgtv["ipaddress"], port=8080)
    cmdText = "<?xml version=\"1.0\" encoding=\"utf-8\"?><command><session>" \
                + lgtv["session"]  \
                + "</session><type>HandleKeyInput</type><value>" \
                + cmdcode \
                + "</value></command>"
    conn.request("POST", "/hdcp/api/dtv_wifirc", cmdText, headers=headers)
    httpResponse = conn.getresponse()

'''
class MyPlayer(xbmc.Player) :
    global lgtv
    def _init_ (self):
        xbmc.Player._init_(self)

    def onPlayBackStarted(self):
        if xbmc.Player().isPlayingVideo():
            currentPlayingFile = xbmc.Player().getPlayingFile()
            if re.search(r'3D Movies', currentPlayingFile, re.I):
                lgtv["session"] = getSessionid()
                if lgtv["session"]:
                    xbmc.sleep(2500) # sleep for a while, may need modification depending on your TV
                    handleCommand("220") # Send 3D button
                    xbmc.sleep(900)
                    handleCommand("68") # Send Select button
                    xbmc.sleep(900)
                    handleCommand("68") # Send Select button again


player=MyPlayer()
while(1):
        xbmc.sleep(500)
'''
x=getSessionid()
print x