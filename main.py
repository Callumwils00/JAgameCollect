#! /bin/python
import json
from sense_hat import SenseHat
from io import BytesIO
import cv2
import time
import sys
import pandas as pd
import numpy as np
import paho.mqtt.client as mqtt
from picamera2 import Picamera2
import warnings
import requests

MQTT_BROKER = "broker.hivemq.com"
# The MQTT port here is different to the port referenced in the web page (8884)
# That is because this program can send to the MQTT broker directly since it isn't sending
# from a web browser like the webpage that needs to use websockets.
MQTT_PORT = 1883
MQTT_TOPIC = "test/JAgame/fromWebPage"
MQTT_SEND_TOPIC = "test/JAgame/toWebPage"
STATE_PATH = "data/state.json"

# There's a problem to solve regarding launching the data collection process,
# We only want it to kick off after the players have input their names and started the game,
# and to cleanly exit after the game has finished
# Since this is a prototype I choose to use global variables that are switched from False to 
# true when the game has started and ended respectively
runGame = False
endProgram = False

sense = SenseHat()
my_stream = BytesIO()
camera = Picamera2()
WIDTH = 700
HEIGHT = 700
config = camera.create_preview_configuration({'format': 'RGB888', 'size': (WIDTH, HEIGHT)})
camera.configure(config)
camera.start()
tracker = None

# Initalise an empty numpy array 

gameData = np.array([[], [], [], [], [], [],[]])

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

            stateDataJson["winner"] = playerName
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




def captureData():
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

        gameData = np.append(gameData, np.array([stateData["PlayerOneName"], stateData["PlayerTwoName"], stateData["ts"],  stateData["playerOneScore"], stateData["playerTwoScore"], cx, cy]))
        try:
            cv2.imshow("Camera", output)
        except:
            print(f"Cannot forward to camera over ssh using x11")


        

def on_connect(client, userdata, flags, rc):
    print("MQTT connected with result code", rc)
    client.subscribe(MQTT_TOPIC, 1)
    #client.subscribe(MQTT_SEND_TOPIC)
    print("Subscribed to:", MQTT_TOPIC, " and ", MQTT_SEND_TOPIC) 

def on_message(client, userdata, msg):
    global runGame
    global gameData
    print("MQTT message on ", msg.topic)
    payload_str = msg.payload.decode("utf-8")
    # Setting up the initial state of the experiment
    data = json.loads(payload_str)
    
    if(data["quit"] == "true"):
        runGame = False
        exit

    # A beginning timestamp will be useful the experimenter wants to do time series analysis
    data["ts"] = int(time.time())
    # Both players start with 0 scores
    data["playerOneScore"] = 0
    data["playerTwoScore"] = 0
    data["winner"] = ""

    gameData = np.append(gameData, np.array([data["PlayerOneName"], data["PlayerTwoName"], data["ts"],  data["playerOneScore"], data["playerTwoScore"], None, None]))

    with open(STATE_PATH, "w") as f:
        json.dump(data, f)
    print("State updated:", payload_str)
    # The game starts when the sense hat flashes
    time.sleep(3)
    sense.clear(255,255,255)
    time.sleep(0.2)
    sense.clear()
           
    with open(STATE_PATH, "r") as f:
        stateData = json.load(f)
    
    stringState = str(stateData)
    stringState = stringState.replace("'", '"')
    print(stringState)
    status = mqtt_client.publish(MQTT_SEND_TOPIC, stringState, 1) 
    if status == 0:
        print(f"Sent Message")
    else:
        print(f"Failed to send message")

    runGame = True
    
    #im = camera.capture_array()
    #cv2.imshow("Camera", im)
def main():
    while runGame is True:
        on_message
        captureData()
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows() 
            break




def save_state(path=""):
    now = datetime.now()
    payload = {
           # "player0ne": name1,
           # "playerTwo": name2,
            "playerOneScore": 0,
            "playerTwoScore": 1
            }
    with open(path, "w") as f:
        json.dump(payload, f)
    print("State saved:", payload)

def on_publish(client, userdata, msg):
    with open(STATE_PATH, "r") as file:
        data = json.load(file)
    print("publishing message")

    #status = client.publish(MQTT_SEND_TOPIC, data)
    #if status == 0:
    #    print(f"Sent Message")
   # else:
    #    print(f"Failed to send message")
#with open(STATE_PATH, "r") as f:
 #       stateData = json.load(f)

   # stringState = str(stateData)
  #  stringState = stringState.replace("'", '"')
   # print(stringState)
   # status = client.publish(MQTT_SEND_TOPIC, stringState) 
   # if status == 0:
   #     print(f"Sent Message")
   # else:
   #     print(f"Failed to send message")


# Set up MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect 
mqtt_client.on_message = on_message
mqtt_client.on_publish = on_publish

mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60) 
mqtt_client.loop_start()

# This will hold the program from starting to collect game data until the 
# game is started from the web page
while not runGame:
    time.sleep(0.1)
main()


gameData = np.reshape(gameData, (-1, 7))

gameDataPd = pd.DataFrame({'playerOneName': gameData[:,0], 'playerTwoName': gameData[:,1], 'timeStamp': gameData[:,2], 'playerOneScore': gameData[:,3], 'playerTwoScore': gameData[:,4], 'gyroOne': gameData[:,5], 'gyroTwo': gameData[:,6]})

gameDataJson = gameDataPd.to_json(orient = "records")
print(gameDataJson)

# Need to point the url to my laptop not to localhost, since the api isn't running locally
url = "http://192.168.1.124:5000"

requests.put(url, gameDataJson)

sys.exit("Ending Game")

mqtt_client.loop_stop()
mqtt_client.disconnect()
