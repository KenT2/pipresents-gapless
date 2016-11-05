# include this script file in autostart to debug pp_manager.py running at boot.
# /usr/bin/python /home/pi/pipresents/pipresents.py -p pp_mediashow_1p3 -o /home/pi
# python /home/pi/pipresents/pp_manager.py
/usr/bin/python /home/pi/pipresents/pp_manager.py >> /home/pi/pipresents/pp_logs/pp_manager.txt 2>&1