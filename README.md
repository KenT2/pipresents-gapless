PI PRESENTS  - Version 1.3.1
============================

Diese Readme-Datei hat Peter Vasen ins Deutsche übersetzt. Klicken Sie hier 
http://www.weser-echo.de/README_Vers_1_3.pdf

This repository contains a beta test version of the next version Pi Presents. The version is a beta as it is likely to have a few bugs and also will be developed further to add new features.


TO UPGRADE FROM VERSION 1.2
============================
To upgrade follow the instructions in the 'Updating Pi Presents' section below. Before doing so keep a copy of the current Pi Presents and all the profiles:


PI PRESENTS
===========
Pi Presents is a toolkit for producing interactive multimedia applications for museums, visitor centres and more. I am involved with a couple of charity organisations that are museums or have visitor centres and have wanted a cost effective way to provide interactive audio interpretation and slide/videoshow displays. Until the Raspberry Pi arrived buying or constructing even sound players was expensive. The Pi with its combination of Linux, GPIO and a powerful GPU is ideal for black box multi-media applications; all it needs is a program to harness its power in a way that could be used by non-programmers.

This second major upgrade of Pi Presents adds three major new features  - multi-window displays running concurrent shows, gapless transition between tracks, and remote control from and of other Pi Presents and with any OSC enabled device. This has entailed a large rewrite and along the way many of the existing features have been improved.

Pi Presents is now a flexible toolkit for interactive display and animation with a large range of features. This large range of features may seem to make it complicated, hopefully not so as most of them are optional.  I have tried to keep it simple for beginners by providing an editor with templates and a set of examples for basic applications. A extensive User Manual is also provided.

The components of Pi Presents are five types of show, four media players for different types of track, a GPIO output sequencer, a time of day scheduler, and something to handle external inputs.  These can be combined using a simple to use editor to serve a great variety of simple or complex applications. Applications include:

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

http://www.weser-echo.de/Pipresents_1_3_1_a_manual_de.pdf


To download Pi Presents including the manual and get going follow the instructions below.


Install required applications (MPlayer, PIL,  X Server utils and font)
------------------------------------------------------

         sudo apt-get update
         sudo apt-get install python-imaging
         sudo apt-get install python-imaging-tk
		 sudo apt-get install unclutter
		 sudo apt-get install mplayer
		 sudo apt-get install uzbl
		 sudo apt-get install ttf-liberation

	   
Download and install pexpect
-----------------------------

Specified here http://www.noah.org/wiki/pexpect#Download_and_Installation and below.

From a terminal window open in your home directory type:

         wget http://pexpect.sourceforge.net/pexpect-2.3.tar.gz
         tar xzf pexpect-2.3.tar.gz
         cd pexpect-2.3
         sudo python ./setup.py install

Return the terminal window to the home directory.
	   
Download Pi Presents
--------------------

Pi Presents MUST use Raspbian and be run from the desktop (startx). From a terminal window open in your home directory type:

         wget https://github.com/KenT2/pipresents-gapless/tarball/master -O - | tar xz

There should now be a directory 'KenT2-pipresents-gapless-xxxx' in your home directory. Rename the directory to pipresents.

To install install icons on your desktop and menu, run the install_desktop_icons.sh script in the pipresents directory.

Run Pi Presents to check the installation is successful. From a terminal window opened in the home directory type:

         python /home/pi/pipresents/pipresents.py

You will see an error message which is because you have no profiles. Exit Pi Presents using CTRL-BREAK or close the window.


Download and try an Example Profile
-----------------------------------

Warning: The download includes a 26MB video file.

Open a terminal window in your home directory and type:

         wget https://github.com/KenT2/pipresents-gapless-examples/tarball/master -O - | tar xz

There should now be a directory 'KenT2-pipresents-gapless-examples-xxxx' in your home directory. Open the directory and move the 'pp_home' directory and its contents to your home directory.

From the terminal window type:

         python /home/pi/pipresents/pipresents.py -p pp_mediashow_1p3
		 
to see a repeating multimedia show.

Now read the manual to try other examples.


Updating Pi Presents from Version 1.2
======================================

Open a terminal window in your home directory and type:

         wget https://github.com/KenT2/pipresents-gapless/tarball/master -O - | tar xz

There should now be a directory 'KenT2-pipresents-gapless-xxxx' in your home directory

Rename the existing pipresents directory to old-pipresents

Rename the new directory to pipresents.

Copy pp_editor.cfg from the old to new /pipresents/pp_config directory.


Getting examples for this version.
----------------------------------

New to this version is a github repository [pipresents-gapless-examples]

Rename the existing pp_home directory to old_pp_home.

Open a terminal window in your home directory and type:

         wget https://github.com/KenT2/pipresents-gapless-examples/tarball/master -O - | tar xz

There should now be a directory 'KenT2-pipresents-gapless-examples-xxxx' in your home directory.

Open the directory and move the 'pp_home' directory and its contents to your home directory.

These examples are compatible with the version of  Pi Presents you have just downloaded. In addition you can update profiles from version 1.2.x [pipresents-next] to 1.3.1 by simply opening them in the editor (make a backup copy first):

In either case you can use the tools>update all menu option to update all profiles in /pp_home

Lastly you will need to do some manual updating of some of the field values as specified in  ReleaseNotes.txt. Start at the paragraph in releasenotes.txt that introduces version 1.3 and work backwards.

I have started a new thread on the forum for [pipresents-gapless], see below.


Requirements
============
Pi Presents was developed on Raspbian using Python 2.7. It is now being developed on Jessie, Wheezy now being obsolescent for over a year. While it will run on a Pi 1, a Pi2 or Pi3 gives much better performance for videos and images. 

omxplayer plays some videos using 64MB of RAM; others need 128MB, especially if you want sub-titles. 


Bug Reports and Feature Requests
================================
I am keen to develop Pi Presents further and would welcome bug reports and ideas for additional features and uses.

Please use the Issues tab on Github https://github.com/KenT2/pipresents-gapless/issues.

For more information on how Pi Presents is being used, Hints and Tips on how to use it and all the latest news hop over to the Pi Presents website http://pipresents.wordpress.com/

