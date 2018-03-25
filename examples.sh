#!/bin/sh
# A launcher I use for the Pi Presents examples
# It is based on the one that launches Python Games; developed by Alex Bradbury
# with contributions from me

RET=0


while [ $RET -eq 0 ]; do
  GAME=$(zenity --width=700 --height=700 --list \
    --title="Pi Presents" \
    --text="Examples of Pi Presents in Operation, CTRL-BREAK to return" \
    --column="Example" --column="Description" \
    pp_mediashow_1p3 "A Repeating multi-media show" \
    pp_interactive_1p3 "An Interactive Show for a Visitor Centre" \
    pp_exhibit_1p3 "A track or show triggered by a button or PIR" \
    pp_openclose_1p3 "Start when the lid is opened, stop on close (requires gpio)" \
    pp_onerandom_1p3 "Trigger one random track" \
    pp_magicpicture_1p3 "Magic Picture" \
    pp_menu_1p3 "Scrolling Menu Kiosk Content Chooser" \
    pp_radiobuttonshow_1p3 "Button operated Kiosk Content Chooser" \
    pp_hyperlinkshow_1p3 "A Touchscreen as seen in Museums" \
    pp_liveshow_1p3 "A multi-media show with dynamically provided content" \
    pp_liveshowempty_1p3 "Liveshow demonstrating the empty list features" \
    pp_presentation_1p3  "Controlling a multi-media show manually" \
    pp_audio_1p3 "Audio Capabilities" \
    pp_web_1p3 "Demonstration of Web Browser Player" \
    pp_concurrent_1p3 "Play many shows simultaneously" \
    pp_multiwindow_1p3 "Many concurrent shows sharing the screen" \
    pp_artmediashow_1p3 "A truly gapless multi-media show without freezes" \
    pp_artliveshow_1p3 "A truly gapless liveshow without freezes" \
    pp_showcontrol_1p3 "Control one show from another" \
    pp_showcontrolevent_1p3 "Sending input events from a show to others" \
    pp_clickarea_1p3 "Touchscreen Click Areas and Soft Keys" \
    pp_timeofday_1p3 "Run shows at specfied times each day" \
    pp_animate_1p3 "Demonstration of Animation Control" \
    pp_subshow_1p3 "Demonstration of Subshows" \
    pp_trackplugin_1p3 "Demonstration of Track Plugins" \
    pp_shutdown_1p3 "Shutdown the Raspberry Pi from Pi Presents" \
    pp_videoplayout_1p3 "Using Pi Presents as a simple video playout system" \
    pp_quiz_1p3 "A simple quiz using a hyperlinkshow and counters" \
    website "pipresents.wordpress.com")
  RET=$?
  echo $RET
  if [ "$RET" -eq 0 ]
  then
     if [ "$GAME" = "website" ]
     then
        sensible-browser "http://pipresents.wordpress.com"
     else
       if [ "$GAME" != "" ]; then
          cd /home/pi/pipresents
          python /home/pi/pipresents/pipresents.py -o /home/pi -p $GAME -bf
       fi
     fi
  fi
done
