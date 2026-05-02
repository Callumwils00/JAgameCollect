#! /bin/python

import paho.mqtt.client as mqtt
import time
import json

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "test/JAgame"
STATE_PATH = "data/state.json"

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


# Set up MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect 
mqtt_client.on_message = on_message 

mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60) 
mqtt_client.loop_start()

time.sleep(10)

mqtt_client.loop_stop()
mqtt_client.disconnect()
