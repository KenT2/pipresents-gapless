PI PRESENTS  - Version 1.3.5
============================

Diese Readme-Datei hat Peter Vasen ins Deutsche übersetzt. Klicken Sie hier 
http://www.web-echo.de/4.html

This repository contains the stable version Pi Presents. The version  will not be developed further other than bug and compatibility fixes.


TO INSTALL PIPRESENTS-GAPLESS
=============================

Read the 'Installling Pi Presents Gapless' section below.

TO UPGRADE FROM VERSION 1.2 [PIPRESENTS-NEXT]
=============================================
Read the file upgrade_1p2_1p3.txt


TO UPGRADE FROM EARLIER VERSIONS OF PIPRESENTS-GAPLESS
======================================================
To upgrade follow the instructions in the 'Updating Pi Presents' section below. Then follow any instructions in the Release Notes.


PI PRESENTS
===========

Pi Presents is a toolkit for producing interactive multimedia applications for museums, visitor centres, and more.

There are a number of Digital Signage solutions for the Raspberry Pi which are generally browser based, limited to slideshows, non-interactive, and driven from a central server enabling the content to be modified frequently.

Pi Presents is different, it is stand alone, multi-media, highly interactive, diverse in it set of control paradigms – slideshow, cursor controlled menu, radio button, and hyperlinked show, and able to interface with users or machines over several types of interface. It is aimed primarly at curated applications in museums, science centres, and visitor centres.

Being so flexible Pi Presents needs to be configured for your application. This is achieved using a simple to use graphical editor and needs no Python programming. There are numerous tutorial examples and a comprehensive manual.

There are two versions of Pi Presents. ‘Gapless’ is the current stable version. ‘Next’ is now 3 years old and missing many of the refinements and later developments. This will be supported until June 2019.

For a detailed list of applications and features see here:

          https://pipresents.wordpress.com/features/



Licence
=======

See the licence.md file. Pi Presents is Careware to help support a small museum charity of which I am a Trustee http://www.museumoftechnology.org.uk  Particularly if you are using Pi Presents in a profit making situation a donation would be appreciated.


Installing Pi Presents Gapless
===============================

The full manual in English is here https://github.com/KenT2/pipresents-gapless/blob/master/manual.pdf. It will be downloaded with Pi Presents.

There is a German version of the manual written by Peter Vasen ( http://www.web-echo.de/ ) you can download it here

http://www.web-echo.de/4.html


Requirements
-------------

	* must use the latest version of Raspbian Stretch with Desktop (not the Lite version)
	* must be run from the PIXEL desktop.
	* must be installed and run from user Pi


Set the GPU Memory size to 256MB
---------------------------------
Using the Raspbian menu preferences>raspberry pi configuration>performance, increase the GPU Memory to 256.


Ensure Raspbian is up to date.
-------------------------------
Pi Presents MUST have the latest version of omxplayer and of Raspbian, get this by

		sudo apt-get update
		sudo apt-get upgrade

Install required packages 
-----------------------------
         sudo apt-get install python-imaging
         sudo apt-get install python-imaging-tk
         sudo apt-get install unclutter
         sudo apt-get install mplayer
         sudo apt-get install uzbl
         sudo apt-get install python-pexpect
		 
Install optional packages
------------------------------
         sudo pip install evdev  (if you are using the input device I/O plugin)

	   
Download Pi Presents Gapless
----------------------------

From a terminal window open in your home directory type:

         wget https://github.com/KenT2/pipresents-gapless/tarball/master -O - | tar xz     # -O is a capital Ohhh...

There should now be a directory 'KenT2-pipresents-gapless-xxxx' in your /home/pi directory. Copy or rename the directory to pipresents

Run Pi Presents to check the installation is successful. From a terminal window opened in the home directory type:

         python /home/pi/pipresents/pipresents.py

You will see a window with an error message which is because you have no profiles.Click OK to exit Pi Presents.


Download and try an Example Profile
-----------------------------------

Examples are in the github repository pipresents-gapless-examples.

Open a terminal window in your home directory and type:

         wget https://github.com/KenT2/pipresents-gapless-examples/tarball/master -O - | tar xz

There should now be a directory 'KenT2-pipresents-gapless-examples-xxxx' in the /home/pi directory. Open the directory and move the 'pp_home' directory and its contents to the /home/pi directory.

From the terminal window type:

         python /home/pi/pipresents/pipresents.py -p pp_mediashow_1p3
		 
to see a repeating multimedia show

Exit this with CTRL-BREAK or closing the window, then:

          python /home/pi/pipresents/pipresents.py -p pp_mediashow_1p3 -f -b
		  
to display full screen and to disable screen blanking


Now read the manual to try other examples.


Updating Pi Presents from earlier Versions of Pi Presents Gapless
=================================================================

Open a terminal window in the /home/pi and type:

         wget https://github.com/KenT2/pipresents-gapless/tarball/master -O - | tar xz

There should now be a directory 'KenT2-pipresents-gapless-xxxx' in the /home/pi directory

Rename the existing pipresents directory to old-pipresents

Rename the new directory to pipresents.

Copy pp_editor.cfg, pp_web.cfg, pp_email.cfg, pp_oscmonitor.cfg, and pp_oscremote.cfg from the old to new /pipresents/pp_config directory.


Getting examples for this version.
----------------------------------

Examples are in the github repository pipresents-gapless-examples.

Rename the existing pp_home directory to old_pp_home.

Open a terminal window in your home directory and type:

         wget https://github.com/KenT2/pipresents-gapless-examples/tarball/master -O - | tar xz

There should now be a directory 'KenT2-pipresents-gapless-examples-xxxx' in the /home/pi directory.

Open the directory and move the 'pp_home' directory and its contents to the /home/pi directory.

These examples are compatible with the version of Pi Presents you have just downloaded. In addition you can update profiles from earlier 1.3.x versions by simply opening them in the editor (make a backup copy first).

You can use the update>update all menu option of the editor to update all profiles in a single directory at once.

Lastly you will need to do some manual updating of some of the field values as specified in  ReleaseNotes.txt. Start at the paragraph in ReleaseNotes.txt that introduces your previous version and work forwards



Bug Reports and Feature Requests
================================
I am keen to develop Pi Presents further and would welcome bug reports and ideas for additional features and uses.

Please use the Issues tab on Github https://github.com/KenT2/pipresents-gapless/issues.

For more information on how Pi Presents is being used, Hints and Tips on how to use it and all the latest news hop over to the Pi Presents website https://pipresents.wordpress.com/

