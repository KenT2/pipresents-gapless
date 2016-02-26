#!/bin/sh

case "$1" in

   exit)
       # aborting Pi Presents Using SIGTERM
       # receiving SIGTERM cleans up PP and closes any sub-processes and files used.

       # Just print the PID first for debugging
       # pgrep -f /pipresents/pipresents.py

       # sudo is required for when PP is run with sudo
       # pkill sends SIGTERM
       pkill -f /pipresents/pipresents.py
       ;;

   sudo_exit)
       # aborting Pi Presents Using SIGTERM
       # receiving SIGTERM cleans up PP and closes any sub-processes and files used.

       # Just print the PID first for debugging
       # pgrep -f /pipresents/pipresents.py

       # sudo is required for when PP is run with sudo
       # pkill sends SIGTERM
       sudo pkill -f /pipresents/pipresents.py
       ;;
esac

