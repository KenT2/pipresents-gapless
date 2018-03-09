"""
KRT: This is a  cut down and modified version of pyosc. https://gitorious.org/pyosc
removed oSC multi-cilent code
removed connect and send in OSC Client code and modified sendto to do a sendto not a send - original stopped two clients using the same server.

Original Text
-------------
This module contains an OpenSoundControl implementation (in Pure Python), based (somewhat) on the 
good old 'SimpleOSC' implementation by Daniel Holth & Clinton McChesney.

This implementation is intended to still be 'Simple' to the user, but much more complete
(with OSCServer & OSCClient classes) and much more powerful
(the OSCMultiClient supports subscriptions & message-filtering,
OSCMessage & OSCBundle are now proper container-types)

================
OpenSoundControl
================

OpenSoundControl is a network-protocol for sending (small) packets of addressed data over network sockets.
This OSC-implementation uses the UDP/IP protocol for sending and receiving packets.
(Although it is theoretically possible to send OSC-packets over TCP, almost all known implementations use UDP) 

OSC-packets come in two kinds:
- OSC-messages consist of an 'address'-string (not to be confused with a (host:port) network-address!),
followed by a string of 'typetags' associated with the message's arguments (ie. 'payload'), 
and finally the arguments themselves, encoded in an OSC-specific way.
The OSCMessage class makes it easy to create & manipulate OSC-messages of this kind in a 'pythonesque' way
(that is, OSCMessage-objects behave a lot like lists)

- OSC-bundles are a special type of OSC-message containing only OSC-messages as 'payload'. Recursively.
(meaning; an OSC-bundle could contain other OSC-bundles, containing OSC-bundles etc.)
OSC-bundles start with the special keyword '#bundle' and do not have an OSC-address. (but the OSC-messages 
a bundle contains will have OSC-addresses!)
Also, an OSC-bundle can have a timetag, essentially telling the receiving Server to 'hold' the bundle until
the specified time.
The OSCBundle class allows easy cration & manipulation of OSC-bundles.
    
see also http://opensoundcontrol.org/spec-1_0

---------

To send OSC-messages, you need an OSCClient, and to receive OSC-messages you need an OSCServer.

The OSCClient uses an 'AF_INET / SOCK_DGRAM' type socket (see the 'socket' module) to send 
binary representations of OSC-messages to a remote host:port address.

The OSCServer listens on an 'AF_INET / SOCK_DGRAM' type socket bound to a local port, and handles
incoming requests. Either one-after-the-other (OSCServer) or in a multi-threaded / multi-process fashion 
(ThreadingOSCServer / ForkingOSCServer). If the Server has a callback-function (a.k.a. handler) registered
to 'deal with' (i.e. handle) the received message's OSC-address, that function is called, passing it the (decoded) message

The different OSCServers implemented here all support the (recursive) un-bundling of OSC-bundles,
and OSC-bundle timetags.

In fact, this implementation supports:

- OSC-messages with 'i' (int32), 'f' (float32), 's' (string) and 'b' (blob / binary data) types
- OSC-bundles, including timetag-support
- OSC-address patterns including '*', '?', '{,}' and '[]' wildcards.

(please *do* read the OSC-spec! http://opensoundcontrol.org/spec-1_0 it explains what these things mean.) 

In addition, the OSCMultiClient supports:
- Sending a specific OSC-message to multiple remote servers
- Remote server subscription / unsubscription (through OSC-messages, of course)
- Message-address filtering.

---------

Stock, V2_Lab, Rotterdam, 2008

----------
Changelog:
----------
v0.3.0  - 27 Dec. 2007
    Started out to extend the 'SimpleOSC' implementation (v0.2.3) by Daniel Holth & Clinton McChesney.
    Rewrote OSCMessage
    Added OSCBundle
    
v0.3.1  - 3 Jan. 2008
    Added OSClient
    Added OSCRequestHandler, loosely based on the original CallbackManager 
    Added OSCServer
    Removed original CallbackManager
    Adapted testing-script (the 'if __name__ == "__main__":' block at the end) to use new Server & Client
    
v0.3.2  - 5 Jan. 2008
    Added 'container-type emulation' methods (getitem(), setitem(), __iter__() & friends) to OSCMessage
    Added ThreadingOSCServer & ForkingOSCServer
        - 6 Jan. 2008
    Added OSCMultiClient
    Added command-line options to testing-script (try 'python OSC.py --help')

v0.3.3  - 9 Jan. 2008
    Added OSC-timetag support to OSCBundle & OSCRequestHandler
    Added ThreadingOSCRequestHandler
    
v0.3.4  - 13 Jan. 2008
    Added message-filtering to OSCMultiClient
    Added subscription-handler to OSCServer
    Added support fon numpy/scipy int & float types. (these get converted to 'standard' 32-bit OSC ints / floats!)
    Cleaned-up and added more Docstrings

v0.3.5 - 14 aug. 2008
    Added OSCServer.reportErr(...) method

-----------------
Original Comments
-----------------

> Open SoundControl for Python
> Copyright (C) 2002 Daniel Holth, Clinton McChesney
> 
> This library is free software; you can redistribute it and/or modify it under
> the terms of the GNU Lesser General Public License as published by the Free
> Software Foundation; either version 2.1 of the License, or (at your option) any
> later version.
> 
> This library is distributed in the hope that it will be useful, but WITHOUT ANY
> WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
> PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
> details.

> You should have received a copy of the GNU Lesser General Public License along
> with this library; if not, write to the Free Software Foundation, Inc., 59
> Temple Place, Suite 330, Boston, MA  02111-1307  USA

> For questions regarding this module contact Daniel Holth <dholth@stetson.edu>
> or visit http://www.stetson.edu/~ProctoLogic/

> Changelog:
> 15 Nov. 2001:
>   Removed dependency on Python 2.0 features.
>   - dwh
> 13 Feb. 2002:
>   Added a generic callback handler.
>   - dwh
"""

import math, re, socket, select, string, struct, sys, threading, time, types
from SocketServer import UDPServer, DatagramRequestHandler, ForkingMixIn, ThreadingMixIn

global version
version = ("0.3","5b", "$Rev: 5294 $"[6:-2])

global FloatTypes
FloatTypes = [types.FloatType]

global IntTypes
IntTypes = [types.IntType]

"""
# numpy/scipy support
"""

try:
    from numpy import typeDict

    for ftype in ['float32', 'float64', 'float128']:
        try:
            FloatTypes.append(typeDict[ftype])
        except KeyError:
            pass
        
    for itype in ['int8', 'int16', 'int32', 'int64']:
        try:
            IntTypes.append(typeDict[itype])
            IntTypes.append(typeDict['u' + itype])
        except KeyError:
            pass
        
    # thanks for those...
    del typeDict, ftype, itype
    
except ImportError:
    pass

######
#
# OSCMessage classes
#
######

class OSCMessage(object):
    """ Builds typetagged OSC messages. 
    
    OSCMessage objects are container objects for building OSC-messages.
    On the 'front' end, they behave much like list-objects, and on the 'back' end
    they generate a binary representation of the message, which can be sent over a network socket.
    OSC-messages consist of an 'address'-string (not to be confused with a (host, port) IP-address!),
    followed by a string of 'typetags' associated with the message's arguments (ie. 'payload'), 
    and finally the arguments themselves, encoded in an OSC-specific way.
    
    On the Python end, OSCMessage are lists of arguments, prepended by the message's address.
    The message contents can be manipulated much like a list:
      >>> msg = OSCMessage("/my/osc/address")
      >>> msg.append('something')
      >>> msg.insert(0, 'something else')
      >>> msg[1] = 'entirely'
      >>> msg.extend([1,2,3.])
      >>> msg += [4, 5, 6.]
      >>> del msg[3:6]
      >>> msg.pop(-2)
      5
      >>> print msg
      /my/osc/address ['something else', 'entirely', 1, 6.0]

    OSCMessages can be concatenated with the + operator. In this case, the resulting OSCMessage
    inherits its address from the left-hand operand. The right-hand operand's address is ignored.
    To construct an 'OSC-bundle' from multiple OSCMessage, see OSCBundle!
    
    Additional methods exist for retreiving typetags or manipulating items as (typetag, value) tuples.
    """
    def __init__(self, address=""):
        """Instantiate a new OSCMessage.
        The OSC-address can be specified with the 'address' argument
        """
        self.clear(address)

    def setAddress(self, address):
        """Set or change the OSC-address
        """
        self.address = address

    def clear(self, address=""):
        """Clear (or set a new) OSC-address and clear any arguments appended so far
        """
        self.address  = address
        self.clearData()

    def clearData(self):
        """Clear any arguments appended so far
        """
        self.typetags = ","
        self.message  = ""

    def append(self, argument, typehint=None):
        """Appends data to the message, updating the typetags based on
        the argument's type. If the argument is a blob (counted
        string) pass in 'b' as typehint.
        'argument' may also be a list or tuple, in which case its elements
        will get appended one-by-one, all using the provided typehint
        """
        if type(argument) == types.DictType:
            argument = argument.items()
        elif isinstance(argument, OSCMessage):
            raise TypeError("Can only append 'OSCMessage' to 'OSCBundle'")
        
        if hasattr(argument, '__iter__'):
            for arg in argument:
                self.append(arg, typehint)
            
            return
        
        if typehint == 'b':
            binary = OSCBlob(argument)
            tag = 'b'
        elif typehint == 't':
            binary = OSCTimeTag(argument)
            tag = 't'
        else:
            tag, binary = OSCArgument(argument, typehint)

        self.typetags += tag
        self.message += binary
        
    def getBinary(self):
        """Returns the binary representation of the message
        """
        binary = OSCString(self.address)
        binary += OSCString(self.typetags)
        binary += self.message
        
        return binary

    def __repr__(self):
        """Returns a string containing the decode Message
        """
        return str(decodeOSC(self.getBinary()))

    def __str__(self):
        """Returns the Message's address and contents as a string.
        """
        return "%s %s" % (self.address, str(self.values()))
    
    def __len__(self):
        """Returns the number of arguments appended so far
        """
        return (len(self.typetags) - 1)
    
    def __eq__(self, other):
        """Return True if two OSCMessages have the same address & content
        """
        if not isinstance(other, self.__class__):
            return False
        
        return (self.address == other.address) and (self.typetags == other.typetags) and (self.message == other.message)
    
    def __ne__(self, other):
        """Return (not self.__eq__(other))
        """
        return not self.__eq__(other)
    
    def __add__(self, values):
        """Returns a copy of self, with the contents of 'values' appended
        (see the 'extend()' method, below)
        """
        msg = self.copy()
        msg.extend(values)
        return msg
    
    def __iadd__(self, values):
        """Appends the contents of 'values'
        (equivalent to 'extend()', below)
        Returns self
        """
        self.extend(values)
        return self
    
    def __radd__(self, values):
        """Appends the contents of this OSCMessage to 'values'
        Returns the extended 'values' (list or tuple)
        """
        out = list(values)
        out.extend(self.values())
        
        if type(values) == types.TupleType:
            return tuple(out)
        
        return out
    
    def _reencode(self, items):
        """Erase & rebuild the OSCMessage contents from the given
        list of (typehint, value) tuples"""
        self.clearData()
        for item in items:
            self.append(item[1], item[0])
        
    def values(self):
        """Returns a list of the arguments appended so far
        """
        return decodeOSC(self.getBinary())[2:]
    
    def tags(self):
        """Returns a list of typetags of the appended arguments
        """
        return list(self.typetags.lstrip(','))
    
    def items(self):
        """Returns a list of (typetag, value) tuples for 
        the arguments appended so far
        """
        out = []
        values = self.values()
        typetags = self.tags()
        for i in range(len(values)):
            out.append((typetags[i], values[i]))
            
        return out

    def __contains__(self, val):
        """Test if the given value appears in the OSCMessage's arguments
        """
        return (val in self.values())

    def __getitem__(self, i):
        """Returns the indicated argument (or slice)
        """
        return self.values()[i]

    def __delitem__(self, i):
        """Removes the indicated argument (or slice)
        """
        items = self.items()
        del items[i]
            
        self._reencode(items)
    
    def _buildItemList(self, values, typehint=None):
        if isinstance(values, OSCMessage):
            items = values.items()
        elif type(values) == types.ListType:
            items = []
            for val in values:
                if type(val) == types.TupleType:
                    items.append(val[:2])
                else:
                    items.append((typehint, val))
        elif type(values) == types.TupleType:
            items = [values[:2]]
        else:       
            items = [(typehint, values)]
            
        return items
    
    def __setitem__(self, i, val):
        """Set indicatated argument (or slice) to a new value.
        'val' can be a single int/float/string, or a (typehint, value) tuple.
        Or, if 'i' is a slice, a list of these or another OSCMessage.
        """
        items = self.items()
        
        new_items = self._buildItemList(val)
        
        if type(i) != types.SliceType:
            if len(new_items) != 1:
                raise TypeError("single-item assignment expects a single value or a (typetag, value) tuple")
            
            new_items = new_items[0]
            
        # finally...
        items[i] = new_items
        
        self._reencode(items)
    
    def setItem(self, i, val, typehint=None):
        """Set indicated argument to a new value (with typehint)
        """
        items = self.items()
        
        items[i] = (typehint, val)
            
        self._reencode(items)
        
    def copy(self):
        """Returns a deep copy of this OSCMessage
        """
        msg = self.__class__(self.address)
        msg.typetags = self.typetags
        msg.message = self.message
        return msg
    
    def count(self, val):
        """Returns the number of times the given value occurs in the OSCMessage's arguments
        """
        return self.values().count(val)
    
    def index(self, val):
        """Returns the index of the first occurence of the given value in the OSCMessage's arguments.
        Raises ValueError if val isn't found
        """
        return self.values().index(val)
    
    def extend(self, values):
        """Append the contents of 'values' to this OSCMessage.
        'values' can be another OSCMessage, or a list/tuple of ints/floats/strings
        """
        items = self.items() + self._buildItemList(values)
        
        self._reencode(items)
        
    def insert(self, i, val, typehint = None):
        """Insert given value (with optional typehint) into the OSCMessage
        at the given index.
        """
        items = self.items()
        
        for item in reversed(self._buildItemList(val)):
            items.insert(i, item)
            
        self._reencode(items)
        
    def popitem(self, i):
        """Delete the indicated argument from the OSCMessage, and return it
        as a (typetag, value) tuple.
        """
        items = self.items()
        
        item = items.pop(i)
        
        self._reencode(items)
        
        return item
    
    def pop(self, i):
        """Delete the indicated argument from the OSCMessage, and return it.
        """
        return self.popitem(i)[1]
        
    def reverse(self):
        """Reverses the arguments of the OSCMessage (in place)
        """
        items = self.items()
        
        items.reverse()
        
        self._reencode(items)
        
    def remove(self, val):
        """Removes the first argument with the given value from the OSCMessage.
        Raises ValueError if val isn't found.
        """
        items = self.items()
        
        # this is not very efficient...
        i = 0
        for (t, v) in items:
            if (v == val):
                break
            i += 1
        else:
            raise ValueError("'%s' not in OSCMessage" % str(val))
        # but more efficient than first calling self.values().index(val),
        # then calling self.items(), which would in turn call self.values() again...
        
        del items[i]
        
        self._reencode(items)
        
    def __iter__(self):
        """Returns an iterator of the OSCMessage's arguments
        """
        return iter(self.values())

    def __reversed__(self):
        """Returns a reverse iterator of the OSCMessage's arguments
        """
        return reversed(self.values())

    def itervalues(self):
        """Returns an iterator of the OSCMessage's arguments
        """
        return iter(self.values())

    def iteritems(self):
        """Returns an iterator of the OSCMessage's arguments as
        (typetag, value) tuples
        """
        return iter(self.items())

    def itertags(self):
        """Returns an iterator of the OSCMessage's arguments' typetags
        """
        return iter(self.tags())

class OSCBundle(OSCMessage):
    """Builds a 'bundle' of OSC messages.
    
    OSCBundle objects are container objects for building OSC-bundles of OSC-messages.
    An OSC-bundle is a special kind of OSC-message which contains a list of OSC-messages
    (And yes, OSC-bundles may contain other OSC-bundles...)
    
    OSCBundle objects behave much the same as OSCMessage objects, with these exceptions:
      - if an item or items to be appended or inserted are not OSCMessage objects, 
      OSCMessage objectss are created to encapsulate the item(s)
      - an OSC-bundle does not have an address of its own, only the contained OSC-messages do.
      The OSCBundle's 'address' is inherited by any OSCMessage the OSCBundle object creates.
      - OSC-bundles have a timetag to tell the receiver when the bundle should be processed.
      The default timetag value (0) means 'immediately'
    """
    def __init__(self, address="", time=0):
        """Instantiate a new OSCBundle.
        The default OSC-address for newly created OSCMessages 
        can be specified with the 'address' argument
        The bundle's timetag can be set with the 'time' argument
        """
        super(OSCBundle, self).__init__(address)
        self.timetag = time

    def __str__(self):
        """Returns the Bundle's contents (and timetag, if nonzero) as a string.
        """
        if (self.timetag > 0.):
            out = "#bundle (%s) [" % self.getTimeTagStr()
        else:
            out = "#bundle ["

        if self.__len__():
            for val in self.values():
                out += "%s, " % str(val)
            out = out[:-2]      # strip trailing space and comma
            
        return out + "]"
    
    def setTimeTag(self, time):
        """Set or change the OSCBundle's TimeTag
        In 'Python Time', that's floating seconds since the Epoch
        """
        if time >= 0:
            self.timetag = time
    
    def getTimeTagStr(self):
        """Return the TimeTag as a human-readable string
        """
        fract, secs = math.modf(self.timetag)
        out = time.ctime(secs)[11:19]
        out += ("%.3f" % fract)[1:]
        
        return out
    
    def append(self, argument, typehint = None):
        """Appends data to the bundle, creating an OSCMessage to encapsulate
        the provided argument unless this is already an OSCMessage.
        Any newly created OSCMessage inherits the OSCBundle's address at the time of creation.
        If 'argument' is an iterable, its elements will be encapsuated by a single OSCMessage.
        Finally, 'argument' can be (or contain) a dict, which will be 'converted' to an OSCMessage;
          - if 'addr' appears in the dict, its value overrides the OSCBundle's address
          - if 'args' appears in the dict, its value(s) become the OSCMessage's arguments
        """
        if isinstance(argument, OSCMessage):
            binary = OSCBlob(argument.getBinary())
        else:
            msg = OSCMessage(self.address)
            if type(argument) == types.DictType:
                if 'addr' in argument:
                    msg.setAddress(argument['addr'])
                if 'args' in argument:
                    msg.append(argument['args'], typehint)
            else:
                msg.append(argument, typehint)
            
            binary = OSCBlob(msg.getBinary())

        self.message += binary
        self.typetags += 'b'
        
    def getBinary(self):
        """Returns the binary representation of the message
        """
        binary = OSCString("#bundle")
        binary += OSCTimeTag(self.timetag)
        binary += self.message
        
        return binary

    def _reencapsulate(self, decoded):
        if decoded[0] == "#bundle":
            msg = OSCBundle()
            msg.setTimeTag(decoded[1])
            for submsg in decoded[2:]:
                msg.append(self._reencapsulate(submsg))
                
        else:
            msg = OSCMessage(decoded[0])
            tags = decoded[1].lstrip(',')
            for i in range(len(tags)):
                msg.append(decoded[2+i], tags[i])
                
        return msg
    
    def values(self):
        """Returns a list of the OSCMessages appended so far
        """
        out = []
        for decoded in decodeOSC(self.getBinary())[2:]:
            out.append(self._reencapsulate(decoded))
            
        return out
        
    def __eq__(self, other):
        """Return True if two OSCBundles have the same timetag & content
        """
        if not isinstance(other, self.__class__):
            return False
        
        return (self.timetag == other.timetag) and (self.typetags == other.typetags) and (self.message == other.message)
    
    def copy(self):
        """Returns a deep copy of this OSCBundle
        """
        copy = super(OSCBundle, self).copy()
        copy.timetag = self.timetag
        return copy

######
#
# OSCMessage encoding functions
#
######

def OSCString(next):
    """Convert a string into a zero-padded OSC String.
    The length of the resulting string is always a multiple of 4 bytes.
    The string ends with 1 to 4 zero-bytes ('\x00') 
    """
    
    OSCstringLength = math.ceil((len(next)+1) / 4.0) * 4
    return struct.pack(">%ds" % (OSCstringLength), str(next))

def OSCBlob(next):
    """Convert a string into an OSC Blob.
    An OSC-Blob is a binary encoded block of data, prepended by a 'size' (int32).
    The size is always a mutiple of 4 bytes. 
    The blob ends with 0 to 3 zero-bytes ('\x00') 
    """

    if type(next) in types.StringTypes:
        OSCblobLength = math.ceil((len(next)) / 4.0) * 4
        binary = struct.pack(">i%ds" % (OSCblobLength), OSCblobLength, next)
    else:
        binary = ""

    return binary

def OSCArgument(next, typehint=None):
    """ Convert some Python types to their
    OSC binary representations, returning a
    (typetag, data) tuple.
    """
    if not typehint:
        if type(next) in FloatTypes:
            binary  = struct.pack(">f", float(next))
            tag = 'f'
        elif type(next) in IntTypes:
            binary  = struct.pack(">i", int(next))
            tag = 'i'
        else:
            binary  = OSCString(next)
            tag = 's'

    elif typehint == 'f':
        try:
            binary  = struct.pack(">f", float(next))
            tag = 'f'
        except ValueError:
            binary  = OSCString(next)
            tag = 's'
    elif typehint == 'i':
        try:
            binary  = struct.pack(">i", int(next))
            tag = 'i'
        except ValueError:
            binary  = OSCString(next)
            tag = 's'
    else:
        binary  = OSCString(next)
        tag = 's'

    return (tag, binary)

def OSCTimeTag(time):
    """Convert a time in floating seconds to its
    OSC binary representation
    """
    if time > 0:
        fract, secs = math.modf(time)
        binary = struct.pack('>ll', long(secs), long(fract * 1e9))
    else:
        binary = struct.pack('>ll', 0L, 1L)

    return binary

######
#
# OSCMessage decoding functions
#
######

def _readString(data):
    """Reads the next (null-terminated) block of data
    """
    length   = string.find(data,"\0")
    nextData = int(math.ceil((length+1) / 4.0) * 4)
    return (data[0:length], data[nextData:])

def _readBlob(data):
    """Reads the next (numbered) block of data
    """
    
    length   = struct.unpack(">i", data[0:4])[0]
    nextData = int(math.ceil((length) / 4.0) * 4) + 4
    return (data[4:length+4], data[nextData:])

def _readInt(data):
    """Tries to interpret the next 4 bytes of the data
    as a 32-bit integer. """
    
    if(len(data)<4):
        print "Error: too few bytes for int", data, len(data)
        rest = data
        integer = 0
    else:
        integer = struct.unpack(">i", data[0:4])[0]
        rest    = data[4:]

    return (integer, rest)

def _readLong(data):
    """Tries to interpret the next 8 bytes of the data
    as a 64-bit signed integer.
     """

    high, low = struct.unpack(">ll", data[0:8])
    big = (long(high) << 32) + low
    rest = data[8:]
    return (big, rest)

def _readTimeTag(data):
    """Tries to interpret the next 8 bytes of the data
    as a TimeTag.
     """
    high, low = struct.unpack(">ll", data[0:8])
    if (high == 0) and (low <= 1):
        time = 0.0
    else:
        time = int(high) + float(low / 1e9)
    rest = data[8:]
    return (time, rest)

def _readFloat(data):
    """Tries to interpret the next 4 bytes of the data
    as a 32-bit float. 
    """
    
    if(len(data)<4):
        print "Error: too few bytes for float", data, len(data)
        rest = data
        float = 0
    else:
        float = struct.unpack(">f", data[0:4])[0]
        rest  = data[4:]

    return (float, rest)

def decodeOSC(data):
    """Converts a binary OSC message to a Python list. 
    """
    table = {"i":_readInt, "f":_readFloat, "s":_readString, "b":_readBlob}
    decoded = []
    address,  rest = _readString(data)
    if address.startswith(","):
        typetags = address
        address = ""
    else:
        typetags = ""

    if address == "#bundle":
        time, rest = _readTimeTag(rest)
        decoded.append(address)
        decoded.append(time)
        while len(rest)>0:
            length, rest = _readInt(rest)
            decoded.append(decodeOSC(rest[:length]))
            rest = rest[length:]

    elif len(rest)>0:
        if not len(typetags):
            typetags, rest = _readString(rest)
        decoded.append(address)
        decoded.append(typetags)
        if typetags.startswith(","):
            for tag in typetags[1:]:
                value, rest = table[tag](rest)
                decoded.append(value)
        else:
            raise OSCError("OSCMessage's typetag-string lacks the magic ','")

    return decoded

######
#
# Utility functions
#
######

def hexDump(bytes):
    """ Useful utility; prints the string in hexadecimal.
    """
    print "byte   0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F"

    num = len(bytes)
    for i in range(num):
        if (i) % 16 == 0:
             line = "%02X0 : " % (i/16)
        line += "%02X " % ord(bytes[i])
        if (i+1) % 16 == 0:
            print "%s: %s" % (line, repr(bytes[i-15:i+1]))
            line = ""

    bytes_left = num % 16
    if bytes_left:
        print "%s: %s" % (line.ljust(54), repr(bytes[-bytes_left:]))

def getUrlStr(*args):
    """Convert provided arguments to a string in 'host:port/prefix' format
    Args can be:
      - (host, port)
      - (host, port), prefix
      - host, port
      - host, port, prefix
    """
    if not len(args):
        return ""
        
    if type(args[0]) == types.TupleType:
        host = args[0][0]
        port = args[0][1]
        args = args[1:]
    else:
        host = args[0]
        port = args[1]
        args = args[2:]
        
    if len(args):
        prefix = args[0]
    else:
        prefix = ""
    
    if len(host) and (host != '0.0.0.0'):
        try:
            (host, _, _) = socket.gethostbyaddr(host)
        except socket.error:
            pass
    else:
        host = 'localhost'
    
    if type(port) == types.IntType:
        return "%s:%d%s" % (host, port, prefix)
    else:
        return host + prefix
        
def parseUrlStr(url):
    """Convert provided string in 'host:port/prefix' format to it's components
    Returns ((host, port), prefix)
    """
    if not (type(url) in types.StringTypes and len(url)):
        return (None, '')

    i = url.find("://")
    if i > -1:
        url = url[i+3:]
        
    i = url.find(':')
    if i > -1:
        host = url[:i].strip()
        tail = url[i+1:].strip()
    else:
        host = ''
        tail = url
    
    for i in range(len(tail)):
        if not tail[i].isdigit():
            break
    else:
        i += 1
    
    portstr = tail[:i].strip()
    tail = tail[i:].strip()
    
    found = len(tail)
    for c in ('/', '+', '-', '*'):
        i = tail.find(c)
        if (i > -1) and (i < found):
            found = i
    
    head = tail[:found].strip()
    prefix = tail[found:].strip()
    
    prefix = prefix.strip('/')
    if len(prefix) and prefix[0] not in ('+', '-', '*'):
        prefix = '/' + prefix
    
    if len(head) and not len(host):
        host = head

    if len(host):
        try:
            host = socket.gethostbyname(host)
        except socket.error:
            pass

    try:
        port = int(portstr)
    except ValueError:
        port = None
    
    return ((host, port), prefix)

######
#
# OSCClient class
#
######

class OSCClient(object):
    """Simple OSC Client. Handles the sending of OSC-Packets (OSCMessage or OSCBundle) via a UDP-socket
    """
    # set outgoing socket buffer size
    sndbuf_size = 4096 * 8

    def __init__(self, server=None):
        """Construct an OSC Client.
          - server: Local OSCServer-instance this client will use the socket of for transmissions.
          If none is supplied, a socket will be created.
        """
        self.socket = None
        
        if server == None:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self.sndbuf_size)
            self._fd = self.socket.fileno()

            self.server = None
        else:
            self.setServer(server)

        self.client_address = None
        
    def setServer(self, server):
        """Associate this Client with given server.
        The Client will send from the Server's socket.
        The Server will use this Client instance to send replies.
        """
        if not isinstance(server, OSCServer):
            raise ValueError("'server' argument is not a valid OSCServer object")
        
        if self.socket != None:
            self.close()

        self.socket = server.socket.dup()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self.sndbuf_size)
        self._fd = self.socket.fileno()

        self.server = server

        if self.server.client != None:
            self.server.client.close()
        
        self.server.client = self

    def close(self):
        """Disconnect & close the Client's socket
        """
        if self.socket != None:
            self.socket.close()
            self.socket = None

    def __str__(self):
        """Returns a string containing this Client's Class-name, software-version
        and the remote-address it is connected to (if any)
        """
        out = self.__class__.__name__
        out += " v%s.%s-%s" % version
        addr = self.address()
        if addr:
            out += " connected to osc://%s" % getUrlStr(addr)
        else:
            out += " (unconnected)"
    
        return out
    
    def __eq__(self, other):
        """Compare function.
        """
        if not isinstance(other, self.__class__):
            return False
            
        isequal = cmp(self.socket._sock, other.socket._sock)
        if isequal and self.server and other.server:
            return cmp(self.server, other.server)
        
        return isequal
    
    def __ne__(self, other):
        """Compare function.
        """
        return not self.__eq__(other)

    def address(self):
        """Returns a (host,port) tuple of the remote server this client is
        connected to or None if not connected to any server.
        """
        try:
            return self.socket.getpeername()
        except socket.error:
            return None


    def sendto(self, msg, address, timeout=None):
        """Send the given OSCMessage to the specified address.
          - msg:  OSCMessage (or OSCBundle) to be sent
          - address:  (host, port) tuple specifing remote server to send the message to
          - timeout:  A timeout value for attempting to send. If timeout == None,
            this call blocks until socket is available for writing. 
        Raises OSCClientError when timing out while waiting for the socket. 
        """
        if not isinstance(msg, OSCMessage):
            raise TypeError("'msg' argument is not an OSCMessage or OSCBundle object")
            return
        
        ret = select.select([],[self._fd], [], timeout)
        try:
            ret[1].index(self._fd)
        except:
            # for the very rare case this might happen
            raise OSCClientError("Timed out waiting for file descriptor")
        
        try:
            self.socket.sendto(msg.getBinary(),address)

        except socket.error, e:
            if e[0] in (7, 65): # 7 = 'no address associated with nodename',  65 = 'no route to host'
                raise e
            else:
                raise OSCClientError("while sending to %s: %s" % (str(address), str(e)))
                


######
#
# FilterString Utility functions
#
######

def parseFilterStr(args):
    """Convert Message-Filter settings in '+<addr> -<addr> ...' format to a dict of the form
    { '<addr>':True, '<addr>':False, ... } 
    Returns a list: ['<prefix>', filters]
    """
    out = {}
    
    if type(args) in types.StringTypes:
        args = [args]
        
    prefix = None
    for arg in args:
        head = None
        for plus in arg.split('+'):
            minus = plus.split('-')
            plusfs = minus.pop(0).strip()
            if len(plusfs):
                plusfs = '/' + plusfs.strip('/')
            
            if (head == None) and (plusfs != "/*"):
                head = plusfs
            elif len(plusfs):
                if plusfs == '/*':
                    out = { '/*':True } # reset all previous filters
                else:
                    out[plusfs] = True
                
            for minusfs in minus:
                minusfs = minusfs.strip()
                if len(minusfs):
                    minusfs = '/' + minusfs.strip('/')
                    if minusfs == '/*':
                        out = { '/*':False }    # reset all previous filters
                    else:
                        out[minusfs] = False
                
        if prefix == None:
            prefix = head

    return [prefix, out]

def getFilterStr(filters):
    """Return the given 'filters' dict as a list of
    '+<addr>' | '-<addr>' filter-strings
    """
    if not len(filters):
        return []
    
    if '/*' in filters.keys():
        if filters['/*']:
            out = ["+/*"]
        else:
            out = ["-/*"]
    else:
        if False in filters.values():
            out = ["+/*"]
        else:
            out = ["-/*"]
    
    for (addr, bool) in filters.items():
        if addr == '/*':
            continue
        
        if bool:
            out.append("+%s" % addr)
        else:
            out.append("-%s" % addr)

    return out

# A translation-table for mapping OSC-address expressions to Python 're' expressions
OSCtrans = string.maketrans("{,}?","(|).")

def getRegEx(pattern):
    """Compiles and returns a 'regular expression' object for the given address-pattern.
    """
    # Translate OSC-address syntax to python 're' syntax
    pattern = pattern.replace(".", r"\.")       # first, escape all '.'s in the pattern.
    pattern = pattern.replace("(", r"\(")       # escape all '('s.
    pattern = pattern.replace(")", r"\)")       # escape all ')'s.
    pattern = pattern.replace("*", r".*")       # replace a '*' by '.*' (match 0 or more characters)
    pattern = pattern.translate(OSCtrans)       # change '?' to '.' and '{,}' to '(|)'
    
    return re.compile(pattern)
    

######
#
# OSCRequestHandler classes
#
######

class OSCRequestHandler(DatagramRequestHandler):
    """RequestHandler class for the OSCServer
    """
    def dispatchMessage(self, pattern, tags, data):
        """Attempt to match the given OSC-address pattern, which may contain '*',
        against all callbacks registered with the OSCServer.
        Calls the matching callback and returns whatever it returns.
        If no match is found, and a 'default' callback is registered, it calls that one,
        or raises NoCallbackError if a 'default' callback is not registered.
        
          - pattern (string):  The OSC-address of the receied message
          - tags (string):  The OSC-typetags of the receied message's arguments, without ','
          - data (list):  The message arguments
        """
        if len(tags) != len(data):
            raise OSCServerError("Malformed OSC-message; got %d typetags [%s] vs. %d values" % (len(tags), tags, len(data)))
        
        expr = getRegEx(pattern)
        
        replies = []
        matched = 0
        for addr in self.server.callbacks.keys():
            match = expr.match(addr)
            if match and (match.end() == len(addr)):
                reply = self.server.callbacks[addr](pattern, tags, data, self.client_address)
                matched += 1
                if isinstance(reply, OSCMessage):
                    replies.append(reply)
                elif reply != None:
                    raise TypeError("Message-callback %s did not return OSCMessage or None: %s" % (self.server.callbacks[addr], type(reply)))
                    
        if matched == 0:
            if 'default' in self.server.callbacks:
                reply = self.server.callbacks['default'](pattern, tags, data, self.client_address)
                if isinstance(reply, OSCMessage):
                    replies.append(reply)
                elif reply != None:
                    raise TypeError("Message-callback %s did not return OSCMessage or None: %s" % (self.server.callbacks['default'], type(reply)))
            else:
                raise NoCallbackError(pattern)
        
        return replies
        
    def setup(self):
        """Prepare RequestHandler.
        Unpacks request as (packet, source socket address)
        Creates an empty list for replies.
        """

        (self.packet, self.socket) = self.request
        print 'MESSAGE RECEIVED'
        print 'from: ',self.client_address
        print 'raw contents; ',self.packet,'\n'
        self.replies = []

    def _unbundle(self, decoded):
        """Recursive bundle-unpacking function"""
        if decoded[0] != "#bundle":
            self.replies += self.dispatchMessage(decoded[0], decoded[1][1:], decoded[2:])
            return
        
        now = time.time()
        timetag = decoded[1]
        if (timetag > 0.) and (timetag > now):
            time.sleep(timetag - now)
        
        for msg in decoded[2:]:
            self._unbundle(msg)
        
    def handle(self):
        """Handle incoming OSCMessage
        """
        decoded = decodeOSC(self.packet)
        if not len(decoded):
            return
        
        self._unbundle(decoded)
        
    def finish(self):
        """Finish handling OSCMessage.
        Send any reply returned by the callback(s) back to the originating client
        as an OSCMessage or OSCBundle
        """
        if self.server.return_port:
            self.client_address = (self.client_address[0], self.server.return_port)
        
        if len(self.replies) > 1:
            msg = OSCBundle()
            for reply in self.replies:
                msg.append(reply)
        elif len(self.replies) == 1:
            msg = self.replies[0]
        else:
            return
        
        self.server.client.sendto(msg, self.client_address)
        print 'sent reply to',self.client_address




class ThreadingOSCRequestHandler(OSCRequestHandler):
    """Multi-threaded OSCRequestHandler;
    Starts a new RequestHandler thread for each unbundled OSCMessage
    """
    def _unbundle(self, decoded):
        """Recursive bundle-unpacking function
        This version starts a new thread for each sub-Bundle found in the Bundle,
        then waits for all its children to finish.
        """
        if decoded[0] != "#bundle":
            self.replies += self.dispatchMessage(decoded[0], decoded[1][1:], decoded[2:])
            return
        
        now = time.time()
        timetag = decoded[1]
        if (timetag > 0.) and (timetag > now):
            time.sleep(timetag - now)
            now = time.time()
            
        children = []
        
        for msg in decoded[2:]:
            t = threading.Thread(target = self._unbundle, args = (msg,))
            t.start()
            children.append(t)
            
        # wait for all children to terminate
        for t in children:
            t.join()
        
######
#
# OSCServer classes
#
######

class OSCServer(UDPServer):
    """A Synchronous OSCServer
    Serves one request at-a-time, until the OSCServer is closed.
    The OSC address-pattern is matched against a set of OSC-adresses
    that have been registered to the server with a callback-function.
    If the adress-pattern of the message machtes the registered address of a callback,
    that function is called. 
    """
    
    # set the RequestHandlerClass, will be overridden by ForkingOSCServer & ThreadingOSCServer
    RequestHandlerClass = OSCRequestHandler
    
    # define a socket timeout, so the serve_forever loop can actually exit.
    socket_timeout = 1
    
    # DEBUG: print error-tracebacks (to stderr)?
    print_tracebacks = True
    
    def __init__(self, server_address, client=None, return_port=0):
        """Instantiate an OSCServer.
          - server_address ((host, port) tuple): the local host & UDP-port
          the server listens on
          - client (OSCClient instance): The OSCClient used to send replies from this server.
          If none is supplied (default) an OSCClient will be created.
          - return_port (int): if supplied, sets the default UDP destination-port
          for replies coming from this server.
        """
        UDPServer.__init__(self, server_address, self.RequestHandlerClass)
        
        self.callbacks = {}
        self.setReturnPort(return_port)
        self.error_prefix = ""
        self.info_prefix = "/info"
        
        self.socket.settimeout(self.socket_timeout)
        
        self.running = False
        self.client = None
        
        if client == None:
            self.client = OSCClient(server=self)
        else:
            self.setClient(client)
            
    def setClient(self, client):
        """Associate this Server with a new local Client instance, closing the Client this Server is currently using.
        """
        if not isinstance(client, OSCClient):
            raise ValueError("'client' argument is not a valid OSCClient object")
        
        if client.server != None:
            raise OSCServerError("Provided OSCClient already has an OSCServer-instance: %s" % str(client.server))
        
        # Server socket is already listening at this point, so we can't use the client's socket.
        # we'll have to force our socket on the client...
        client_address = client.address()   # client may be already connected
        client.close()              # shut-down that socket
        
        # force our socket upon the client
        client.socket = self.socket.dup()
        client.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, client.sndbuf_size)
        client._fd = client.socket.fileno()
        client.server = self
        
        if client_address:
            client.connect(client_address)
            if not self.return_port:
                self.return_port = client_address[1]
        
        if self.client != None:
            self.client.close()

        self.client = client

    def serve_forever(self):
        """Handle one request at a time until server is closed."""
        self.running = True
        while self.running:
            self.handle_request()   # this times-out when no data arrives.

    def close(self):
        """Stops serving requests, closes server (socket), closes used client
        """
        self.running = False
        self.client.close()
        self.server_close()
    
    def __str__(self):
        """Returns a string containing this Server's Class-name, software-version and local bound address (if any)
        """
        out = self.__class__.__name__
        out += " v%s.%s-%s" % version
        addr = self.address()
        if addr:
            out += " listening on osc://%s" % getUrlStr(addr)
        else:
            out += " (unbound)"
            
        return out
    
    def __eq__(self, other):
        """Compare function.
        """
        if not isinstance(other, self.__class__):
            return False
            
        return cmp(self.socket._sock, other.socket._sock)

    def __ne__(self, other):
        """Compare function.
        """
        return not self.__eq__(other)

    def address(self):
        """Returns a (host,port) tuple of the local address this server is bound to,
        or None if not bound to any address.
        """
        try:
            return self.socket.getsockname()
        except socket.error:
            return None
    
    def setReturnPort(self, port):
        """Set the destination UDP-port for replies returning from this server to the remote client
        """
        if (port > 1024) and (port < 65536):
            self.return_port = port
        else:
            self.return_port = None
            

    def setSrvInfoPrefix(self, pattern):
        """Set the first part of OSC-address (pattern) this server will use to reply to server-info requests.
        """
        if len(pattern):
            pattern = '/' + pattern.strip('/')
        
        self.info_prefix = pattern

    def setSrvErrorPrefix(self, pattern=""):
        """Set the OSC-address (pattern) this server will use to report errors occuring during
        received message handling to the remote client.
        
        If pattern is empty (default), server-errors are not reported back to the client.
        """
        if len(pattern):
            pattern = '/' + pattern.strip('/')
        
        self.error_prefix = pattern

    def addMsgHandler(self, address, callback):
        """Register a handler for an OSC-address
          - 'address' is the OSC address-string. 
        the address-string should start with '/' and may not contain '*'
          - 'callback' is the function called for incoming OSCMessages that match 'address'.
        The callback-function will be called with the same arguments as the 'msgPrinter_handler' below
        """
        for chk in '*?,[]{}# ':
            if chk in address:
                raise OSCServerError("OSC-address string may not contain any characters in '*?,[]{}# '")
        
        if type(callback) not in (types.FunctionType, types.MethodType):
            raise OSCServerError("Message callback '%s' is not callable" % repr(callback))
        
        if address != 'default':
            address = '/' + address.strip('/')
            
        self.callbacks[address] = callback
        
    def delMsgHandler(self,address):
        """Remove the registered handler for the given OSC-address
        """
        del self.callbacks[address]
    
    def getOSCAddressSpace(self):
        """Returns a list containing all OSC-addresses registerd with this Server. 
        """
        return self.callbacks.keys()
    
    def addDefaultHandlers(self, prefix="", info_prefix="/info", error_prefix="/error"):
        """Register a default set of OSC-address handlers with this Server:
        - 'default' ->  noCallback_handler
        the given prefix is prepended to all other callbacks registered by this method:
        - '<prefix><info_prefix' ->  serverInfo_handler
        - '<prefix><error_prefix> ->  msgPrinter_handler
        - '<prefix>/print' ->  msgPrinter_handler
        and, if the used Client supports it;
        - '<prefix>/subscribe' -> subscription_handler
        - '<prefix>/unsubscribe' -> subscription_handler

        Note: the given 'error_prefix' argument is also set as default 'error_prefix' for error-messages
        *sent from* this server. This is ok, because error-messages generally do not elicit a reply from the receiver.
        
        To do this with the serverInfo-prefixes would be a bad idea, because if a request received on '/info' (for example)
        would send replies to '/info', this could potentially cause a never-ending loop of messages!
        Do *not* set the 'info_prefix' here (for incoming serverinfo requests) to the same value as given to
        the setSrvInfoPrefix() method (for *replies* to incoming serverinfo requests).
        For example, use '/info' for incoming requests, and '/inforeply' or '/serverinfo' or even just '/print' as the 
        info-reply prefix. 
        """
        self.error_prefix = error_prefix
        self.addMsgHandler('default', self.noCallback_handler)
        self.addMsgHandler(prefix + info_prefix, self.serverInfo_handler)
        self.addMsgHandler(prefix + error_prefix, self.msgPrinter_handler)
        self.addMsgHandler(prefix + '/print', self.msgPrinter_handler)
        
        
    def printErr(self, txt):
        """Writes 'OSCServer: txt' to sys.stderr
        """
        sys.stderr.write("OSCServer: %s\n" % txt)
                
    def sendOSCerror(self, txt, client_address):
        """Sends 'txt', encapsulated in an OSCMessage to the default 'error_prefix' OSC-addres.
        Message is sent to the given client_address, with the default 'return_port' overriding
        the client_address' port, if defined.
        """
        lines = txt.split('\n')
        if len(lines) == 1:
            msg = OSCMessage(self.error_prefix)
            msg.append(lines[0])
        elif len(lines) > 1:
            msg = OSCBundle(self.error_prefix)
            for line in lines:
                msg.append(line)
        else:
            return
        
        if self.return_port:
            client_address = (client_address[0], self.return_port)
        
        self.client.sendto(msg, client_address)
    
    def reportErr(self, txt, client_address):
        """Writes 'OSCServer: txt' to sys.stderr
        If self.error_prefix is defined, sends 'txt' as an OSC error-message to the client(s)
        (see printErr() and sendOSCerror())
        """
        self.printErr(txt)
        
        if len(self.error_prefix):
            self.sendOSCerror(txt, client_address)
    
    def sendOSCinfo(self, txt, client_address):
        """Sends 'txt', encapsulated in an OSCMessage to the default 'info_prefix' OSC-addres.
        Message is sent to the given client_address, with the default 'return_port' overriding
        the client_address' port, if defined.
        """
        lines = txt.split('\n')
        if len(lines) == 1:
            msg = OSCMessage(self.info_prefix)
            msg.append(lines[0])
        elif len(lines) > 1:
            msg = OSCBundle(self.info_prefix)
            for line in lines:
                msg.append(line)
        else:
            return
        
        if self.return_port:
            client_address = (client_address[0], self.return_port)
        
        self.client.sendto(msg, client_address)
    
    ###
    # Message-Handler callback functions
    ###
                
    def handle_error(self, request, client_address):
        """Handle an exception in the Server's callbacks gracefully.
        Writes the error to sys.stderr and, if the error_prefix (see setSrvErrorPrefix()) is set,
        sends the error-message as reply to the client
        """
        (e_type, e) = sys.exc_info()[:2]
        self.printErr("%s on request from %s: %s" % (e_type.__name__, getUrlStr(client_address), str(e)))

        if self.print_tracebacks:
            import traceback
            traceback.print_exc() # XXX But this goes to stderr!
        
        if len(self.error_prefix):
            self.sendOSCerror("%s: %s" % (e_type.__name__, str(e)), client_address)
    
    def noCallback_handler(self, addr, tags, data, client_address):
        """Example handler for OSCMessages.
        All registerd handlers must accept these three arguments:
        - addr (string): The OSC-address pattern of the received Message
          (the 'addr' string has already been matched against the handler's registerd OSC-address,
          but may contain '*'s & such)
        - tags (string):  The OSC-typetags of the received message's arguments. (without the preceding comma)
        - data (list): The OSCMessage's arguments
          Note that len(tags) == len(data)
        - client_address ((host, port) tuple): the host & port this message originated from.
        
        a Message-handler function may return None, but it could also return an OSCMessage (or OSCBundle),
        which then gets sent back to the client.
        
        This handler prints a "No callback registered to handle ..." message.
        Returns None
        """
        self.reportErr("No callback registered to handle OSC-address '%s'" % addr, client_address)
        
    def msgPrinter_handler(self, addr, tags, data, client_address):
        """Example handler for OSCMessages.
        All registerd handlers must accept these three arguments:
        - addr (string): The OSC-address pattern of the received Message
          (the 'addr' string has already been matched against the handler's registerd OSC-address,
          but may contain '*'s & such)
        - tags (string):  The OSC-typetags of the received message's arguments. (without the preceding comma)
        - data (list): The OSCMessage's arguments
          Note that len(tags) == len(data)
        - client_address ((host, port) tuple): the host & port this message originated from.
        
        a Message-handler function may return None, but it could also return an OSCMessage (or OSCBundle),
        which then gets sent back to the client.
        
        This handler prints the received message.
        Returns None
        """
        txt = "OSCMessage '%s' from %s: " % (addr, getUrlStr(client_address))
        txt += str(data)
            
        self.printErr(txt)  # strip trailing comma & space
    
    def serverInfo_handler(self, addr, tags, data, client_address):
        """Example handler for OSCMessages.
        All registerd handlers must accept these three arguments:
        - addr (string): The OSC-address pattern of the received Message
          (the 'addr' string has already been matched against the handler's registerd OSC-address,
          but may contain '*'s & such)
        - tags (string):  The OSC-typetags of the received message's arguments. (without the preceding comma)
        - data (list): The OSCMessage's arguments
          Note that len(tags) == len(data)
        - client_address ((host, port) tuple): the host & port this message originated from.
        
        a Message-handler function may return None, but it could also return an OSCMessage (or OSCBundle),
        which then gets sent back to the client.
        
        This handler returns a reply to the client, which can contain various bits of information
        about this server, depending on the first argument of the received OSC-message:
        - 'help' | 'info' :  Reply contains server type & version info, plus a list of 
          available 'commands' understood by this handler
        - 'list' | 'ls' :  Reply is a bundle of 'address <string>' messages, listing the server's 
          OSC address-space.
        - 'clients' | 'targets' :  Reply is a bundle of 'target osc://<host>:<port>[<prefix>] [<filter>] [...]'
          messages, listing the local Client-instance's subscribed remote clients.
        """
        if len(data) == 0:
            return None
        
        cmd = data.pop(0)
        
        reply = None
        if cmd in ('help', 'info'):
            reply = OSCBundle(self.info_prefix)
            reply.append(('server', str(self)))
            reply.append(('info_command', "ls | list : list OSC address-space"))
            reply.append(('info_command', "clients | targets : list subscribed clients"))
        elif cmd in ('ls', 'list'):
            reply = OSCBundle(self.info_prefix)
            for addr in self.callbacks.keys():
                reply.append(('address', addr))
        elif cmd in ('clients', 'targets'):
            if hasattr(self.client, 'getOSCTargetStrings'):
                reply = OSCBundle(self.info_prefix)
                for trg in self.client.getOSCTargetStrings():
                    reply.append(('target',) + trg)
            else:
                cli_addr = self.client.address()
                if cli_addr:
                    reply = OSCMessage(self.info_prefix)
                    reply.append(('target', "osc://%s/" % getUrlStr(cli_addr)))
        else:
            self.reportErr("unrecognized command '%s' in /info request from osc://%s. Try 'help'" % (cmd, getUrlStr(client_address)), client_address)
            
        return reply
    
    def _subscribe(self, data, client_address):
        """Handle the actual subscription. the provided 'data' is concatenated together to form a
        '<host>:<port>[<prefix>] [<filter>] [...]' string, which is then passed to 
        parseUrlStr() & parseFilterStr() to actually retreive <host>, <port>, etc.
        
        This 'long way 'round' approach (almost) guarantees that the subscription works, 
        regardless of how the bits of the <url> are encoded in 'data'. 
        """
        url = ""
        have_port = False
        for item in data:
            if (type(item) == types.IntType) and not have_port:
                url += ":%d" % item
                have_port = True
            elif type(item) in types.StringTypes:
                url += item

        (addr, tail) = parseUrlStr(url)
        (prefix, filters) = parseFilterStr(tail)
        
        if addr != None:
            (host, port) = addr
            if not host:
                host = client_address[0]
            if not port:
                port = client_address[1]
            addr = (host, port)
        else:
            addr = client_address
        
        self.client._setTarget(addr, prefix, filters)
    
        trg = self.client.getOSCTargetStr(addr)
        if trg[0] != None:
            reply = OSCMessage(self.info_prefix)
            reply.append(('target',) + trg)
            return reply
        
    def _unsubscribe(self, data, client_address):
        """Handle the actual unsubscription. the provided 'data' is concatenated together to form a
        '<host>:<port>[<prefix>]' string, which is then passed to 
        parseUrlStr() to actually retreive <host>, <port> & <prefix>.
        
        This 'long way 'round' approach (almost) guarantees that the unsubscription works, 
        regardless of how the bits of the <url> are encoded in 'data'. 
        """
        url = ""
        have_port = False
        for item in data:
            if (type(item) == types.IntType) and not have_port:
                url += ":%d" % item
                have_port = True
            elif type(item) in types.StringTypes:
                url += item

        (addr, _) = parseUrlStr(url)
        
        if addr == None:
            addr = client_address
        else:
            (host, port) = addr
            if not host:
                host = client_address[0]
            if not port:
                try:
                    (host, port) = self.client._searchHostAddr(host)
                except NotSubscribedError:
                    port = client_address[1]
                    
            addr = (host, port)
        
        try:
            self.client._delTarget(addr)
        except NotSubscribedError, e:
            txt = "%s: %s" % (e.__class__.__name__, str(e))
            self.printErr(txt)

            reply = OSCMessage(self.error_prefix)
            reply.append(txt)
            return reply
    
    def subscription_handler(self, addr, tags, data, client_address):
        """Handle 'subscribe' / 'unsubscribe' requests from remote hosts,
        if the local Client supports this (i.e. OSCMultiClient).
        
        Supported commands:
        - 'help' | 'info' :  Reply contains server type & version info, plus a list of 
          available 'commands' understood by this handler
        - 'list' | 'ls' :  Reply is a bundle of 'target osc://<host>:<port>[<prefix>] [<filter>] [...]'
          messages, listing the local Client-instance's subscribed remote clients.
        - '[subscribe | listen | sendto | target] <url> [<filter> ...] :  Subscribe remote client/server at <url>,
          and/or set message-filters for messages being sent to the subscribed host, with the optional <filter>
          arguments. Filters are given as OSC-addresses (or '*') prefixed by a '+' (send matching messages) or
          a '-' (don't send matching messages). The wildcard '*', '+*' or '+/*' means 'send all' / 'filter none',
          and '-*' or '-/*' means 'send none' / 'filter all' (which is not the same as unsubscribing!)
          Reply is an OSCMessage with the (new) subscription; 'target osc://<host>:<port>[<prefix>] [<filter>] [...]' 
        - '[unsubscribe | silence | nosend | deltarget] <url> :  Unsubscribe remote client/server at <url>
          If the given <url> isn't subscribed, a NotSubscribedError-message is printed (and possibly sent)
        
        The <url> given to the subscribe/unsubscribe handler should be of the form:
        '[osc://][<host>][:<port>][<prefix>]', where any or all components can be omitted.
        
        If <host> is not specified, the IP-address of the message's source is used.
        If <port> is not specified, the <host> is first looked up in the list of subscribed hosts, and if found,
        the associated port is used.
        If <port> is not specified and <host> is not yet subscribed, the message's source-port is used.
        If <prefix> is specified on subscription, <prefix> is prepended to the OSC-address of all messages
        sent to the subscribed host.
        If <prefix> is specified on unsubscription, the subscribed host is only unsubscribed if the host, 
        port and prefix all match the subscription.
        If <prefix> is not specified on unsubscription, the subscribed host is unsubscribed if the host and port 
        match the subscription.
        """
        
        addr_cmd = addr.split('/')[-1]
        
        if len(data):
            if data[0] in ('help', 'info'):
                reply = OSCBundle(self.info_prefix)
                reply.append(('server', str(self)))
                reply.append(('subscribe_command', "ls | list : list subscribed targets"))
                reply.append(('subscribe_command', "[subscribe | listen | sendto | target] <url> [<filter> ...] : subscribe to messages, set filters"))
                reply.append(('subscribe_command', "[unsubscribe | silence | nosend | deltarget] <url> : unsubscribe from messages"))
                return reply

            if data[0] in ('ls', 'list'):
                reply = OSCBundle(self.info_prefix)
                for trg in self.client.getOSCTargetStrings():
                    reply.append(('target',) + trg)
                return reply

            if data[0] in ('subscribe', 'listen', 'sendto', 'target'):
                return self._subscribe(data[1:], client_address)

            if data[0] in ('unsubscribe', 'silence', 'nosend', 'deltarget'):
                return self._unsubscribe(data[1:], client_address)
                
        if addr_cmd in ('subscribe', 'listen', 'sendto', 'target'):
            return self._subscribe(data, client_address)
        
        if addr_cmd in ('unsubscribe', 'silence', 'nosend', 'deltarget'):
            return self._unsubscribe(data, client_address)

class ForkingOSCServer(ForkingMixIn, OSCServer):
    """An Asynchronous OSCServer.
    This server forks a new process to handle each incoming request.
    """ 
    # set the RequestHandlerClass, will be overridden by ForkingOSCServer & ThreadingOSCServer
    RequestHandlerClass = ThreadingOSCRequestHandler

class ThreadingOSCServer(ThreadingMixIn, OSCServer):
    """An Asynchronous OSCServer.
    This server starts a new thread to handle each incoming request.
    """ 
    # set the RequestHandlerClass, will be overridden by ForkingOSCServer & ThreadingOSCServer
    RequestHandlerClass = ThreadingOSCRequestHandler

######
#
# OSCError classes
#
######

class OSCError(Exception):
    """Base Class for all OSC-related errors
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class OSCClientError(OSCError):
    """Class for all OSCClient errors
    """
    pass

class OSCServerError(OSCError):
    """Class for all OSCServer errors
    """
    pass

class NoCallbackError(OSCServerError):
    """This error is raised (by an OSCServer) when an OSCMessage with an 'unmatched' address-pattern
    is received, and no 'default' handler is registered.
    """
    def __init__(self, pattern):
        """The specified 'pattern' should be the OSC-address of the 'unmatched' message causing the error to be raised.
        """
        self.message = "No callback registered to handle OSC-address '%s'" % pattern

class NotSubscribedError(OSCClientError):
    """This error is raised (by an OSCMultiClient) when an attempt is made to unsubscribe a host
    that isn't subscribed.
    """
    def __init__(self, addr, prefix=None):
        if prefix:
            url = getUrlStr(addr, prefix)
        else:
            url = getUrlStr(addr, '')

        self.message = "Target osc://%s is not subscribed" % url            


if __name__ == '__main__':

    print 'test'
