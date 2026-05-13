## JAgameCollect

This program is the data collection service of the Joint Action game platform and the backend of the corresponding web page (see PowerShift https://github.com/Callumwils00/ScoreBoard).

JAgameCollect uses a raspberrypi to collect visual and gyroscopic information about the Joint action game (See proposal) and send on relevant information to the webpage over MQTT and the database over http. 

### Requirements:

* A raspberrypi compatible with the camera module 3 and the sense hat. This platform was developed on a raspberrypi 4B, but should work on other RPi's with the 40-pin GPIO headers.
 * A camera module 3. You will need to callibrate this for your own experimental setup. A raspberrypi fisheye lense for the camera may also be useful.
 * A sense hat
 * python3 

The lab will need a raspberrypi set up to run JAgameCollect and a separate machine to host the RESTJA API and database. This is because the JAgameCollect program is designed to be run in an always running process using systemd. The API should be hosted on a machine that is never turned off, or on a cloud service. If the experimenter wishes to not run JAgameCollect on systemd they can elect to ssh into the raspberrypi and run the JAgameCollect program manually for each trial. I would recommend, if the lab doesn't want any data leaving the building to use an old machine or SBC that can run Debian Linux or Debian based distro. See the API README, it was developed on Ubuntu 24 and tested using a laptop for hosting.

If the experimenter wishes to monitor the ball tracking computer vision process using their laptop they can ssh in using x11 and allow their laptop to show the computer vision output stream. I have used this for testing using a laptop running Ubuntu linux, other operating systems that run different camera apps may need aditional configuration. 

