PI PRESENTS  - Version 1.3.2
============================

Diese Readme-Datei hat Peter Vasen ins Deutsche übersetzt. Klicken Sie hier 
http://www.web-echo.de/4.html

This repository contains a beta test version of the next version Pi Presents. The version is a beta as it is likely to have a few bugs and also will be developed further to add new features.

TO UPGRADE FROM VERSION 1.2 [PIPRESENTS-NEXT]
============================
To upgrade follow the instructions in the 'Updating Pi Presents' section below. Then you will need to read the section of the manual on update from 1.2 to 1.3 and Release Notes for all 1.3x versions. Before doing so keep a copy of the current Pi Presents and all the profiles:

TO UPGRADE FROM VERSION 1.3.1 (PIPRESENTS-GAPLESS)
======================================
To upgrade follow the instructions in the 'Updating Pi Presents' section below. Then follow the instructions in the Release Notes


PI PRESENTS
===========
Pi Presents is a toolkit for producing interactive multimedia applications for museums, visitor centres and more. I am involved with a couple of charity organisations that are museums or have visitor centres and have wanted a cost effective way to provide interactive audio interpretation and slide/videoshow displays. Until the Raspberry Pi arrived buying or constructing even sound players was expensive. The Pi with its combination of Linux, GPIO and a powerful GPU is ideal for black box multi-media applications; all it needs is a program to harness its power in a way that could be used by non-programmers.

Pi Presents is now a flexible toolkit for interactive display and animation with a large range of features. This large range of features may seem to make it complicated, hopefully not so as most of them are optional.  I have tried to keep it simple for beginners by providing an editor with templates and a set of examples for basic applications. A extensive User Manual is also provided.

The components of Pi Presents are five types of show, four media players for different types of track, a GPIO output sequencer, a time of day scheduler, and something to handle external inputs.  These can be combined using a simple to use web based editor to serve a great variety of simple or complex applications. Applications include:

*	Audio-visual interpretation of exhibits by triggering a sound, video, or slideshow from GPIO, keyboard or buttons.

*	A repeating media show for a visitor centre. Images, videos, audio tracks, and messages can be displayed. Different shows can be scheduled at specified times of day.

*	Allow media shows to be interrupted by the visitor and a menu of shows or tracks to be presented.

*	Showing 'Powerpoint' like presentations where progress is controlled by buttons or keyboard. The presentation may include images, text, audio tracks and videos.

*   Control animation of exhibits by switching GPIO outputs synchronised with the playing of tracks.

*   A dynamic show capability (Liveshow) in which tracks to be played can be included and deleted while the show is running.

* A button controlled content chooser for kiosks.

* A touchscreen hyperlink navigation system as seen in many museums.

There are potentially many applications of Pi Presents and your input on real world experiences would be invaluable to me, both minor tweaks to the existing functionality and major improvements.

Licence
=======

See the licence.md file. Pi Presents is Careware to help support a small museum charity of which I am a Trustee and who are busy building themselves a larger premises http://www.museumoftechnology.org.uk  Particularly if you are using Pi Presents in a profit making situation a donation would be appreciated.

Installation
============

The full manual in English is here https://github.com/KenT2/pipresents-gapless/blob/master/manual.pdf

There is a German version of the manual written by Peter Vasen ( http://www.web-echo.de/ ) you can download it here

http://www.web-echo.de/4.html


To download Pi Presents including the manual and get going follow the instructions below.

Set the GPU Memory size to 256MB
---------------------------------
Using the Raspbian menu preferences>raspberry pi configuration>performance, increase the GPU Memory to 256.

Ensure Raspbian is up to date.
-------------------------------
Pi Presents MUST have the latest version of omxplayer and of Raspbian, get this by

		sudo apt-get update
		sudo apt-get upgrade

Install required applications 
-----------------------------
         sudo apt-get install python-pexpect
         sudo apt-get install python-imaging
         sudo apt-get install python-imaging-tk
		 sudo apt-get install unclutter
		 sudo apt-get install mplayer
		 sudo apt-get install uzbl

	   
	   
Download Pi Presents
--------------------
Requirements:

	* must use the latest version of Raspbian Stretch
	* must be run from the PIXEL desktop.
	* must be installed and run from user Pi

From a terminal window open in your home directory type:

         wget https://github.com/KenT2/pipresents-gapless/tarball/master -O - | tar xz

There should now be a directory 'KenT2-pipresents-gapless-xxxx' in your /home/pi directory. Copy or rename the directory to pipresents

Run Pi Presents to check the installation is successful. From a terminal window opened in the home directory type:

         python /home/pi/pipresents/pipresents.py

You will see an error message which is because you have no profiles. Exit Pi Presents using CTRL-BREAK or close the window.


Download and try an Example Profile
-----------------------------------

Warning: The download includes a 26MB video file.

Open a terminal window in your home directory and type:

         wget https://github.com/KenT2/pipresents-gapless-examples/tarball/master -O - | tar xz

There should now be a directory 'KenT2-pipresents-gapless-examples-xxxx' in the /home/pi directory. Open the directory and move the 'pp_home' directory and its contents to the home/pi directory.

From the terminal window type:

         python /home/pi/pipresents/pipresents.py -p pp_mediashow_1p3
		 
to see a repeating multimedia show.

Now read the manual to try other examples.


Updating Pi Presents from earlier Versions
======================================

Open a terminal window in the /home/pi and type:

         wget https://github.com/KenT2/pipresents-gapless/tarball/master -O - | tar xz

There should now be a directory 'KenT2-pipresents-gapless-xxxx' in the /home/pi directory

Rename the existing pipresents directory to old-pipresents

Rename the new directory to pipresents.

Copy pp_editor.cfg, pp_web.cfg, pp_email.cfg, keys.cfg, pp_oscmonitor.cfg, and pp_osc_remote.cfg from the old to new /pipresents/pp_config directory.


Getting examples for this version.
----------------------------------

Updated in this version is a github repository [pipresents-gapless-examples]

Rename the existing pp_home directory to old_pp_home.

Open a terminal window in your home directory and type:

         wget https://github.com/KenT2/pipresents-gapless-examples/tarball/master -O - | tar xz

There should now be a directory 'KenT2-pipresents-gapless-examples-xxxx' in the /home/pi directory.

Open the directory and move the 'pp_home' directory and its contents to the /home/pi directory.

These examples are compatible with the version of Pi Presents you have just downloaded. In addition you can update profiles from version 1.3.1 or earlier to 1.3.2 by simply opening them in the editor (make a backup copy first):

In either case you can use the tools>update all menu option to update all profiles in a single directory at once.

Lastly you will need to do some manual updating of some of the field values as specified in  ReleaseNotes.txt. Start at the paragraph in releasenotes.txt that introduces version 1.3.1 and work forwards



Requirements
============
Pi Presents was developed on Raspbian using Python 2.7. It is now being developed on Stretch and will not work on Wheezy or Jessie. While it will run on a Pi 1, a Pi2 or Pi3 gives much better performance for the starting of videos and images. 

If you want to play videos omxplayer requires 256MB of GPU memory. 


Bug Reports and Feature Requests
================================
I am keen to develop Pi Presents further and would welcome bug reports and ideas for additional features and uses.

Please use the Issues tab on Github https://github.com/KenT2/pipresents-gapless/issues.

For more information on how Pi Presents is being used, Hints and Tips on how to use it and all the latest news hop over to the Pi Presents website http://pipresents.wordpress.com/

