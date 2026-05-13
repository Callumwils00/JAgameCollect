## JAgameCollect

This program is the data collection service of the Joint Action game platform and the backend of the corresponding web page (see PowerShift https://github.com/Callumwils00/ScoreBoard).

JAgameCollect uses a raspberrypi to collect visual and gyroscopic information about the Joint action game (See proposal) and send on relevant information to the webpage over MQTT and the database over http. 

### Requirements:

    * A raspberrypi compatible with the camera module 3 and the sense hat. This platform was developed on a raspberrypi 4B, but should work on other RPi's with the 40-pin GPIO headers.
    * A camera module 3. You will need to callibrate this for your own experimental setup. A raspberrypi fisheye lense for the camera may also be useful.
    * A sense hat
    * python3 
