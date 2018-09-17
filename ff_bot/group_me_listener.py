import requests
import time
import json
import os
import websockets
import asyncio
import ff_bot.utils as utils

# environment vars
BOT_NAME = os.environ["BOT_NAME"]
USER_ID = os.environ["USER_ID"]
GROUP_ID = os.environ["GROUP_ID"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]


# initialize group chat listener
# for more info: https://dev.groupme.com/tutorials/push
def init(callback):
    # start handshake with server
    client_id = handshake()
    # subscribe to group channel
    subscribe_group(client_id)
    # subscribe to user channel
    subscribe_user(client_id)
    # open websocket connection to listen for messages
    return asyncio.get_event_loop().run_until_complete(open_websocket(client_id, callback))


# handshake for GroupMe listener
def handshake():
    # start handshake with server
    template = {
        "channel": "/meta/handshake",
        "version": "1.0",
        "supportedConnectionTypes": ["websocket"],
        "id": "1"}
    headers = {'content-type': 'application/json'}
    r = requests.post("https://push.groupme.com/faye", data=json.dumps(template), headers=headers)
    return r.json()[0]["clientId"]


# subscribe to user channel for GroupMe listener
def subscribe_user(client_id):
    template = {
        "channel": "/meta/subscribe",
        "clientId": client_id,
        "subscription": "/user/" + USER_ID,
        "id": "2",
        "ext": {
            "access_token": ACCESS_TOKEN,
            "timestamp": time.time()}}
    headers = {'content-type': 'application/json'}
    requests.post("https://push.groupme.com/faye", data=json.dumps(template), headers=headers)


# subscribe to group channel for GroupMe listener
def subscribe_group(client_id):
    template = {
        "channel": "/meta/subscribe",
        "clientId": client_id,
        "subscription": "/group/" + GROUP_ID,
        "id": "3",
        "ext": {
            "access_token": ACCESS_TOKEN,
            "timestamp": time.time()}}
    headers = {'content-type': 'application/json'}
    requests.post("https://push.groupme.com/faye", data=json.dumps(template), headers=headers)


# open websocket connection to listen for group messages
async def open_websocket(client_id, callback):
    template = {
        "channel": "/meta/connect",
        "clientId": client_id,
        "connectionType": "websocket",
        "id": "4"
    }

    while True:
        try:
            utils.out("Connecting to server.")
            async with websockets.connect("wss://push.groupme.com/faye") as ws:
                await ws.send(json.dumps(template))
                r = await ws.recv()

                # if response is a failure, re-initialize ws connection
                if not is_success(json.loads(r)[0]):
                    utils.out("Connection broken. Re-initializing.")
                    asyncio.get_event_loop().close()
                    asyncio.sleep(1)
                    init(callback)
                    return
                elif len(json.loads(r)) > 0 and is_valid_response(json.loads(r)[0]):
                    user_from = json.loads(r)[0]["data"]["subject"]["name"]
                    group_id = json.loads(r)[0]["data"]["subject"]["group_id"]
                    text = json.loads(r)[0]["data"]["subject"]["text"]

                    callback(user_from, group_id, text)
        except websockets.exceptions.ConnectionClosed:
            utils.out("ConnectionClosed exception. Continue loop.")
        except ConnectionResetError:
            utils.out("ConnectionResetError error. Continue loop.")
        except Exception as ex:
            utils.out(ex.__repr__() + " exception. Continue loop.")


# checks that the provided response has all required fields
def is_valid_response(response):
    return "data" in response and \
           "subject" in response["data"] and \
           "name" in response["data"]["subject"] and \
           "group_id" in response["data"]["subject"] and \
           "text" in response["data"]["subject"]


# checks that the provided response is a success
def is_success(response):
    return "data" in response or ("successful" in response and response["successful"])
