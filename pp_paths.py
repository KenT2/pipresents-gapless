# This is a module rather than a class because pp_home will be set once at
# startup and then use of other functions can refer to it.

import sys
import os
import time
from pp_utils import Monitor

pp_dir     = sys.path[0]
pp_resource_dir = os.path.join(pp_dir, 'pp_resources')
pp_home    = ""
pp_profile = ""
media_dir  = ""
mon        = Monitor()
self       = type('pp_paths', (object,), {})()  # for monitor to report what we are


def get_home(home=""):
    # get directory containing pp_home from the command,
    # if no home dir is given, default to /home/pi/pp_home
    # if a home dir is given, try:
    #   a) the given home dir
    #   b) a 'pp_home' dir within the given home dir (original PP operation)
    global pp_home
    
    if pp_home:
        return pp_home
    home = home.strip()
    if home == "":
        home_pp = os.path.expanduser('~')+ os.sep+"pp_home"
    else:
        home_pp = home + os.sep + "pp_home"
    mon.log(self,"PP home directory is: " + home + "[" + os.sep + "pp_home]")
    #print "PP home directory is: {0}[{1}pp_home]".format(home, os.sep)
    # check if pp_home exists.
    # try for 10 seconds to allow usb stick to automount
    # fall back to pipresents/pp_home
    pp_home = pp_dir+"/pp_home"
    found = False
    for i in range (1, 2):
        if os.path.exists(home_pp):
            found = True
            pp_home = home_pp
            break
        if os.path.isdir(home):
            if os.path.isdir(home + os.sep + "pp_profiles"):
              found = True
              pp_home = home
              break
            mon.log(self,"Found the home directory, but no subdirectory pp_home or pp_pprofiles at: {0}".format(home, i))
            break  # if we found the parent dir, the media is mounted... retries are not going to fix a missing sub dir
        mon.log(self,"Did not find PP home with {0}pp_home at: {1} ({2} of 10)".format(os.sep, home_pp, i))
        mon.log(self,"Did not find PP home with {0}pp_profiles at: {1} ({2} of 10)".format(os.sep, home, i))
        time.sleep (1)
    if found==True:
        mon.log(self,"Found requested home directory, using: " + pp_home)
        #print "Found pp_home: " + pp_home
        return pp_home
    else:
        mon.err(self,"Failed to find pp_home directory at " + home)
        #self.end('error','Failed to find pp_home')
        return None


def get_profile_dir(home, profile):
    # returns the full path to the directory that contains (or will contain)
    # pp_showlist.json and other files for the profile
    # if the directory doesn't exist, returns None
    global pp_profile
    global pp_profile_dir
    profile = profile.strip()
    if profile != '':
        name = profile
    else:
        name = "pp_profile"   # the default profile
    home = home.strip() + os.sep
    attempts = [ 
        home + "pp_profiles" +os.sep+ name, # with magic intermediate subdir
        home + name,                        # directly under home
        os.getcwd() + os.sep + profile,     # try relative to current working dir
        profile                             # try full path
    ]
    found = None
    for attempt in attempts:
        if os.path.exists(attempt):
            found = attempt
            break
    if found is None:
        mon.err(self,"Failed to find requested profile: \n" + "\n".join(attempts))
    else:
        mon.log(self, "Found requested profile at: " + found)
    pp_profile_dir = found
    pp_profile = name
    return found


def get_dir(path):
    path = get_path(path)
    if path is not None:
        if os.path.isdir(path):
            return path
    return None


def get_file(path):
    path = get_path(path)
    if path is not None:
        if os.path.isfile(path):
            return path
    return None


def get_path(path):
    # find a file from a PiPresents path string 
    #   - might contain '+' to point to the PP_home dir)
    # returns None if file is not found
    home = os.path.abspath(pp_home)
    if path[0] == '+':
        path = path.replace('+', home)
    attempts = [path, os.path.join(home, path)]
    found = None
    for attempt in attempts:
        if os.path.exists(attempt):
            found = attempt
            break
    return found
  