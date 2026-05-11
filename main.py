#! /bin/python

import paho.mqtt.client as mqtt
import time
import json
from sense_hat import SenseHat
from io import BytesIO
from picamera2 import Picamera2
import cv2

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "test/JAgame/fromWebPage"
MQTT_SEND_TOPIC = "test/JAgame/toWebPage"
STATE_PATH = "data/state.json"

sense = SenseHat()
my_stream = BytesIO()
camera = Picamera2()
WIDTH = 650
HEIGHT = 650
config = camera.create_preview_configuration({'format': 'YUV420', 'size': (WIDTH, HEIGHT)})
camera.configure(config)
camera.start()
#stop_cascade = cv2.CascadeClassifier('stop_data.xml')

def captureData():
    # capture a frame 
#    found = stop_cascade.detectMultiScale(im, minSize=(20,20))
#    for(x,y,w,h) in found:
#        cv2.rectangle(im, (x, y), (x + w, y + h), (0, 255, 0), 5)
    cv2.imshow("Camera", im)

def on_connect(client, userdata, flags, rc):
    print("MQTT connected with result code", rc)
    client.subscribe(MQTT_TOPIC)
    #client.subscribe(MQTT_SEND_TOPIC)
    print("Subscribed to:", MQTT_TOPIC, " and ", MQTT_SEND_TOPIC) 

def on_message(client, userdata, msg):
    print("MQTT message on ", msg.topic)
    payload_str = msg.payload.decode("utf-8")
    data = json.loads(payload_str)
    data["ts"] = int(time.time())
    data["playerOneScore"] = 0
    data["playerTwoScore"] = 1
    with open(STATE_PATH, "w") as f:
        json.dump(data, f)
    print("State updated:", payload_str) 
    sense.clear(255,255,255)
    time.sleep(0.2)
    sense.clear()
           
    with open(STATE_PATH, "r") as f:
        stateData = json.load(f)
    
    stringState = str(stateData)
    stringState = stringState.replace("'", '"')
    print(stringState)
    status = mqtt_client.publish(MQTT_SEND_TOPIC, stringState, 0) 
    if status == 0:
        print(f"Sent Message")
    else:
        print(f"Failed to send message")
    
    #im = camera.capture_array()
    #cv2.imshow("Camera", im)
    
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

#time.sleep(30)
im = camera.capture_array()

captureData()
time.sleep(30)
cv2.destroyAllWindows()

time.sleep(30)

"""while True:
    captureData()
    if cv2.waitKey(1) & 0xFF == ord('q'):
         break
    # Release the camera and close the windows
    cv2.destroyAllWindows()
"""
mqtt_client.loop_stop()
mqtt_client.disconnect()
