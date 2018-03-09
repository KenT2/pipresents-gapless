# include this script file in autostart to debug pipresents.py running at boot.
# make debug_autostart.sh executale first
/usr/bin/python /home/pi/pipresents/pipresents.py -p pp_mediashow_1p3 -o /home/pi >> /home/pi/pipresents/pp_logs/pp_autostart.txt 2>&1
# /usr/bin/python /home/pi/pipresents/pp_manager.py >> /home/pi/pipresents/pp_logs/pp_manager.txt 2>&1