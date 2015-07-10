# This is a module rather than a class because pp_home will be set once at
# startup and then use of other functions can refer to it.

import sys
import os
from pp_utils import Monitor

pp_home    = ""
pp_profile = ""
mon        = Monitor()
pp_dir     = sys.path[0]
self       = type('pp_paths', (object,), {})() # for monitor to report what we are

def get_home(home_option):
    # get directory containing pp_home from the command,
    # if no home dir is given, default to /home/pi/pp_home
    # if a home dir is given, try:
    #   a) the given home dir
    #   b) a 'pp_home' dir within the given home dir (original PP operation)
    global pp_home
    
    if home_option == "":
        home    = ""
        home_pp = os.path.expanduser('~')+ os.sep+"pp_home"
    else:
        home    = home_option
        home_pp = home_option + os.sep + "pp_home"
    mon.log(self,"PP home directory is: " + home + "[" + os.sep + "pp_home]")

    # check if pp_home exists.
    # try for 10 seconds to allow usb stick to automount
    # fall back to pipresents/pp_home
    pp_home = pp_dir+"/pp_home"
    found = False
    for i in range (1, 10):
        if os.path.exists(home_pp):
            found = True
            pp_home = home_pp
            break
        if os.path.exists(home):
            if os.path.exists(home + os.sep + "pp_profiles"):
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
        print "Found pp_home: " + pp_home
        return pp_home
    else:
        mon.err(self,"Failed to find pp_home directory at " + home)
        #self.end('error','Failed to find pp_home')
        return None
    
def get_profile_dir(home, profile_option):
    # returns the full path to the directory that contains (or will contain)
    # pp_showlist.json and other files for the profile
    # if the directory doesn't exist, returns None
    if profile_option != '':
        name = profile_option
    else:
        name = "pp_profile"   # the default profile
    home += os.sep
    attempts = [ 
        home + "pp_profiles" +os.sep+ name, # with magic intermediate subdir
        home + name,                        # directly under home
        os.getcwd() + os.sep + profile_option, # try relative to current working dir
        profile_option                      # try full path
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
    return found
    
def get_file(path):
    # find a file from a PiPresents path string 
    #   - might contain '+' to point to the PP_home dir)
    # returns None if file is not found
    home = os.path.abspath(pp_home)
    if path[0] == '+':
        path = path.replace('+', home)
    home += os.sep
    attempts = [ path, home + path ]
    found = None
    for attempt in attempts:
      if os.path.isfile(attempt):
        found = attempt
        break
    return found
  #