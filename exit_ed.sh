#!/bin/sh

case "$1" in

   exit)
       # aborting Editor Using SIGTERM
       # receiving SIGTERM cleans up Web Editor and closes any sub-processes and files used.

       # Just print the PID first for debugging
       # pgrep -f /pipresents/pp_web_editor.py.py

       # sudo is required for when PP is run with sudo
       # pkill sends SIGTERM
       pkill -f /pipresents/pp_web_editor.py
       ;;

   sudo_exit)
       # aborting Web Editor Using SIGTERM
       # receiving SIGTERM cleans up Web Editor and closes any sub-processes and files used.

       # Just print the PID first for debugging
       # pgrep -f /pipresents/pp_web_editor.py

       # sudo is required for when Web editor is run with sudo
       # pkill sends SIGTERM
       sudo pkill -f /pipresents/pp_web_editor.py
       ;;
esac

