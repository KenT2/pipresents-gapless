import argparse

def command_options():
    """ reads the command line options and returns a dictionary of them"""
    parser = argparse.ArgumentParser(description = 'Pi presents presentation package')
    parser.add_argument( '-b','--noblank', action='store_true', help='Disable screen blanking.')
    parser.add_argument( '-f','--fullscreen', action='store_true', help='Full Screen')
    parser.add_argument( '-g','--gpio', action='store_true',help='Use GPIO')
    parser.add_argument( '-v','--verify', action='store_true',help='Verify Profile')
    parser.add_argument( '-d','--debug', action='store_true',help='Debug output to terminal window')
    parser.add_argument( '-o','--home', nargs='?', default='', const='',help='Path to pp_home')
    parser.add_argument( '-l','--liveshow', nargs='?', default='', const='',help='Directory for live tracks')
    parser.add_argument( '-p','--profile', nargs='?', default='', const='',help='Profile')
    args=parser.parse_args()
    return  vars(args)


def ed_options():
    """ reads the command line options and returns a dictionary of them"""
    parser = argparse.ArgumentParser(description = 'Pi Presents Editor')
    parser.add_argument( '-d','--debug', action='store_true',help='Debug output to terminal window')
    parser.add_argument( '--forceupdate', action='store_true',help='Force Update')
    args=parser.parse_args()
    return  vars(args)
