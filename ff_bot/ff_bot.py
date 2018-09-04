import requests
import time
import json
import os

# environment vars
BOT_ID = os.environ["BOT_ID"]
BOT_NAME = os.environ["BOT_NAME"]
USER_ID = os.environ["USER_ID"]
GROUP_ID = os.environ["GROUP_ID"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]


class GroupMeBot(object):
    # Creates GroupMe Bot to send messages
    def __init__(self, bot_id):
        self.bot_id = bot_id

    def __repr__(self):
        return "GroupMeBot(%s)" % self.bot_id

    # initialize group chat listener
    def init_listener(self):
        # start handshake with server
        client_id = self.handshake()
        # subscribe to user channel
        self.subscribe_user(client_id)
        # subscribe to group channel
        self.subscribe_group(client_id)
        # long poll for stuff
        self.start_poll(client_id)
        return

    # handshake for GroupMe listener
    def handshake(self):
        # start handshake with server
        template = {
            "channel": "/meta/handshake",
            "version": "1.0",
            "supportedConnectionTypes": ["long-polling"],
            "id": "1"}
        headers = {'content-type': 'application/json'}
        r = requests.post("https://push.groupme.com/faye", data=json.dumps(template), headers=headers)
        return r.json()[0]["clientId"]

    # subscribe to user channel for GroupMe listener
    def subscribe_user(self, client_id):
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
    def subscribe_group(self, client_id):
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

    # begin polling
    def start_poll(self, client_id):
        template = {
            "channel": "/meta/connect",
            "clientId": client_id,
            "connectionType": "long-polling",
            "id": "4"
        }
        headers = {'content-type': 'application/json'}

        loop = True
        while loop:
            try:
                r = requests.post("https://push.groupme.com/faye", data=json.dumps(template), headers=headers)
            except ConnectionError:
                print("ohnos ConnectionError")
                self.start_poll(client_id)
            except ConnectionAbortedError:
                print("ohnos ConnectionAbortedError")
                self.start_poll(client_id)
            handle_response(self, r.json()[1]["data"])

    # Send message from bot to chat room
    def send_message(self, text):
        template = {
            "bot_id": self.bot_id,
            "text": text,
            "attachments": []}
        headers = {'content-type': 'application/json'}
        requests.post("https://api.groupme.com/v3/bots/post", data=json.dumps(template), headers=headers)


# handle different response scenarios here.
# currently supports:
#    1) response = "@[BOT_NAME]", print greeting
#    2) response = "wonder", print arrested development reference
#
# future scenarios:
#    ⁃ response contains “hard”, print “thats what she said”
#    ⁃ response = "@[BOT_NAME] help", provide list of commands
#    - response = "@[BOT_NAME] [COMMAND]", perform command
def handle_response(bot, json_data):
    # get the text from response. if exception, simply return
    try:
        text = json_data["subject"]["text"]
        if text == "@" + BOT_NAME:
            handle_bot_name(bot)
        elif text == "wonder":
            handle_wonder(bot)
    except:
        return


# handle when response = "@[BOT_NAME]"
def handle_bot_name(bot):
    bot.send_message("whatup losers. im @" + BOT_NAME + ". " +
                     "pretty soon ill be able to handle commands straight from here. " +
                     "ill mostly just be hangin around here to throw salt at people. peace.")


# handle when response = "wonder"
def handle_wonder(bot):
    bot.send_message("did somebody say wonder?!")


# main class
def bot_main():
    bot = GroupMeBot(BOT_ID)
    bot.init_listener()


if __name__ == '__main__':
    bot_main()
