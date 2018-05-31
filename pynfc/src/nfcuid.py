"""Test for a simple Mifare NFC Authentication"""

#  Pynfc is a python wrapper for the libnfc library
#  Copyright (C) 2009  Mike Auty
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import time
import logging
import ctypes
import string
import nfc

def hex_dump(string):
    """Dumps data as hexstrings"""
    return ' '.join(["%0.2X" % ord(x) for x in string])

### NFC device setup
class NFCReader(object):


    # executed by main program and by each object using the driver
    def __init__(self):
        self.__context = None
        self.__device = None

        mods = [(nfc.NMT_ISO14443A, nfc.NBR_106)]

        self.__modulations = (nfc.nfc_modulation * len(mods))()
        for i in range(len(mods)):
            self.__modulations[i].nmt = mods[i][0]
            self.__modulations[i].nbr = mods[i][1]

    def run(self):
        """Starts the looping thread"""
        self.__context = ctypes.pointer(nfc.nfc_context())
        nfc.nfc_init(ctypes.byref(self.__context))
        loop = True
        try:
            conn_strings = (nfc.nfc_connstring * 10)()
            devices_found = nfc.nfc_list_devices(self.__context, conn_strings, 10)
            if devices_found >= 1:
                self.__device = nfc.nfc_open(self.__context, conn_strings[0])
                try:
                    _ = nfc.nfc_initiator_init(self.__device)
                    self.uid = ''
                    print 'start poll'
                    while True:
                        self._poll()
                finally:
                    nfc.nfc_close(self.__device)
            else:
                print "NFC Waiting for device."
                time.sleep(5)
        except (KeyboardInterrupt, SystemExit):
            loop = False
        except IOError, e:
            print "Exception: " + str(e)
            loop = True
        finally:
            nfc.nfc_exit(self.__context)
            print "NFC Clean shutdown called"
        return loop


    def _poll(self):
        """One iteration of a loop that polls for cards"""
        nt = nfc.nfc_target()
        res = nfc.nfc_initiator_poll_target(self.__device, self.__modulations, len(self.__modulations), 1, 2,
                                            ctypes.byref(nt))
        print "RES", res
        if res < 0:
            print 'card absent'
        elif res >= 1:
            print 'length ',nt.nti.nai.szUidLen
            self.uid = "".join([chr(nt.nti.nai.abtUid[i]) for i in range(nt.nti.nai.szUidLen)])
            print self.uid.encode("hex")
        else:
            print 'fault'


if __name__ == '__main__':
    while NFCReader().run():
        pass
