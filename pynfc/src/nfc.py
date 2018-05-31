''' modified by krt for RPi

Wrapper for nfc-emulation.h

Generated with:
/usr/bin/ctypesgen.py -lnfc /usr/include/nfc/nfc-emulation.h /usr/include/nfc/nfc.h /usr/include/nfc/nfc-types.h -o nfc.py

 Do not modify this file.
'''

__docformat__ = 'restructuredtext'

# Begin preamble

import ctypes, os, sys
from ctypes import cast, c_int, c_int16, c_int32, c_uint8, c_uint32, c_int64, c_char, c_char_p, c_size_t, c_void_p, sizeof, Structure, Union, CFUNCTYPE

_int_types = (c_int16, c_int32)
if hasattr(ctypes, 'c_int64'):
    # Some builds of ctypes apparently do not have c_int64
    # defined; it's a pretty good bet that these builds do not
    # have 64-bit pointers.
    _int_types += (c_int64,)
for t in _int_types:
    if sizeof(t) == sizeof(c_size_t):
        c_ptrdiff_t = t
del t
del _int_types

class c_void(Structure):
    # c_void_p is a buggy return type, converting to int, so
    # POINTER(None) == c_void_p is actually written as
    # POINTER(c_void), so it can be treated as a real pointer.
    _fields_ = [('dummy', c_int)]

def POINTER(obj):
    p = ctypes.POINTER(obj)

    # Convert None to a real NULL pointer to work around bugs
    # in how ctypes handles None on 64-bit platforms
    if not isinstance(p.from_param, classmethod):
        def from_param(cls, x):
            if x is None:
                return cls()
            else:
                return x
        p.from_param = classmethod(from_param)

    return p

class UserString:
    def __init__(self, seq):
        if isinstance(seq, basestring):
            self.data = seq
        elif isinstance(seq, UserString):
            self.data = seq.data[:]
        else:
            self.data = str(seq)
    def __str__(self): return str(self.data)
    def __repr__(self): return repr(self.data)
    def __int__(self): return int(self.data)
    def __long__(self): return long(self.data)
    def __float__(self): return float(self.data)
    def __complex__(self): return complex(self.data)
    def __hash__(self): return hash(self.data)

    def __cmp__(self, string):
        if isinstance(string, UserString):
            return cmp(self.data, string.data)
        else:
            return cmp(self.data, string)
    def __contains__(self, char):
        return char in self.data

    def __len__(self): return len(self.data)
    def __getitem__(self, index): return self.__class__(self.data[index])
    def __getslice__(self, start, end):
        start = max(start, 0); end = max(end, 0)
        return self.__class__(self.data[start:end])

    def __add__(self, other):
        if isinstance(other, UserString):
            return self.__class__(self.data + other.data)
        elif isinstance(other, basestring):
            return self.__class__(self.data + other)
        else:
            return self.__class__(self.data + str(other))
    def __radd__(self, other):
        if isinstance(other, basestring):
            return self.__class__(other + self.data)
        else:
            return self.__class__(str(other) + self.data)
    def __mul__(self, n):
        return self.__class__(self.data * n)
    __rmul__ = __mul__
    def __mod__(self, args):
        return self.__class__(self.data % args)

    # the following methods are defined in alphabetical order:
    def capitalize(self): return self.__class__(self.data.capitalize())
    def center(self, width, *args):
        return self.__class__(self.data.center(width, *args))
    def count(self, sub, start = 0, end = sys.maxint):
        return self.data.count(sub, start, end)
    def decode(self, encoding = None, errors = None): # XXX improve this?
        if encoding:
            if errors:
                return self.__class__(self.data.decode(encoding, errors))
            else:
                return self.__class__(self.data.decode(encoding))
        else:
            return self.__class__(self.data.decode())
    def encode(self, encoding = None, errors = None): # XXX improve this?
        if encoding:
            if errors:
                return self.__class__(self.data.encode(encoding, errors))
            else:
                return self.__class__(self.data.encode(encoding))
        else:
            return self.__class__(self.data.encode())
    def endswith(self, suffix, start = 0, end = sys.maxint):
        return self.data.endswith(suffix, start, end)
    def expandtabs(self, tabsize = 8):
        return self.__class__(self.data.expandtabs(tabsize))
    def find(self, sub, start = 0, end = sys.maxint):
        return self.data.find(sub, start, end)
    def index(self, sub, start = 0, end = sys.maxint):
        return self.data.index(sub, start, end)
    def isalpha(self): return self.data.isalpha()
    def isalnum(self): return self.data.isalnum()
    def isdecimal(self): return self.data.isdecimal() #pylint: disable-msg=E1103
    def isdigit(self): return self.data.isdigit()
    def islower(self): return self.data.islower()
    def isnumeric(self): return self.data.isnumeric() #pylint: disable-msg=E1103
    def isspace(self): return self.data.isspace()
    def istitle(self): return self.data.istitle()
    def isupper(self): return self.data.isupper()
    def join(self, seq): return self.data.join(seq)
    def ljust(self, width, *args):
        return self.__class__(self.data.ljust(width, *args))
    def lower(self): return self.__class__(self.data.lower())
    def lstrip(self, chars = None): return self.__class__(self.data.lstrip(chars))
    def partition(self, sep):
        return self.data.partition(sep)
    def replace(self, old, new, maxsplit = -1):
        return self.__class__(self.data.replace(old, new, maxsplit))
    def rfind(self, sub, start = 0, end = sys.maxint):
        return self.data.rfind(sub, start, end)
    def rindex(self, sub, start = 0, end = sys.maxint):
        return self.data.rindex(sub, start, end)
    def rjust(self, width, *args):
        return self.__class__(self.data.rjust(width, *args))
    def rpartition(self, sep):
        return self.data.rpartition(sep)
    def rstrip(self, chars = None): return self.__class__(self.data.rstrip(chars))
    def split(self, sep = None, maxsplit = -1):
        return self.data.split(sep, maxsplit)
    def rsplit(self, sep = None, maxsplit = -1):
        return self.data.rsplit(sep, maxsplit)
    def splitlines(self, keepends = 0): return self.data.splitlines(keepends)
    def startswith(self, prefix, start = 0, end = sys.maxint):
        return self.data.startswith(prefix, start, end)
    def strip(self, chars = None): return self.__class__(self.data.strip(chars))
    def swapcase(self): return self.__class__(self.data.swapcase())
    def title(self): return self.__class__(self.data.title())
    def translate(self, *args):
        return self.__class__(self.data.translate(*args))
    def upper(self): return self.__class__(self.data.upper())
    def zfill(self, width): return self.__class__(self.data.zfill(width))

class MutableString(UserString):
    """mutable string objects

    Python strings are immutable objects.  This has the advantage, that
    strings may be used as dictionary keys.  If this property isn't needed
    and you insist on changing string values in place instead, you may cheat
    and use MutableString.

    But the purpose of this class is an educational one: to prevent
    people from inventing their own mutable string class derived
    from UserString and than forget thereby to remove (override) the
    __hash__ method inherited from UserString.  This would lead to
    errors that would be very hard to track down.

    A faster and better solution is to rewrite your program using lists."""
    def __init__(self, string = ""):
        self.data = string
    def __hash__(self):
        raise TypeError("unhashable type (it is mutable)")
    def __setitem__(self, index, sub):
        if index < 0:
            index += len(self.data)
        if index < 0 or index >= len(self.data): raise IndexError
        self.data = self.data[:index] + sub + self.data[index + 1:]
    def __delitem__(self, index):
        if index < 0:
            index += len(self.data)
        if index < 0 or index >= len(self.data): raise IndexError
        self.data = self.data[:index] + self.data[index + 1:]
    def __setslice__(self, start, end, sub):
        start = max(start, 0); end = max(end, 0)
        if isinstance(sub, UserString):
            self.data = self.data[:start] + sub.data + self.data[end:]
        elif isinstance(sub, basestring):
            self.data = self.data[:start] + sub + self.data[end:]
        else:
            self.data = self.data[:start] + str(sub) + self.data[end:]
    def __delslice__(self, start, end):
        start = max(start, 0); end = max(end, 0)
        self.data = self.data[:start] + self.data[end:]
    def immutable(self):
        return UserString(self.data)
    def __iadd__(self, other):
        if isinstance(other, UserString):
            self.data += other.data
        elif isinstance(other, basestring):
            self.data += other
        else:
            self.data += str(other)
        return self
    def __imul__(self, n):
        self.data *= n
        return self

class String(MutableString, Union):

    _fields_ = [('raw', POINTER(c_char)),
                ('data', c_char_p)]

    def __init__(self, obj = ""):
        if isinstance(obj, (str, unicode, UserString)):
            self.data = str(obj)
        else:
            self.raw = obj

    def __len__(self):
        return self.data and len(self.data) or 0

    def from_param(cls, obj):
        # Convert None or 0
        if obj is None or obj == 0:
            return cls(POINTER(c_char)())

        # Convert from String
        elif isinstance(obj, String):
            return obj

        # Convert from str
        elif isinstance(obj, str):
            return cls(obj)

        # Convert from c_char_p
        elif isinstance(obj, c_char_p):
            return obj

        # Convert from POINTER(c_char)
        elif isinstance(obj, POINTER(c_char)):
            return obj

        # Convert from raw pointer
        elif isinstance(obj, int):
            return cls(cast(obj, POINTER(c_char)))

        # Convert from object
        else:
            return String.from_param(obj._as_parameter_)
    from_param = classmethod(from_param)

def ReturnString(obj, func = None, arguments = None):
    return String.from_param(obj)

# As of ctypes 1.0, ctypes does not support custom error-checking
# functions on callbacks, nor does it support custom datatypes on
# callbacks, so we must ensure that all callbacks return
# primitive datatypes.
#
# Non-primitive return values wrapped with UNCHECKED won't be
# typechecked, and will be converted to c_void_p.
def UNCHECKED(type):
    if (hasattr(type, "_type_") and isinstance(type._type_, str)
        and type._type_ != "P"):
        return type
    else:
        return c_void_p

# ctypes doesn't have direct support for variadic functions, so we have to write
# our own wrapper class
class _variadic_function(object):
    def __init__(self, func, restype, argtypes):
        self.func = func
        self.func.restype = restype
        self.argtypes = argtypes
    def _as_parameter_(self):
        # So we can pass this variadic function as a function pointer
        return self.func
    def __call__(self, *args):
        fixed_args = []
        i = 0
        for argtype in self.argtypes:
            # Typecheck what we can
            fixed_args.append(argtype.from_param(args[i]))
            i += 1
        return self.func(*fixed_args + list(args[i:]))

# End preamble

_libs = {}
_libdirs = []

# Begin loader

# ----------------------------------------------------------------------------
# Copyright (c) 2008 David James
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

import os.path, re, sys, glob
import platform
import ctypes
import ctypes.util

def _environ_path(name):
    if name in os.environ:
        return os.environ[name].split(":")
    else:
        return []

class LibraryLoader(object):
    def __init__(self):
        self.other_dirs = []

    def load_library(self, libname):
        """Given the name of a library, load it."""
        paths = self.getpaths(libname)

        for path in paths:
            if os.path.exists(path):
                return self.load(path)

        raise ImportError("%s not found." % libname)

    def load(self, path):
        """Given a path to a library, load it."""
        try:
            # Darwin requires dlopen to be called with mode RTLD_GLOBAL instead
            # of the default RTLD_LOCAL.  Without this, you end up with
            # libraries not being loadable, resulting in "Symbol not found"
            # errors
            if sys.platform == 'darwin':
                return ctypes.CDLL(path, ctypes.RTLD_GLOBAL)
            else:
                return ctypes.cdll.LoadLibrary(path)
        except OSError, e:
            raise ImportError(e)

    def getpaths(self, libname):
        """Return a list of paths where the library might be found."""
        if os.path.isabs(libname):
            yield libname
        else:
            # FIXME / TODO return '.' and os.path.dirname(__file__)
            for path in self.getplatformpaths(libname):
                yield path

            path = ctypes.util.find_library(libname)
            if path: yield path

    def getplatformpaths(self, libname):
        return []

# Darwin (Mac OS X)

class DarwinLibraryLoader(LibraryLoader):
    name_formats = ["lib%s.dylib", "lib%s.so", "lib%s.bundle", "%s.dylib",
                "%s.so", "%s.bundle", "%s"]

    def getplatformpaths(self, libname):
        if os.path.pathsep in libname:
            names = [libname]
        else:
            names = [format % libname for format in self.name_formats]

        for dir in self.getdirs(libname):
            for name in names:
                yield os.path.join(dir, name)

    def getdirs(self, libname):
        '''Implements the dylib search as specified in Apple documentation:

        http://developer.apple.com/documentation/DeveloperTools/Conceptual/
            DynamicLibraries/Articles/DynamicLibraryUsageGuidelines.html

        Before commencing the standard search, the method first checks
        the bundle's ``Frameworks`` directory if the application is running
        within a bundle (OS X .app).
        '''

        dyld_fallback_library_path = _environ_path("DYLD_FALLBACK_LIBRARY_PATH")
        if not dyld_fallback_library_path:
            dyld_fallback_library_path = [os.path.expanduser('~/lib'),
                                          '/usr/local/lib', '/usr/lib']

        dirs = []

        if '/' in libname:
            dirs.extend(_environ_path("DYLD_LIBRARY_PATH"))
        else:
            dirs.extend(_environ_path("LD_LIBRARY_PATH"))
            dirs.extend(_environ_path("DYLD_LIBRARY_PATH"))

        dirs.extend(self.other_dirs)
        dirs.append(".")
        dirs.append(os.path.dirname(__file__))

        if hasattr(sys, 'frozen') and sys.frozen == 'macosx_app': #pylint: disable-msg=E1101
            dirs.append(os.path.join(
                os.environ['RESOURCEPATH'],
                '..',
                'Frameworks'))

        dirs.extend(dyld_fallback_library_path)

        return dirs

# Posix

class PosixLibraryLoader(LibraryLoader):
    _ld_so_cache = None

    def _create_ld_so_cache(self):
        # Recreate search path followed by ld.so.  This is going to be
        # slow to build, and incorrect (ld.so uses ld.so.cache, which may
        # not be up-to-date).  Used only as fallback for distros without
        # /sbin/ldconfig.
        #
        # We assume the DT_RPATH and DT_RUNPATH binary sections are omitted.

        directories = []
        for name in ("LD_LIBRARY_PATH",
                     "SHLIB_PATH", # HPUX
                     "LIBPATH", # OS/2, AIX
                     "LIBRARY_PATH", # BE/OS
                    ):
            if name in os.environ:
                directories.extend(os.environ[name].split(os.pathsep))
        directories.extend(self.other_dirs)
        directories.append(".")
        directories.append(os.path.dirname(__file__))

        try: directories.extend([dir.strip() for dir in open('/etc/ld.so.conf.d/arm-linux-gnueabihf.conf')])
        except IOError: pass

        unix_lib_dirs_list = ['/lib', '/usr/lib', '/lib64', '/usr/lib64']
        if sys.platform.startswith('linux'):
            # Try and support multiarch work in Ubuntu
            # https://wiki.ubuntu.com/MultiarchSpec
            bitage = platform.architecture()[0]
            if bitage.startswith('32'):
                # Assume Intel/AMD x86 compat
                unix_lib_dirs_list += ['/lib/i386-linux-gnu', '/usr/lib/i386-linux-gnu']
            elif bitage.startswith('64'):
                # Assume Intel/AMD x86 compat
                unix_lib_dirs_list += ['/lib/x86_64-linux-gnu', '/usr/lib/x86_64-linux-gnu']
            else:
                # guess...
                unix_lib_dirs_list += glob.glob('/lib/*linux-gnu')
        directories.extend(unix_lib_dirs_list)

        cache = {}
        lib_re = re.compile(r'lib(.*)\.s[ol]')
        ext_re = re.compile(r'\.s[ol]$')
        for dir in directories:
            try:
                for path in glob.glob("%s/*.s[ol]*" % dir):
                    file = os.path.basename(path)

                    # Index by filename
                    if file not in cache:
                        cache[file] = path

                    # Index by library name
                    match = lib_re.match(file)
                    if match:
                        library = match.group(1)
                        if library not in cache:
                            cache[library] = path
            except OSError:
                pass

        self._ld_so_cache = cache

    def getplatformpaths(self, libname):
        if self._ld_so_cache is None:
            self._create_ld_so_cache()

        result = self._ld_so_cache.get(libname)
        if result: yield result

        path = ctypes.util.find_library(libname)
        if path: yield os.path.join("/lib", path)

# Windows

class _WindowsLibrary(object):
    def __init__(self, path):
        self.cdll = ctypes.cdll.LoadLibrary(path)
        self.windll = ctypes.windll.LoadLibrary(path)

    def __getattr__(self, name):
        try: return getattr(self.cdll, name)
        except AttributeError:
            try: return getattr(self.windll, name)
            except AttributeError:
                raise

class WindowsLibraryLoader(LibraryLoader):
    name_formats = ["%s.dll", "lib%s.dll", "%slib.dll"]

    def load_library(self, libname):
        try:
            result = LibraryLoader.load_library(self, libname)
        except ImportError:
            result = None
            if os.path.sep not in libname:
                for name in self.name_formats:
                    try:
                        result = getattr(ctypes.cdll, name % libname)
                        if result:
                            break
                    except ImportError:
                        result = None
            if result is None:
                try:
                    result = getattr(ctypes.cdll, libname)
                except ImportError:
                    result = None
            if result is None:
                raise ImportError("%s not found." % libname)
        return result

    def load(self, path):
        return _WindowsLibrary(path)

    def getplatformpaths(self, libname):
        if os.path.sep not in libname:
            for name in self.name_formats:
                dll_in_current_dir = os.path.abspath(name % libname)
                if os.path.exists(dll_in_current_dir):
                    yield dll_in_current_dir
                path = ctypes.util.find_library(name % libname)
                if path:
                    yield path

# Platform switching

# If your value of sys.platform does not appear in this dict, please contact
# the Ctypesgen maintainers.

loaderclass = {
    "darwin":   DarwinLibraryLoader,
    "cygwin":   WindowsLibraryLoader,
    "win32":    WindowsLibraryLoader
}

loader = loaderclass.get(sys.platform, PosixLibraryLoader)()

def add_library_search_dirs(other_dirs):
    loader.other_dirs = other_dirs

load_library = loader.load_library

del loaderclass

# End loader

add_library_search_dirs([])

# Begin libraries

_libs["nfc"] = load_library("nfc")

# 1 libraries
# End libraries

# No modules

# /usr/include/nfc/nfc-types.h: 42
class struct_nfc_context(Structure):
    _pack_ = 1

nfc_context = struct_nfc_context # /usr/include/nfc/nfc-types.h: 42

# /usr/include/nfc/nfc-types.h: 47
class struct_nfc_device(Structure):
    _pack_ = 1

nfc_device = struct_nfc_device # /usr/include/nfc/nfc-types.h: 47

# /usr/include/nfc/nfc-types.h: 52
class struct_nfc_driver(Structure):
    _pack_ = 1

nfc_driver = struct_nfc_driver # /usr/include/nfc/nfc-types.h: 52

nfc_connstring = c_char * 1024 # /usr/include/nfc/nfc-types.h: 57

enum_anon_18 = c_int # /usr/include/nfc/nfc-types.h: 137

NP_TIMEOUT_COMMAND = 0 # /usr/include/nfc/nfc-types.h: 137

NP_TIMEOUT_ATR = (NP_TIMEOUT_COMMAND + 1) # /usr/include/nfc/nfc-types.h: 137

NP_TIMEOUT_COM = (NP_TIMEOUT_ATR + 1) # /usr/include/nfc/nfc-types.h: 137

NP_HANDLE_CRC = (NP_TIMEOUT_COM + 1) # /usr/include/nfc/nfc-types.h: 137

NP_HANDLE_PARITY = (NP_HANDLE_CRC + 1) # /usr/include/nfc/nfc-types.h: 137

NP_ACTIVATE_FIELD = (NP_HANDLE_PARITY + 1) # /usr/include/nfc/nfc-types.h: 137

NP_ACTIVATE_CRYPTO1 = (NP_ACTIVATE_FIELD + 1) # /usr/include/nfc/nfc-types.h: 137

NP_INFINITE_SELECT = (NP_ACTIVATE_CRYPTO1 + 1) # /usr/include/nfc/nfc-types.h: 137

NP_ACCEPT_INVALID_FRAMES = (NP_INFINITE_SELECT + 1) # /usr/include/nfc/nfc-types.h: 137

NP_ACCEPT_MULTIPLE_FRAMES = (NP_ACCEPT_INVALID_FRAMES + 1) # /usr/include/nfc/nfc-types.h: 137

NP_AUTO_ISO14443_4 = (NP_ACCEPT_MULTIPLE_FRAMES + 1) # /usr/include/nfc/nfc-types.h: 137

NP_EASY_FRAMING = (NP_AUTO_ISO14443_4 + 1) # /usr/include/nfc/nfc-types.h: 137

NP_FORCE_ISO14443_A = (NP_EASY_FRAMING + 1) # /usr/include/nfc/nfc-types.h: 137

NP_FORCE_ISO14443_B = (NP_FORCE_ISO14443_A + 1) # /usr/include/nfc/nfc-types.h: 137

NP_FORCE_SPEED_106 = (NP_FORCE_ISO14443_B + 1) # /usr/include/nfc/nfc-types.h: 137

nfc_property = enum_anon_18 # /usr/include/nfc/nfc-types.h: 137

enum_anon_19 = c_int # /usr/include/nfc/nfc-types.h: 150

NDM_UNDEFINED = 0 # /usr/include/nfc/nfc-types.h: 150

NDM_PASSIVE = (NDM_UNDEFINED + 1) # /usr/include/nfc/nfc-types.h: 150

NDM_ACTIVE = (NDM_PASSIVE + 1) # /usr/include/nfc/nfc-types.h: 150

nfc_dep_mode = enum_anon_19 # /usr/include/nfc/nfc-types.h: 150

# /usr/include/nfc/nfc-types.h: 174
class struct_anon_20(Structure):
    _pack_ = 1

struct_anon_20.__slots__ = [
    'abtNFCID3',
    'btDID',
    'btBS',
    'btBR',
    'btTO',
    'btPP',
    'abtGB',
    'szGB',
    'ndm',
]
struct_anon_20._fields_ = [
    ('abtNFCID3', c_uint8 * 10),
    ('btDID', c_uint8),
    ('btBS', c_uint8),
    ('btBR', c_uint8),
    ('btTO', c_uint8),
    ('btPP', c_uint8),
    ('abtGB', c_uint8 * 48),
    ('szGB', c_size_t),
    ('ndm', nfc_dep_mode),
]

nfc_dep_info = struct_anon_20 # /usr/include/nfc/nfc-types.h: 174

# /usr/include/nfc/nfc-types.h: 187
class struct_anon_21(Structure):
    _pack_ = 1

struct_anon_21.__slots__ = [
    'abtAtqa',
    'btSak',
    'szUidLen',
    'abtUid',
    'szAtsLen',
    'abtAts',
]
struct_anon_21._fields_ = [
    ('abtAtqa', c_uint8 * 2),
    ('btSak', c_uint8),
    ('szUidLen', c_size_t),
    ('abtUid', c_uint8 * 10),
    ('szAtsLen', c_size_t),
    ('abtAts', c_uint8 * 254),
]

nfc_iso14443a_info = struct_anon_21 # /usr/include/nfc/nfc-types.h: 187

# /usr/include/nfc/nfc-types.h: 199
class struct_anon_22(Structure):
    _pack_ = 1

struct_anon_22.__slots__ = [
    'szLen',
    'btResCode',
    'abtId',
    'abtPad',
    'abtSysCode',
]
struct_anon_22._fields_ = [
    ('szLen', c_size_t),
    ('btResCode', c_uint8),
    ('abtId', c_uint8 * 8),
    ('abtPad', c_uint8 * 8),
    ('abtSysCode', c_uint8 * 2),
]

nfc_felica_info = struct_anon_22 # /usr/include/nfc/nfc-types.h: 199

# /usr/include/nfc/nfc-types.h: 214
class struct_anon_23(Structure):
    _pack_ = 1

struct_anon_23.__slots__ = [
    'abtPupi',
    'abtApplicationData',
    'abtProtocolInfo',
    'ui8CardIdentifier',
]
struct_anon_23._fields_ = [
    ('abtPupi', c_uint8 * 4),
    ('abtApplicationData', c_uint8 * 4),
    ('abtProtocolInfo', c_uint8 * 3),
    ('ui8CardIdentifier', c_uint8),
]

nfc_iso14443b_info = struct_anon_23 # /usr/include/nfc/nfc-types.h: 214

# /usr/include/nfc/nfc-types.h: 230
class struct_anon_24(Structure):
    _pack_ = 1

struct_anon_24.__slots__ = [
    'abtDIV',
    'btVerLog',
    'btConfig',
    'szAtrLen',
    'abtAtr',
]
struct_anon_24._fields_ = [
    ('abtDIV', c_uint8 * 4),
    ('btVerLog', c_uint8),
    ('btConfig', c_uint8),
    ('szAtrLen', c_size_t),
    ('abtAtr', c_uint8 * 33),
]

nfc_iso14443bi_info = struct_anon_24 # /usr/include/nfc/nfc-types.h: 230

# /usr/include/nfc/nfc-types.h: 238
class struct_anon_25(Structure):
    _pack_ = 1

struct_anon_25.__slots__ = [
    'abtUID',
]
struct_anon_25._fields_ = [
    ('abtUID', c_uint8 * 8),
]

nfc_iso14443b2sr_info = struct_anon_25 # /usr/include/nfc/nfc-types.h: 238

# /usr/include/nfc/nfc-types.h: 248
class struct_anon_26(Structure):
    _pack_ = 1

struct_anon_26.__slots__ = [
    'abtUID',
    'btProdCode',
    'btFabCode',
]
struct_anon_26._fields_ = [
    ('abtUID', c_uint8 * 4),
    ('btProdCode', c_uint8),
    ('btFabCode', c_uint8),
]

nfc_iso14443b2ct_info = struct_anon_26 # /usr/include/nfc/nfc-types.h: 248

# /usr/include/nfc/nfc-types.h: 257
class struct_anon_27(Structure):
    _pack_ = 1

struct_anon_27.__slots__ = [
    'btSensRes',
    'btId',
]
struct_anon_27._fields_ = [
    ('btSensRes', c_uint8 * 2),
    ('btId', c_uint8 * 4),
]

nfc_jewel_info = struct_anon_27 # /usr/include/nfc/nfc-types.h: 257

# /usr/include/nfc/nfc-types.h: 272
class union_anon_28(Union):
    _pack_ = 1

union_anon_28.__slots__ = [
    'nai',
    'nfi',
    'nbi',
    'nii',
    'nsi',
    'nci',
    'nji',
    'ndi',
]
union_anon_28._fields_ = [
    ('nai', nfc_iso14443a_info),
    ('nfi', nfc_felica_info),
    ('nbi', nfc_iso14443b_info),
    ('nii', nfc_iso14443bi_info),
    ('nsi', nfc_iso14443b2sr_info),
    ('nci', nfc_iso14443b2ct_info),
    ('nji', nfc_jewel_info),
    ('ndi', nfc_dep_info),
]

nfc_target_info = union_anon_28 # /usr/include/nfc/nfc-types.h: 272

enum_anon_29 = c_int # /usr/include/nfc/nfc-types.h: 284

NBR_UNDEFINED = 0 # /usr/include/nfc/nfc-types.h: 284

NBR_106 = (NBR_UNDEFINED + 1) # /usr/include/nfc/nfc-types.h: 284

NBR_212 = (NBR_106 + 1) # /usr/include/nfc/nfc-types.h: 284

NBR_424 = (NBR_212 + 1) # /usr/include/nfc/nfc-types.h: 284

NBR_847 = (NBR_424 + 1) # /usr/include/nfc/nfc-types.h: 284

nfc_baud_rate = enum_anon_29 # /usr/include/nfc/nfc-types.h: 284

enum_anon_30 = c_int # /usr/include/nfc/nfc-types.h: 299

NMT_ISO14443A = 1 # /usr/include/nfc/nfc-types.h: 299

NMT_JEWEL = (NMT_ISO14443A + 1) # /usr/include/nfc/nfc-types.h: 299

NMT_ISO14443B = (NMT_JEWEL + 1) # /usr/include/nfc/nfc-types.h: 299

NMT_ISO14443BI = (NMT_ISO14443B + 1) # /usr/include/nfc/nfc-types.h: 299

NMT_ISO14443B2SR = (NMT_ISO14443BI + 1) # /usr/include/nfc/nfc-types.h: 299

NMT_ISO14443B2CT = (NMT_ISO14443B2SR + 1) # /usr/include/nfc/nfc-types.h: 299

NMT_FELICA = (NMT_ISO14443B2CT + 1) # /usr/include/nfc/nfc-types.h: 299

NMT_DEP = (NMT_FELICA + 1) # /usr/include/nfc/nfc-types.h: 299

nfc_modulation_type = enum_anon_30 # /usr/include/nfc/nfc-types.h: 299

enum_anon_31 = c_int # /usr/include/nfc/nfc-types.h: 308

N_TARGET = 0 # /usr/include/nfc/nfc-types.h: 308

N_INITIATOR = (N_TARGET + 1) # /usr/include/nfc/nfc-types.h: 308

nfc_mode = enum_anon_31 # /usr/include/nfc/nfc-types.h: 308

# /usr/include/nfc/nfc-types.h: 317
class struct_anon_32(Structure):
    _pack_ = 1

struct_anon_32.__slots__ = [
    'nmt',
    'nbr',
]
struct_anon_32._fields_ = [
    ('nmt', nfc_modulation_type),
    ('nbr', nfc_baud_rate),
]

nfc_modulation = struct_anon_32 # /usr/include/nfc/nfc-types.h: 317

# /usr/include/nfc/nfc-types.h: 326
class struct_anon_33(Structure):
    _pack_ = 1

struct_anon_33.__slots__ = [
    'nti',
    'nm',
]
struct_anon_33._fields_ = [
    ('nti', nfc_target_info),
    ('nm', nfc_modulation),
]

nfc_target = struct_anon_33 # /usr/include/nfc/nfc-types.h: 326

# /usr/include/nfc/nfc.h: 80
if hasattr(_libs['nfc'], 'nfc_init'):
    nfc_init = _libs['nfc'].nfc_init
    nfc_init.argtypes = [POINTER(POINTER(nfc_context))]
    nfc_init.restype = None

# /usr/include/nfc/nfc.h: 81
if hasattr(_libs['nfc'], 'nfc_exit'):
    nfc_exit = _libs['nfc'].nfc_exit
    nfc_exit.argtypes = [POINTER(nfc_context)]
    nfc_exit.restype = None

# /usr/include/nfc/nfc.h: 82
if hasattr(_libs['nfc'], 'nfc_register_driver'):
    nfc_register_driver = _libs['nfc'].nfc_register_driver
    nfc_register_driver.argtypes = [POINTER(nfc_driver)]
    nfc_register_driver.restype = c_int

# /usr/include/nfc/nfc.h: 85
if hasattr(_libs['nfc'], 'nfc_open'):
    nfc_open = _libs['nfc'].nfc_open
    nfc_open.argtypes = [POINTER(nfc_context), nfc_connstring]
    nfc_open.restype = POINTER(nfc_device)

# /usr/include/nfc/nfc.h: 86
if hasattr(_libs['nfc'], 'nfc_close'):
    nfc_close = _libs['nfc'].nfc_close
    nfc_close.argtypes = [POINTER(nfc_device)]
    nfc_close.restype = None

# /usr/include/nfc/nfc.h: 87
if hasattr(_libs['nfc'], 'nfc_abort_command'):
    nfc_abort_command = _libs['nfc'].nfc_abort_command
    nfc_abort_command.argtypes = [POINTER(nfc_device)]
    nfc_abort_command.restype = c_int

# /usr/include/nfc/nfc.h: 88
if hasattr(_libs['nfc'], 'nfc_list_devices'):
    nfc_list_devices = _libs['nfc'].nfc_list_devices
    nfc_list_devices.argtypes = [POINTER(nfc_context), POINTER(nfc_connstring), c_size_t]
    nfc_list_devices.restype = c_size_t

# /usr/include/nfc/nfc.h: 89
if hasattr(_libs['nfc'], 'nfc_idle'):
    nfc_idle = _libs['nfc'].nfc_idle
    nfc_idle.argtypes = [POINTER(nfc_device)]
    nfc_idle.restype = c_int

# /usr/include/nfc/nfc.h: 92
if hasattr(_libs['nfc'], 'nfc_initiator_init'):
    nfc_initiator_init = _libs['nfc'].nfc_initiator_init
    nfc_initiator_init.argtypes = [POINTER(nfc_device)]
    nfc_initiator_init.restype = c_int

# /usr/include/nfc/nfc.h: 93
if hasattr(_libs['nfc'], 'nfc_initiator_init_secure_element'):
    nfc_initiator_init_secure_element = _libs['nfc'].nfc_initiator_init_secure_element
    nfc_initiator_init_secure_element.argtypes = [POINTER(nfc_device)]
    nfc_initiator_init_secure_element.restype = c_int

# /usr/include/nfc/nfc.h: 94
if hasattr(_libs['nfc'], 'nfc_initiator_select_passive_target'):
    nfc_initiator_select_passive_target = _libs['nfc'].nfc_initiator_select_passive_target
    nfc_initiator_select_passive_target.argtypes = [POINTER(nfc_device), nfc_modulation, POINTER(c_uint8), c_size_t, POINTER(nfc_target)]
    nfc_initiator_select_passive_target.restype = c_int

# /usr/include/nfc/nfc.h: 95
if hasattr(_libs['nfc'], 'nfc_initiator_list_passive_targets'):
    nfc_initiator_list_passive_targets = _libs['nfc'].nfc_initiator_list_passive_targets
    nfc_initiator_list_passive_targets.argtypes = [POINTER(nfc_device), nfc_modulation, POINTER(nfc_target), c_size_t]
    nfc_initiator_list_passive_targets.restype = c_int

# /usr/include/nfc/nfc.h: 96
if hasattr(_libs['nfc'], 'nfc_initiator_poll_target'):
    nfc_initiator_poll_target = _libs['nfc'].nfc_initiator_poll_target
    nfc_initiator_poll_target.argtypes = [POINTER(nfc_device), POINTER(nfc_modulation), c_size_t, c_uint8, c_uint8, POINTER(nfc_target)]
    nfc_initiator_poll_target.restype = c_int

# /usr/include/nfc/nfc.h: 97
if hasattr(_libs['nfc'], 'nfc_initiator_select_dep_target'):
    nfc_initiator_select_dep_target = _libs['nfc'].nfc_initiator_select_dep_target
    nfc_initiator_select_dep_target.argtypes = [POINTER(nfc_device), nfc_dep_mode, nfc_baud_rate, POINTER(nfc_dep_info), POINTER(nfc_target), c_int]
    nfc_initiator_select_dep_target.restype = c_int

# /usr/include/nfc/nfc.h: 98
if hasattr(_libs['nfc'], 'nfc_initiator_poll_dep_target'):
    nfc_initiator_poll_dep_target = _libs['nfc'].nfc_initiator_poll_dep_target
    nfc_initiator_poll_dep_target.argtypes = [POINTER(nfc_device), nfc_dep_mode, nfc_baud_rate, POINTER(nfc_dep_info), POINTER(nfc_target), c_int]
    nfc_initiator_poll_dep_target.restype = c_int

# /usr/include/nfc/nfc.h: 99
if hasattr(_libs['nfc'], 'nfc_initiator_deselect_target'):
    nfc_initiator_deselect_target = _libs['nfc'].nfc_initiator_deselect_target
    nfc_initiator_deselect_target.argtypes = [POINTER(nfc_device)]
    nfc_initiator_deselect_target.restype = c_int

# /usr/include/nfc/nfc.h: 100
if hasattr(_libs['nfc'], 'nfc_initiator_transceive_bytes'):
    nfc_initiator_transceive_bytes = _libs['nfc'].nfc_initiator_transceive_bytes
    nfc_initiator_transceive_bytes.argtypes = [POINTER(nfc_device), POINTER(c_uint8), c_size_t, POINTER(c_uint8), c_size_t, c_int]
    nfc_initiator_transceive_bytes.restype = c_int

# /usr/include/nfc/nfc.h: 101
if hasattr(_libs['nfc'], 'nfc_initiator_transceive_bits'):
    nfc_initiator_transceive_bits = _libs['nfc'].nfc_initiator_transceive_bits
    nfc_initiator_transceive_bits.argtypes = [POINTER(nfc_device), POINTER(c_uint8), c_size_t, POINTER(c_uint8), POINTER(c_uint8), c_size_t, POINTER(c_uint8)]
    nfc_initiator_transceive_bits.restype = c_int

# /usr/include/nfc/nfc.h: 102
if hasattr(_libs['nfc'], 'nfc_initiator_transceive_bytes_timed'):
    nfc_initiator_transceive_bytes_timed = _libs['nfc'].nfc_initiator_transceive_bytes_timed
    nfc_initiator_transceive_bytes_timed.argtypes = [POINTER(nfc_device), POINTER(c_uint8), c_size_t, POINTER(c_uint8), c_size_t, POINTER(c_uint32)]
    nfc_initiator_transceive_bytes_timed.restype = c_int

# /usr/include/nfc/nfc.h: 103
if hasattr(_libs['nfc'], 'nfc_initiator_transceive_bits_timed'):
    nfc_initiator_transceive_bits_timed = _libs['nfc'].nfc_initiator_transceive_bits_timed
    nfc_initiator_transceive_bits_timed.argtypes = [POINTER(nfc_device), POINTER(c_uint8), c_size_t, POINTER(c_uint8), POINTER(c_uint8), c_size_t, POINTER(c_uint8), POINTER(c_uint32)]
    nfc_initiator_transceive_bits_timed.restype = c_int

# /usr/include/nfc/nfc.h: 104
if hasattr(_libs['nfc'], 'nfc_initiator_target_is_present'):
    nfc_initiator_target_is_present = _libs['nfc'].nfc_initiator_target_is_present
    nfc_initiator_target_is_present.argtypes = [POINTER(nfc_device), nfc_target]
    nfc_initiator_target_is_present.restype = c_int

# /usr/include/nfc/nfc.h: 107
if hasattr(_libs['nfc'], 'nfc_target_init'):
    nfc_target_init = _libs['nfc'].nfc_target_init
    nfc_target_init.argtypes = [POINTER(nfc_device), POINTER(nfc_target), POINTER(c_uint8), c_size_t, c_int]
    nfc_target_init.restype = c_int

# /usr/include/nfc/nfc.h: 108
if hasattr(_libs['nfc'], 'nfc_target_send_bytes'):
    nfc_target_send_bytes = _libs['nfc'].nfc_target_send_bytes
    nfc_target_send_bytes.argtypes = [POINTER(nfc_device), POINTER(c_uint8), c_size_t, c_int]
    nfc_target_send_bytes.restype = c_int

# /usr/include/nfc/nfc.h: 109
if hasattr(_libs['nfc'], 'nfc_target_receive_bytes'):
    nfc_target_receive_bytes = _libs['nfc'].nfc_target_receive_bytes
    nfc_target_receive_bytes.argtypes = [POINTER(nfc_device), POINTER(c_uint8), c_size_t, c_int]
    nfc_target_receive_bytes.restype = c_int

# /usr/include/nfc/nfc.h: 110
if hasattr(_libs['nfc'], 'nfc_target_send_bits'):
    nfc_target_send_bits = _libs['nfc'].nfc_target_send_bits
    nfc_target_send_bits.argtypes = [POINTER(nfc_device), POINTER(c_uint8), c_size_t, POINTER(c_uint8)]
    nfc_target_send_bits.restype = c_int

# /usr/include/nfc/nfc.h: 111
if hasattr(_libs['nfc'], 'nfc_target_receive_bits'):
    nfc_target_receive_bits = _libs['nfc'].nfc_target_receive_bits
    nfc_target_receive_bits.argtypes = [POINTER(nfc_device), POINTER(c_uint8), c_size_t, POINTER(c_uint8)]
    nfc_target_receive_bits.restype = c_int

# /usr/include/nfc/nfc.h: 114
if hasattr(_libs['nfc'], 'nfc_strerror'):
    nfc_strerror = _libs['nfc'].nfc_strerror
    nfc_strerror.argtypes = [POINTER(nfc_device)]
    if sizeof(c_int) == sizeof(c_void_p):
        nfc_strerror.restype = ReturnString
    else:
        nfc_strerror.restype = String
        nfc_strerror.errcheck = ReturnString

# /usr/include/nfc/nfc.h: 115
if hasattr(_libs['nfc'], 'nfc_strerror_r'):
    nfc_strerror_r = _libs['nfc'].nfc_strerror_r
    nfc_strerror_r.argtypes = [POINTER(nfc_device), String, c_size_t]
    nfc_strerror_r.restype = c_int

# /usr/include/nfc/nfc.h: 116
if hasattr(_libs['nfc'], 'nfc_perror'):
    nfc_perror = _libs['nfc'].nfc_perror
    nfc_perror.argtypes = [POINTER(nfc_device), String]
    nfc_perror.restype = None

# /usr/include/nfc/nfc.h: 117
if hasattr(_libs['nfc'], 'nfc_device_get_last_error'):
    nfc_device_get_last_error = _libs['nfc'].nfc_device_get_last_error
    nfc_device_get_last_error.argtypes = [POINTER(nfc_device)]
    nfc_device_get_last_error.restype = c_int

# /usr/include/nfc/nfc.h: 120
if hasattr(_libs['nfc'], 'nfc_device_get_name'):
    nfc_device_get_name = _libs['nfc'].nfc_device_get_name
    nfc_device_get_name.argtypes = [POINTER(nfc_device)]
    if sizeof(c_int) == sizeof(c_void_p):
        nfc_device_get_name.restype = ReturnString
    else:
        nfc_device_get_name.restype = String
        nfc_device_get_name.errcheck = ReturnString

# /usr/include/nfc/nfc.h: 121
if hasattr(_libs['nfc'], 'nfc_device_get_connstring'):
    nfc_device_get_connstring = _libs['nfc'].nfc_device_get_connstring
    nfc_device_get_connstring.argtypes = [POINTER(nfc_device)]
    if sizeof(c_int) == sizeof(c_void_p):
        nfc_device_get_connstring.restype = ReturnString
    else:
        nfc_device_get_connstring.restype = String
        nfc_device_get_connstring.errcheck = ReturnString

# /usr/include/nfc/nfc.h: 122
if hasattr(_libs['nfc'], 'nfc_device_get_supported_modulation'):
    nfc_device_get_supported_modulation = _libs['nfc'].nfc_device_get_supported_modulation
    nfc_device_get_supported_modulation.argtypes = [POINTER(nfc_device), nfc_mode, POINTER(POINTER(nfc_modulation_type))]
    nfc_device_get_supported_modulation.restype = c_int

# /usr/include/nfc/nfc.h: 123
if hasattr(_libs['nfc'], 'nfc_device_get_supported_baud_rate'):
    nfc_device_get_supported_baud_rate = _libs['nfc'].nfc_device_get_supported_baud_rate
    nfc_device_get_supported_baud_rate.argtypes = [POINTER(nfc_device), nfc_modulation_type, POINTER(POINTER(nfc_baud_rate))]
    nfc_device_get_supported_baud_rate.restype = c_int

# /usr/include/nfc/nfc.h: 126
if hasattr(_libs['nfc'], 'nfc_device_set_property_int'):
    nfc_device_set_property_int = _libs['nfc'].nfc_device_set_property_int
    nfc_device_set_property_int.argtypes = [POINTER(nfc_device), nfc_property, c_int]
    nfc_device_set_property_int.restype = c_int

# /usr/include/nfc/nfc.h: 127
if hasattr(_libs['nfc'], 'nfc_device_set_property_bool'):
    nfc_device_set_property_bool = _libs['nfc'].nfc_device_set_property_bool
    nfc_device_set_property_bool.argtypes = [POINTER(nfc_device), nfc_property, c_uint8]
    nfc_device_set_property_bool.restype = c_int

# /usr/include/nfc/nfc.h: 130
if hasattr(_libs['nfc'], 'iso14443a_crc'):
    iso14443a_crc = _libs['nfc'].iso14443a_crc
    iso14443a_crc.argtypes = [POINTER(c_uint8), c_size_t, POINTER(c_uint8)]
    iso14443a_crc.restype = None

# /usr/include/nfc/nfc.h: 131
if hasattr(_libs['nfc'], 'iso14443a_crc_append'):
    iso14443a_crc_append = _libs['nfc'].iso14443a_crc_append
    iso14443a_crc_append.argtypes = [POINTER(c_uint8), c_size_t]
    iso14443a_crc_append.restype = None

# /usr/include/nfc/nfc.h: 132
if hasattr(_libs['nfc'], 'iso14443a_locate_historical_bytes'):
    iso14443a_locate_historical_bytes = _libs['nfc'].iso14443a_locate_historical_bytes
    iso14443a_locate_historical_bytes.argtypes = [POINTER(c_uint8), c_size_t, POINTER(c_size_t)]
    iso14443a_locate_historical_bytes.restype = POINTER(c_uint8)

# /usr/include/nfc/nfc.h: 134
if hasattr(_libs['nfc'], 'nfc_free'):
    nfc_free = _libs['nfc'].nfc_free
    nfc_free.argtypes = [POINTER(None)]
    nfc_free.restype = None

# /usr/include/nfc/nfc.h: 135
if hasattr(_libs['nfc'], 'nfc_version'):
    nfc_version = _libs['nfc'].nfc_version
    nfc_version.argtypes = []
    if sizeof(c_int) == sizeof(c_void_p):
        nfc_version.restype = ReturnString
    else:
        nfc_version.restype = String
        nfc_version.errcheck = ReturnString

# /usr/include/nfc/nfc.h: 136
if hasattr(_libs['nfc'], 'nfc_device_get_information_about'):
    nfc_device_get_information_about = _libs['nfc'].nfc_device_get_information_about
    nfc_device_get_information_about.argtypes = [POINTER(nfc_device), POINTER(POINTER(c_char))]
    nfc_device_get_information_about.restype = c_int

# /usr/include/nfc/nfc.h: 139
if hasattr(_libs['nfc'], 'str_nfc_modulation_type'):
    str_nfc_modulation_type = _libs['nfc'].str_nfc_modulation_type
    str_nfc_modulation_type.argtypes = [nfc_modulation_type]
    if sizeof(c_int) == sizeof(c_void_p):
        str_nfc_modulation_type.restype = ReturnString
    else:
        str_nfc_modulation_type.restype = String
        str_nfc_modulation_type.errcheck = ReturnString

# /usr/include/nfc/nfc.h: 140
if hasattr(_libs['nfc'], 'str_nfc_baud_rate'):
    str_nfc_baud_rate = _libs['nfc'].str_nfc_baud_rate
    str_nfc_baud_rate.argtypes = [nfc_baud_rate]
    if sizeof(c_int) == sizeof(c_void_p):
        str_nfc_baud_rate.restype = ReturnString
    else:
        str_nfc_baud_rate.restype = String
        str_nfc_baud_rate.errcheck = ReturnString

# /usr/include/nfc/nfc.h: 141
if hasattr(_libs['nfc'], 'str_nfc_target'):
    str_nfc_target = _libs['nfc'].str_nfc_target
    str_nfc_target.argtypes = [POINTER(POINTER(c_char)), nfc_target, c_uint8]
    str_nfc_target.restype = c_int

# /usr/include/nfc/nfc-emulation.h: 43
class struct_nfc_emulator(Structure):
    _pack_ = 1

# /usr/include/nfc/nfc-emulation.h: 53
class struct_nfc_emulation_state_machine(Structure):
    _pack_ = 1

struct_nfc_emulator.__slots__ = [
    'target',
    'state_machine',
    'user_data',
]
struct_nfc_emulator._fields_ = [
    ('target', POINTER(nfc_target)),
    ('state_machine', POINTER(struct_nfc_emulation_state_machine)),
    ('user_data', POINTER(None)),
]

struct_nfc_emulation_state_machine.__slots__ = [
    'io',
    'data',
]
struct_nfc_emulation_state_machine._fields_ = [
    ('io', CFUNCTYPE(UNCHECKED(c_int), POINTER(struct_nfc_emulator), POINTER(c_uint8), c_size_t, POINTER(c_uint8), c_size_t)),
    ('data', POINTER(None)),
]

# /usr/include/nfc/nfc-emulation.h: 58
if hasattr(_libs['nfc'], 'nfc_emulate_target'):
    nfc_emulate_target = _libs['nfc'].nfc_emulate_target
    nfc_emulate_target.argtypes = [POINTER(nfc_device), POINTER(struct_nfc_emulator), c_int]
    nfc_emulate_target.restype = c_int

# /usr/include/nfc/nfc-types.h: 36
try:
    NFC_BUFSIZE_CONNSTRING = 1024
except:
    pass

# /usr/include/nfc/nfc.h: 62
def __has_attribute(x):
    return 0

# /usr/include/nfc/nfc.h: 148
try:
    NFC_SUCCESS = 0
except:
    pass

# /usr/include/nfc/nfc.h: 153
try:
    NFC_EIO = (-1)
except:
    pass

# /usr/include/nfc/nfc.h: 158
try:
    NFC_EINVARG = (-2)
except:
    pass

# /usr/include/nfc/nfc.h: 163
try:
    NFC_EDEVNOTSUPP = (-3)
except:
    pass

# /usr/include/nfc/nfc.h: 168
try:
    NFC_ENOTSUCHDEV = (-4)
except:
    pass

# /usr/include/nfc/nfc.h: 173
try:
    NFC_EOVFLOW = (-5)
except:
    pass

# /usr/include/nfc/nfc.h: 178
try:
    NFC_ETIMEOUT = (-6)
except:
    pass

# /usr/include/nfc/nfc.h: 183
try:
    NFC_EOPABORTED = (-7)
except:
    pass

# /usr/include/nfc/nfc.h: 188
try:
    NFC_ENOTIMPL = (-8)
except:
    pass

# /usr/include/nfc/nfc.h: 193
try:
    NFC_ETGRELEASED = (-10)
except:
    pass

# /usr/include/nfc/nfc.h: 198
try:
    NFC_ERFTRANS = (-20)
except:
    pass

# /usr/include/nfc/nfc.h: 203
try:
    NFC_EMFCAUTHFAIL = (-30)
except:
    pass

# /usr/include/nfc/nfc.h: 208
try:
    NFC_ESOFT = (-80)
except:
    pass

# /usr/include/nfc/nfc.h: 213
try:
    NFC_ECHIP = (-90)
except:
    pass

nfc_context = struct_nfc_context # /usr/include/nfc/nfc-types.h: 42

nfc_device = struct_nfc_device # /usr/include/nfc/nfc-types.h: 47

nfc_driver = struct_nfc_driver # /usr/include/nfc/nfc-types.h: 52

nfc_emulator = struct_nfc_emulator # /usr/include/nfc/nfc-emulation.h: 43

nfc_emulation_state_machine = struct_nfc_emulation_state_machine # /usr/include/nfc/nfc-emulation.h: 53

# No inserted files

