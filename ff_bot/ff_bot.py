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

        print("[" + get_time() + "] Begin polling.")
        self.send_message("[" + get_time() + "] I'm alive.")
        loop = True
        while loop:
            try:
                r = requests.post("https://push.groupme.com/faye", data=json.dumps(template), headers=headers)
                try:
                    handle_response(self, r.json()[1]["data"])
                # handle response with no "data" field
                except:
                    print("[" + get_time() + "] Unable to pull data from request body: " + r.json())

            except requests.exceptions.ConnectionError:
                print("[" + get_time() + "] ConnectionError occurred. Restart polling.")
            except Exception as ex:
                print("[" + get_time() + "] Something went wrong. " + ex.__repr__())
                self.send_message("[" + get_time() + "] Something went wrong. I'm ded.")
                return

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
        elif text == "@" + BOT_NAME + " help":
            handle_bot_help(bot)
        # todo: change this to check if text includes "wonder"
        elif text == "wonder":
            handle_wonder(bot)
    except:
        return


# handle when response = "@[BOT_NAME]"
def handle_bot_name(bot):
    bot.send_message("you rang? type \"@" + BOT_NAME + " help\" to see what i can do.")


# handle when response = "@[BOT_NAME] help"
def handle_bot_help(bot):
    bot.send_message("commands:\n" +
                     "@" + BOT_NAME + " help -- show list of commands\n")


# handle when response = "wonder"
def handle_wonder(bot):
    bot.send_message("did somebody say wonder?!")


# helper function to get current time as HH:MM:SS UTC
def get_time():
    return time.strftime("%T %Z", time.localtime(time.time()))


# main class
def bot_main():
    bot = GroupMeBot(BOT_ID)
    bot.init_listener()


if __name__ == '__main__':
    bot_main()
