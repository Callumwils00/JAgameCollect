#! /bin/python

MQTT_BROKER = "broker.hivemq.com"
# The MQTT port here is different to the port referenced in the web page (8884)
# That is because this program can send to the MQTT broker directly since it isn't sending
# from a web browser like the webpage that needs to use websockets.
MQTT_PORT = 1883
MQTT_TOPIC = "test/JAgame/fromWebPage"
MQTT_SEND_TOPIC = "test/JAgame/toWebPage"
STATE_PATH = "data/state.json"

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
