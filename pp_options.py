# Dec 2015 - add --manager option

from pp_utils import Monitor
import argparse

def command_options():
    """ reads the command line options and returns a dictionary of them"""
    debug_no_d=Monitor.m_fatal|Monitor.m_err|Monitor.m_warn
    debug_d=Monitor.m_fatal|Monitor.m_err|Monitor.m_warn|Monitor.m_log
    parser = argparse.ArgumentParser(description = 'Pi Presents multimedia toolkit')
    parser.add_argument( '-b','--noblank', action='store_true', help='Disable screen blanking.')
    parser.add_argument( '-f','--fullscreen', action='store_true',help='Full Screen')
    parser.add_argument( '-s','--screensize', nargs='?',default='',const='',help='Size of target screen w*h')
    parser.add_argument( '-v','--verify', action='store_true',help='Verify Profile')
    parser.add_argument( '-d','--debug', nargs='?', default=debug_no_d, const=debug_d,help='Enable Debug Output [and loglevel]')
    parser.add_argument( '-o','--home', nargs='?', default='', const='',help='Path to pp_home')
    parser.add_argument( '-l','--liveshow', nargs='?', default='', const='',help='Directory1 for live tracks')
    parser.add_argument( '-p','--profile', nargs='?', default='', const='',help='Profile')
    parser.add_argument( '--manager', action='store_true',help='Use With Manager for PiPresents')
    args=parser.parse_args()
    return  vars(args)


def ed_options():
    """ reads the command line options and returns a dictionary of them"""
    parser = argparse.ArgumentParser(description = 'Pi Presents Editor')
    parser.add_argument( '-d','--debug', nargs='?', default='7', const='15',help='Debug output to terminal window')
    parser.add_argument( '--forceupdate', action='store_true',help='Force Update')
    parser.add_argument( '-o','--home', nargs='?', default='', const='',help='Path to pp_home')
    parser.add_argument( '-p','--profile', nargs='?', default='', const='',help='Profile')
    args=parser.parse_args()
    return  vars(args)

def remote_options():
    """ reads the command line options and returns a dictionary of them"""
    parser = argparse.ArgumentParser(description = 'Pi Presents Remote')
    parser.add_argument( '-d','--debug', nargs='?', default='7', const='15',help='Debug output to terminal window')
    args=parser.parse_args()
    return  vars(args)
