#!/bin/sh

# simple example of how to run and exit Pi Presents from a shell script.
# my shell scripting is almost non-existent so beware. The main aim of the script is to
# demonstrate how to start and exit Pi Presents from other applications

# examples:
# ./pp_control.sh run "-p myprofile -b"
# ./pp_control.sh exit


case "$1" in

   run)
       echo "run"
       echo "python /home/pi/pipresents/pipresents.py " "$2"
       python /home/pi/pipresents/pipresents.py $2 > /dev/null &
       echo $!
       ;;


   exit)
       echo "exit"
       # aborting Pi Presents Using SIGTERM
       # receiving SIGTERM cleans up PP and closes any sub-processes and files used.

       # Just print the PID first for debugging
       pgrep -f /pipresents/pipresents.py

       pkill -f /pipresents/pipresents.py
       ;;
esac

