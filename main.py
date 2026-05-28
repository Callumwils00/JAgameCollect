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
import src.functions as functions

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

camera = functions.setup_camera()
WIDTH = 700
HEIGHT = 700

tracker = None
sense = SenseHat()

# Initalise an empty numpy array 

gameData = np.array([[], [], [], [], [], [],[]])        

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
    data["ts"] = time.time()
    # Both players start with 0 scores
    data["playerOneScore"] = 0
    data["playerTwoScore"] = 0
    data["winner"] = ""

    gameData = np.append(gameData, np.array([data["playerOneName"], data["playerTwoName"], data["ts"],  data["playerOneScore"], data["playerTwoScore"], None, None]))

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
    global camera
    while runGame is True:
        on_message
        functions.captureData(camera, gameData)
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

# Set up MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect 
mqtt_client.on_message = on_message
mqtt_client.on_publish = on_publish

mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60) 
mqtt_client.loop_start()

# This will hold the program from starting to collect game data until the 
# game is started from the web page
if __name__ == "__main__":
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
