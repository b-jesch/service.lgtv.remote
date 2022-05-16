#!/usr/bin/env python
# encoding: utf-8

import re
import socket
from . tools import *


import xml.etree.ElementTree as etree
import http.client as httplib
import xbmc

# KEY_PAIRING='SMYBYA' # LG at Home
# KEY_PAIRING='045855' # LG at Work


class KeyInputError(Exception):
    pass


class Interface(object):

    _xmlv = '<?xml version="1.0" encoding="utf-8"?>'
    _headers = {'Content-Type': 'application/atom+xml'}
    _maxvalue = {'HDCP': 255, 'ROAP': 1024}

    class LGinNetworkNotFoundException(Exception): pass
    class LGProtocolWebOSException(Exception): pass
    class LGProtocolNotAcceptedException(Exception): pass
    class NoConnectionToHostException(Exception): pass

    def __init__(self, host=None, port=8080, protocol=None):

        self.port = port
        self.host = host
        self.pairing_key = None
        self.session_id = None
        if host is None: self.getip()

        self.protocol = protocol

        if self.host and protocol is None:
            if self.auto_detect_accepted_protocol():
                self.pairing_key = keyboard(ADDON.getSetting('lg_pairing_key'), header=LS(30030))
                if self.pairing_key: ADDON.setSetting('lg_pairing_key', self.pairing_key)

        if self.host: self.get_session_id()

    def getip(self):
        if self.host: return self.host
        strngtoXmit = 'M-SEARCH * HTTP/1.1\r\n' \
                      'HOST: 239.255.255.250:1900\r\n' \
                      'MAN: "ssdp:discover"\r\n' \
                      'MX: 2\r\n' \
                      'ST: urn:schemas-upnp-org:device:MediaRenderer:1\r\n\r\n'.encode()

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        try:
            sock.sendto(strngtoXmit, ('239.255.255.250', 1900))
            gotbytes, addressport = sock.recvfrom(512)
            gotstr = gotbytes.decode()
            if re.search('LG', gotstr):
                notifyLog('Returned: %s' % gotstr, level=xbmc.LOGDEBUG)
                self.host, port = addressport
                notifyLog('Found device: %s' % self.host, level=xbmc.LOGDEBUG)
        except (socket.timeout, socket.error) as e:
            notifyLog('ERROR: %s' % str(e), xbmc.LOGERROR)
        sock.close()

    def auto_detect_accepted_protocol(self):
        if self._doesServiceExist(3000):
            notifyLog("Device use WebOS on Port 3000. Not supported.")
            raise self.LGProtocolWebOSException()

        req_key_xml_string = self._xmlv + '<auth><type>AuthKeyReq</type></auth>'

        for protocol in self._maxvalue:
            try:
                notifyLog("Testing protocol %s on %s:%s" % (protocol, self.host, self.port), level=xbmc.LOGDEBUG)
                conn = httplib.HTTPConnection(self.host, port=self.port, timeout=3)
                conn.request("POST", "/%s/api/auth" % protocol, req_key_xml_string, headers=self._headers)
                http_response = conn.getresponse()
                notifyLog("Got response: %s" % http_response.reason, level=xbmc.LOGDEBUG)
                if http_response.reason == 'OK':
                    self.protocol = protocol
                    notifyLog("Using protocol: %s" % self.protocol, level=xbmc.LOGDEBUG)
                    return True
            except Exception as e:
                notifyLog('Error while testing connection: %s' % str(e), xbmc.LOGERROR)
                return False
            xbmc.sleep(1000)
        raise self.LGProtocolNotAcceptedException()

    def get_session_id(self):
        if not self.pairing_key: return False

        notifyLog("Trying paring key: %s" % self.pairing_key, level=xbmc.LOGDEBUG)
        pair_cmd_xml_string = self._xmlv + '<auth><type>AuthReq</type><value>%s</value></auth>' % self.pairing_key
        try:
            conn = httplib.HTTPConnection(self.host, port=self.port, timeout=3)
            conn.request('POST', '/%s/api/auth' % self.protocol, pair_cmd_xml_string, headers=self._headers)
            http_response = conn.getresponse()
            if http_response.reason != 'OK': return False

            tree = etree.XML(http_response.read())
            self.session_id = tree.find('session').text
            notifyLog("Session ID is %s" % self.session_id, level=xbmc.LOGDEBUG)
            if len(self.session_id) < 8: return False
            return self.session_id

        except (socket.timeout, socket.error):
            raise self.NoConnectionToHostException("No connection to host %s" % self.host)

    def handle_key_input(self, cmdcode):
        try:
            if not (0 < int(cmdcode) < self._maxvalue[self.protocol]):
                raise KeyInputError("Key code %s is not supported." % cmdcode)
        except ValueError:
            notifyLog("Key code %s is not a number" % cmdcode, xbmc.LOGERROR)
            raise KeyInputError("Key code %s is not a number" % cmdcode)

        command_url_for_protocol = {
            'HDCP': '/%s/api/dtv_wifirc' % self.protocol.lower(),
            'ROAP': '/%s/api/command' % self.protocol.lower(),
        }

        key_input_xml_string = self._xmlv + '<command><session>' + self.session_id \
                               + '</session><type>HandleKeyInput</type><value>' + cmdcode + '</value></command>'
        conn = httplib.HTTPConnection(self.host, port=self.port)
        conn.request('POST', command_url_for_protocol[self.protocol], key_input_xml_string, headers=self._headers)
        return conn.getresponse().reason

    def _doesServiceExist(self, port):
        try:
            notifyLog("Checking port %s" % port, level=xbmc.LOGDEBUG)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((self.host, port))
            s.close()
            return True
        except socket.timeout:
            return False
