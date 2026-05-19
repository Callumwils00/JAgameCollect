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
WIDTH = 700
HEIGHT = 700
config = camera.create_preview_configuration({'format': 'RGB888', 'size': (WIDTH, HEIGHT)})
camera.configure(config)
camera.start()
tracker = None

def captureData():
    # capture a frame
    global tracker # the use of the global keyword means that the global tracker variable is used. This can
    # change outside of the scope of the function
    im = camera.capture_array()
    gray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)#im[:HEIGHT, :]#cv2.cvtColor(im, cv2.COLOR_YUV2GRAY_I420)
    gausBlur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(gausBlur, 20, 40)
    #ret, thresh = cv2.threshold(edges, 127, 255, 0)
    output = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    
    if tracker == None:
        contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        largest = max(contours, key=cv2.contourArea)
        print(f"Contours found: {len(contours)}")
        if cv2.contourArea(largest) > 20:
            x, y, w, h = cv2.boundingRect(largest)
            tracker = cv2.legacy.TrackerMOSSE_create()
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
            # using and rather than & as & is a bitwise operand which leads to a logical error
            if 300 < cx < 500 and 300 < cy < 500: 
                print(f"Somebody Scored")
                with open(STATE_PATH, "r") as f:
                    stateData = json.load(f)
                stateData["playerOneScore"] = int(stateData["playerOneScore"]) + 1
                status = mqtt_client.publish(MQTT_SEND_TOPIC, stateData)
                if status == 0:
                    print(f"Sent Message")
                else:
                    print(f"Failed to send message")
            elif 20 < cx < 30 & 20 < cy < 30:
                print(f"Somebody Scored")
                with open(STATE_PATH, "r") as f:
                    stateData = json.load(f)
                stateData["playerTwoScore"] = int(stateData["playerTwoScore"]) + 1
                status = mqtt_client.publish(MQTT_SEND_TOPIC, stateData)
                if status == 0:
                    print(f"Sent Message")
                else:
                    print(f"Failed to send message")
            else:
                print(f"No score")
        else:
            tracker = None # The ball is lost so re-detect in the next frame
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
    print("MQTT message on ", msg.topic)
    payload_str = msg.payload.decode("utf-8")
    # Setting up the initial state of the experiment
    data = json.loads(payload_str)
    # A beginning timestamp will be useful the experimenter wants to do time series analysis
    data["ts"] = int(time.time())
    # Both players start with 0 scores
    data["playerOneScore"] = 0
    data["playerTwoScore"] = 0
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
    status = mqtt_client.publish(MQTT_SEND_TOPIC, stringState, 0) 
    if status == 0:
        print(f"Sent Message")
    else:
        print(f"Failed to send message")
    
   # time.sleep(5)
    while True:
        captureData()
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()

    
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
