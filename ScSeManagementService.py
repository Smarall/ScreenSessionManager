# ScreenSessionManagementService
# author: Smarall
# creation_date: 12.03.2024

# mosquitto_pub -h localhost -t server/start -m "minecraftVanilla.json"
# mosquitto_pub -h localhost -t server/stop -m "minecraftVanilla.json"
# mosquitto_pub -h localhost -t server/kill -m "minecraftVanilla.json"


import os
import sys
import paho.mqtt.client as mqtt
from enum import Enum
import glob
import json


# ENVIRONMENT
configPath = './serverConfigs/'


# CONNECTION
version = '5'
# 'websockets' or 'tcp'
transport = 'tcp'
broker = 'zbox'
port = 1883 if (transport == 'tcp') else 443


# TOPICS
class Topics(Enum):
    SERVERSTART = 'server/start'
    SERVERSTOP = 'server/stop'
    SERVERKILL = 'server/kill'
    GETCONFIGLIST = 'info/configList'
    GETSCREENS = 'info/activeScreens'


def topicAction(topic, message):
    tmpMessage = message.decode("utf-8")
    print('Starting Server ' + str(tmpMessage))
    with open(configPath + str(tmpMessage), 'r') as config:
        serverConfig = json.load(config)
    match topic:
        case Topics.SERVERSTART.value:
            os.system("screen -m -d -S %s\n"
                      "sleep 1\n"
                      "screen -S %s -X stuff 'cd %s\n%s %s\n'" %
                      (serverConfig['name'],
                       serverConfig['name'], serverConfig['absolutePath'], serverConfig['startCommand'], serverConfig['startParameters']))
        case Topics.SERVERSTOP.value:
            print('Stopping Server ' + str(tmpMessage))
            os.system("screen -S %s -X stuff '%s\n'\n"
                      "sleep 60\n"
                      "screen -S %s -X quit\n" %
                      (serverConfig['name'], serverConfig['stopCommand'],
                       serverConfig['name']))
        case Topics.SERVERKILL.value:
            print('Killing Server ' + str(message))
            os.system("screen -S %s -X quit\n" % (serverConfig['name']))
        case Topics.GETCONFIGLIST.value:
            print(glob.glob(configPath+'*.json'))
        case Topics.GETSCREENS.value:
            print('Screen List not implemented yet')
        case _:
            pass


# CLIENT
client = None
if version == '5':
    client = mqtt.Client(client_id="ScSeMaService",
                         transport=transport,
                         protocol=mqtt.MQTTv5)
    from paho.mqtt.properties import Properties
    from paho.mqtt.packettypes import PacketTypes

    properties = Properties(PacketTypes.CONNECT)
    properties.SessionExpiryInterval = 30 * 60  # in seconds
    client.connect(broker,
                   port=port,
                   clean_start=mqtt.MQTT_CLEAN_START_FIRST_ONLY,
                   properties=properties,
                   keepalive=60)
if version == '3':
    client = mqtt.Client(client_id="ScSeMaService",
                         transport=transport,
                         protocol=mqtt.MQTTv311,
                         clean_session=True)
    client.connect(broker, port=port, keepalive=60)


# CALLBACKS
def on_message(client, userdata, message):
    print(" Received message " + str(message.payload)
          + " on topic '" + message.topic)
    topicAction(message.topic, message.payload)


client.on_message = on_message
# client.on_connect = on_connect
# client.on_publish = on_publish
# client.on_subscribe = on_subscribe

for topic in Topics:
    client.subscribe(topic.value, 2)

client.loop_forever()
