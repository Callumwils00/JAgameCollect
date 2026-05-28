#! /bin/python
from io import BytesIO
from picamera2 import Picamera2
from sense_hat import SenseHat
import cv2
import json
import time
import numpy as np

tracker = None
STATE_PATH = "data/state.json"
MQTT_SEND_TOPIC = "test/JAgame/toWebPage"

WIDTH = 700
HEIGHT = 700
# To configure the camera
def setup_camera():
    camera = Picamera2()
    config = camera.create_preview_configuration({'format': 'RGB888', 'size': (WIDTH, HEIGHT)})        
    camera.configure(config)
    camera.start()
    return camera

def detectBall(edges = None):
    global tracker
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    largest = max(contours, key=cv2.contourArea)
    print(f"Contours found: {len(contours)}")
def detectBall(edges = None):
    global tracker
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    largest = max(contours, key=cv2.contourArea)
    print(f"Contours found: {len(contours)}")
    if cv2.contourArea(largest) > 20:
        # In python you can assign values to multiple objects using assignment without them being a list or array
        # Here I only want to draw a rectangle around the largest contour, representing the ball... hopefully
        # https://gist.github.com/bigsnarfdude/d811e31ee17495f82f10db12651ae82d
        x, y, w, h = cv2.boundingRect(largest)
        tracker = cv2.TrackerCSRT_create()
        return x, y, w, h, tracker
    if cv2.contourArea(largest) > 20:
        # In python you can assign values to multiple objects using assignment without them being a list or array
        # Here I only want to draw a rectangle around the largest contour, representing the ball... hopefully
        # https://gist.github.com/bigsnarfdude/d811e31ee17495f82f10db12651ae82d
        x, y, w, h = cv2.boundingRect(largest)
        tracker = cv2.TrackerCSRT_create()
        return x, y, w, h, tracker

def trackBall(side, cx, cy, xMin = None, xMax = None, yMin = None, yMax = None, maxScore= 10, statePath = STATE_PATH, mqttTopic = MQTT_SEND_TOPIC):
    global gameData
    global runGame
    
    if side not in ["playerOne", "playerTwo"]:
        warnings.warn("side parameter must be in ['playerOne', 'playerTwo']")
        #return None 

    # Store json key references as strings
    playerName = side + "Name"
    playerScore = side + "Score"
    
    with open(statePath, "r") as f:
        stateData = json.load(f)

    stateData = int(time.time())
    # Using and rather than bitwise &
    
    if xMin < cx < xMax and yMin < cy < yMax: 
        print(f"Somebody Scored")
        
        with open(statePath, "r") as f:
            stateData = json.load(f)

        stateData[playerScore] = int(stateData[playerScore]) + 1
                
        with open(statePath, "w") as f:
            json.dump(stateData, f)

        with open(statePath, "r") as f:
            stateDataJson = json.load(f)
            
            stateData = str(stateDataJson)
            stateData = stateData.replace("'", '"')
            print(stateData)
               
            # If a score field in the state is greater than 10 something has gone wron
            # it is included here as some defensive coding
        if int(stateDataJson[playerScore]) >=  maxScore:

            stateDataJson["winner"] = stateDataJson[playerName]
            with open(statePath, "w") as f:
                json.dump(stateDataJson, f)

            with open(statePath, "r") as f:
                stateDataJson = json.load(f)
            
            stateData = str(stateDataJson)
            stateData = stateData.replace("'", '"')

            status = mqtt_client.publish(mqttTopic, stateData)
            runGame = False  
        else:
            status = mqtt_client.publish(mqttTopic, stateData)

        if status == 0:
            print(f"Sent Message")
        else:
            print(f"No Score")

       # with open(statePath, "r") as f:
        #    stateDataJson = json.load(f)

       # gameData = np.append(gameData, np.array([stateDataJson["PlayerOneName"], stateDataJson["PlayerTwoName"], stateDataJson["ts"],  stateDataJson["playerOneScore"], stateDataJson["playerTwoScore"], None, None]))
       # print(gameData)




def captureData(camera, dataArray):
    # capture a frame
    global tracker # the use of the global keyword means that the global tracker variable is used. This can
    # change outside of the scope of the function
    global runGame
    global gameData
    im = camera.capture_array()
    gray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)#im[:HEIGHT, :]#cv2.cvtColor(im, cv2.COLOR_YUV2GRAY_I420)
    gausBlur = cv2.GaussianBlur(gray, (5, 5), 0)
    # If Canny edge detection is used without applying gaussian bluring, ie. high pass filtering it will
    # pick up too many artifacts
    edges = cv2.Canny(gausBlur, 20, 40)
    output = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    
    if tracker == None:
        x, y, w, h, tracker = detectBall(edges = edges)
        tracker.init(output, (x, y, w, h))
    else:
        sucess, bbox = tracker.update(output)
        if sucess:
            x, y, w, h = (int(v) for v in bbox)
            cx = x + w // 2
            cy = y + h // 2
            cv2.rectangle(output, (x,  y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(output, (cx, cy), 5, (0, 0, 255), -1)
            print(f"Object at: ({cx}, {cy})")
           # Configuring the goal areas 
            (h, w) = im.shape[:2]

            xMin = 0
            xMax = w
            yMin = 0
            yMax = h // 4

            trackBall("playerOne", cx, cy, xMin, xMax, yMin, yMax)

            yMin = (h // 4) * 3
            yMax = h
            trackBall("playerTwo", cx, cy, xMin, xMax, yMin, yMax)

            # By placing the data appending line here, no data is appended when there is a frame with a lost ball. Since the timestamp is captured the scientist will still be able to reconstruct the time series of the ball movement.
     #       gameData = np.append(gameData, np.array([gameData[1], gameData[2], int(time.time()),  stateDataJson["playerOneScore"], stateDataJson["playerTwoScore"], stateDataJson["winner"], None]))


        else:
            tracker = None # The ball is lost so re-detect in the next frame
            cx = None
            cy = None

        
        with open(STATE_PATH, "r") as f:
            stateData = json.load(f)

        gameData = np.append(dataArray, np.array([stateData["playerOneName"], stateData["playerTwoName"], stateData["ts"],  stateData["playerOneScore"], stateData["playerTwoScore"], cx, cy]))
        try:
            cv2.imshow("Camera", output)
        except:
            print(f"Cannot forward to camera over ssh using x11")

