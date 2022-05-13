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

    _xml_version_string = '<?xml version="1.0" encoding="utf-8"?>'
    _headers = {'Content-Type': 'application/atom+xml'}
    _highest_key_input_for_protocol = {'hdcp': 255, 'roap': 1024}

    class LGinNetworkNotFoundException(Exception): pass
    class LGProtocolWebOSException(Exception): pass
    class LGProtocolNotAcceptedException(Exception): pass
    class NoConnectionToHostException(Exception): pass

    def __init__(self, host=None, port=8080, protocol=None):

        self.port = port
        self.host = host
        if host is None: self.getip()

        self.protocol = protocol
        if protocol is None: self.auto_detect_accepted_protocol()

        self._pairing_key = None
        self.session_id = None

    def getip(self):
        if self.host: return self.host
        strngtoXmit = 'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\n' + \
            'MAN: "ssdp:discover"\r\nMX: 2\r\nST: urn:schemas-upnp-org:device:MediaRenderer:1\r\n\r\n'

        bytestoXmit = strngtoXmit.encode()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        found = False
        i = 0

        while not found and i < 5:
            try:
                sock.sendto(bytestoXmit, ('239.255.255.250', 1900))
                gotbytes, addressport = sock.recvfrom(512)
                gotstr = gotbytes.decode()
                if re.search('LG', gotstr):
                    notifyLog('Returned: %s' % gotstr, level=xbmc.LOGDEBUG)
                    self.host, port = addressport
                    notifyLog('Found device: %s:%s' % (self.host, port), level=xbmc.LOGDEBUG)
                    found = True
                    break
            except Exception as e:
                notifyLog('ERROR: %s' % str(e), xbmc.LOGERROR)

            xbmc.sleep(1000)
            i = i + 1
        sock.close()

        if not found: raise self.LGinNetworkNotFoundException()
        notifyLog("Using device: %s:%s" % (self.host, self.port), level=xbmc.LOGDEBUG)

    def auto_detect_accepted_protocol(self):
        if self._doesServiceExist(3000):
            notifyLog("Device use WebOS on Port 3000. Not supported.")
            raise self.LGProtocolWebOSException()

        req_key_xml_string = self._xml_version_string + '<auth><type>AuthKeyReq</type></auth>'

        for protocol in self._highest_key_input_for_protocol:
            try:
                notifyLog("Testing protocol %s on %s:%s" % (protocol, self.host, self.port), level=xbmc.LOGDEBUG)
                conn = httplib.HTTPConnection(self.host, port=self.port, timeout=3)
                conn.request("POST", "/%s/api/auth" % protocol, req_key_xml_string, headers=self._headers)
                http_response = conn.getresponse()
                notifyLog("Got response: %s" % http_response.reason, level=xbmc.LOGDEBUG)
                if http_response.reason == 'OK':
                    self.protocol = protocol
                    notifyLog("Using protocol: %s" % self.protocol, level=xbmc.LOGDEBUG)
                    return
            except Exception as e:
                notifyLog('Error while testing connection: %s' % str(e), xbmc.LOGERROR)
            xbmc.sleep(1000)
        raise self.LGProtocolNotAcceptedException()

    def get_session_id(self, pairing_key):
        if not pairing_key: return False

        self._pairing_key = pairing_key
        notifyLog("Trying paring key: %s" % self._pairing_key, level=xbmc.LOGDEBUG)
        pair_cmd_xml_string = self._xml_version_string + '<auth><type>AuthReq</type><value>' + \
            self._pairing_key + '</value></auth>'
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
        highest_key_input = self._highest_key_input_for_protocol[self.protocol]
        try:
            if 0 > int(cmdcode) or int(cmdcode) > highest_key_input:
                raise KeyInputError("Key input %s is not supported." % cmdcode)
        except ValueError:
            notifyLog("Key input %s is not a number" % cmdcode, xbmc.LOGERROR)
            raise KeyInputError("Key input %s is not a number" % cmdcode)

        if not self.session_id: raise Exception("No valid session key available.")

        command_url_for_protocol = {
            'hdcp': '/%s/api/dtv_wifirc' % self.protocol,
            'roap': '/%s/api/command' % self.protocol,
        }

        key_input_xml_string = self._xml_version_string + '<command><session>' + self.session_id \
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
        except:
            return False
        return True
