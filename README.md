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

It is assumed that a technicion will set up the experiment and that the experimenter will analyse the data using an api call using Python/MATLAB/R but that outwith analysing their data the experimenter doesn't have programming skills.


## Vision Science problem

We need to find the position of the center of the ball from frame to frame.

## Pipeline

    1. A frame is caputured using the piCamera and the Picamera2 method .capture_array(). This frame will be an array of pixel values from 0 to 255.

### Object ***Detection***

    2. Find the Edges. First the frame is converted to grayscale using the opencv COLOR_RBG2GRAY field [1] and gaussian blur is applied to smooth over some of the small high frequency intensity changes in the frame.

    3. The changes in the intensity of the frame is used to detect edges. Actually canny edge detection is used over laplacian. But the basic idea is that the zero-crossings are found by getting the first derivative of the frame (see Marr Hildreth edge detection [2]  as a starting point, then laplacian and canny edge detection).

    4. The edges are linked up into contours, ie. continuous edges and the largest contour is found. This step is important since artifacts (objects that aren't the ball like where the white paper on the bottom of the surface)  can be and are often detected.

### Object ***Tracking***

    5. An adaption on the MOSSE (Minimum Output Sum of Square error) algorithm [3]  is used to track the ball from frame to frame. This approach (Tracking) is more computationally efficient that running the detection stage alone on ever frame. The basic idea of MOSSE (and CSRT which was actually used) is to learn the object statistics from the first frame captured and then use this found information in subsequent frame, adapting the object statistics from frame to frame, allowing for slight changes (for example how the electrical tape covering the ball creates slight creases which make it not exactly spherical).
    
        - 5.1 If the tracker looses the ball the function goes back to step 2, and detects the ball again.

    
# References 

[2] https://doi.org/10.1098/rspb.1980.0020

[3] https://doi.org/10.1109/CVPR.2010.5539960
