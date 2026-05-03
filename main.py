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
MQTT_TOPIC = "test/JAgame"
STATE_PATH = "data/state.json"

sense = SenseHat()
my_stream = BytesIO()
camera = Picamera2()
camera.start()

def captureData():
    # capture a frame 
    im = camera.capture_array()
    cv2.imshow("Camera", im)


def on_connect(client, userdata, flags, rc):
    print("MQTT connected with result code", rc)
    client.subscribe(MQTT_TOPIC)
    print("Subscribed to:", MQTT_TOPIC) 

def on_message(client, userdata, msg):
    print("MQTT message on ", msg.topic)
    payload_str = msg.payload.decode("utf-8")
   # data = json.loads(payload_str)
   # data["ts"] = int(time.time())
    #with open(STATE_PATH, "w") as f:
    #    json.dump(data, f)
    print("State updated:", payload_str) 
    sense.clear(255,0,0)
    time.sleep(0.5)
    sense.clear()
    while True:
        captureData()
        if cv2.waitKey(1) & 0xFF == ord('q'):
           break
    # Release the camera and close the windows
    cv2.destroyAllWindows()

# Set up MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect 
mqtt_client.on_message = on_message 

mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60) 
mqtt_client.loop_start()

time.sleep(30)

mqtt_client.loop_stop()
mqtt_client.disconnect()
