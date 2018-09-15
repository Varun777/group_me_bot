import requests
import time
import json
import os
import random
import sys
import re
import websockets
import asyncio
import ff_bot.espn_ff_api as espn

# environment vars
BOT_ID = os.environ["BOT_ID"]
BOT_NAME = os.environ["BOT_NAME"]
USER_ID = os.environ["USER_ID"]
GROUP_ID = os.environ["GROUP_ID"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
LATEST_TRADE_TIME = espn.get_latest_trade_time()


class GroupMeBot(object):
    # Creates GroupMe Bot to send messages
    def __init__(self, bot_id):
        self.bot_id = bot_id
        self.ws_loop = self.init_listener()

    def __repr__(self):
        return "GroupMeBot(%s)" % self.bot_id

    # initialize group chat listener
    # for more info: https://dev.groupme.com/tutorials/push
    def init_listener(self):
        # start handshake with server
        client_id = self.handshake()
        # subscribe to group channel
        self.subscribe_group(client_id)
        # subscribe to user channel
        self.subscribe_user(client_id)
        # open websocket connection to listen for messages
        return asyncio.get_event_loop().run_until_complete(self.open_websocket(client_id))

    # handshake for GroupMe listener
    def handshake(self):
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

    # open websocket connection to listen for group messages
    async def open_websocket(self, client_id):
        template = {
            "channel": "/meta/connect",
            "clientId": client_id,
            "connectionType": "websocket",
            "id": "4"
        }

        while True:
            try:
                print("[" + get_time() + "] Connecting to server.", flush=True)
                async with websockets.connect("wss://push.groupme.com/faye") as ws:
                    await ws.send(json.dumps(template))
                    r = await ws.recv()

                    # if response is a failure, re-initialize ws connection
                    if not self.is_success(json.loads(r)[0]):
                        print("[" + get_time() + "] Connection broken. Re-initializing.", flush=True)
                        self.ws_loop.close()
                        asyncio.sleep(1)
                        self.init_listener()
                        return
                    elif len(json.loads(r)) > 0 and self.is_valid_response(json.loads(r)[0]):
                        user_from = json.loads(r)[0]["data"]["subject"]["name"]
                        group_id = json.loads(r)[0]["data"]["subject"]["group_id"]
                        text = json.loads(r)[0]["data"]["subject"]["text"]

                        handle_response(self, user_from, group_id, text)
            except websockets.exceptions.ConnectionClosed:
                print("[" + get_time() + "] ConnectionClosed exception. Continue loop.", flush=True)
            except ConnectionResetError:
                print("[" + get_time() + "] ConnectionResetError error. Continue loop.", flush=True)
            except Exception as ex:
                print("[" + get_time() + "] " + ex.__repr__() + " exception. Continue loop.", flush=True)

    # checks that the provided response has all required fields
    def is_valid_response(self, response):
        return "data" in response and \
               "subject" in response["data"] and \
               "name" in response["data"]["subject"] and \
               "group_id" in response["data"]["subject"] and \
               "text" in response["data"]["subject"]

    # checks that the provided response is a success
    def is_success(self, response):
        return "data" in response or ("successful" in response and response["successful"])

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
#    1) response = "@[BOT_NAME]", display greeting
#    2) response = "@[BOT_NAME] help", display list of commands
#    3) response = "@[BOT_NAME] show scores", display scores for current week
#    4) response = "@[BOT_NAME] show top [TOTAL] players", display top [TOTAL] players for current week
#    5) response = "@[BOT_NAME] salt [USER]", display random insult to [USER]
#    6) response = "@[BOT_NAME] die", kill program
#    7) response contains "wonder", display arrested development reference
#
# future support:
#    1) response = "@[BOT_NAME] show top [TOTAL] scores", display top [TOTAL] scores for year
#    2) response = "@[BOT_NAME] show bottom [TOTAL] scores", display bottom [TOTAL] scores for year
#    3) response = "@[BOT_NAME] show last [TOTAL] trades", display last [TOTAL] trades
def handle_response(bot, user_from, group_id, text):
    # get the text from response. if exception, simply return
    try:
        at_bot = "@" + BOT_NAME

        # ignore response if it comes from the bot, or from a different group
        if str.lower(user_from).__eq__(str.lower(BOT_NAME)) or group_id != GROUP_ID:
            return
        if text == at_bot:
            handle_bot_name(bot)
        elif text == at_bot + " help":
            handle_bot_help(bot)
        elif text == at_bot + " show scores":
            handle_bot_scores(bot)
        elif str.startswith(text, at_bot + " salt "):
            handle_bot_salt(bot, user_from, str.split(text, "salt ", 1)[1])
        elif text == at_bot + " die":
            kill_bot(bot)
        elif re.match(r'^' + at_bot + ' show top \d+ players$', text):
            total = re.search(r'\d+', text).group()
            handle_bot_top_players(bot, total)
        elif re.match(r'^' + at_bot + ' show last \d+ trades$', text):
            total = re.search(r'\d+', text).group()
            handle_bot_last_trades(bot, total)
        elif str.__contains__(str.lower(text), "wonder"):
            handle_bot_wonder(bot)
    except Exception as ex:
        print("[" + get_time() + "] Exception in handle_response: " + ex.__repr__(), flush=True)
        return


# handle when response = "@[BOT_NAME]"
# display greeting
def handle_bot_name(bot):
    bot.send_message("you rang? type \"@" + BOT_NAME + " help\" to see what i can do.")


# handle when response = "@[BOT_NAME] help"
# display command list
def handle_bot_help(bot):
    bot.send_message("commands:\n" +
                     "@" + BOT_NAME + " help -- show list of commands\n" +
                     "@" + BOT_NAME + " show scores -- show this weeks scores\n"
                     "@" + BOT_NAME + " show top [TOTAL] players -- show this weeks top players\n"
                     "@" + BOT_NAME + " salt [USER] -- throw salt at [USER]\n")


# handle when response = "@[BOT_NAME] salt [USER]"
# display random salty comment towards user_to
def handle_bot_salt(bot, user_from, user_to):
    if str.__contains__(str.lower(user_to), str.lower(BOT_NAME)):
        bot.send_message("listen here you lil shit...")
        return

    number = random.randint(1, 100)
    # easter egg: do this 10% of the time..
    if number <= 10:
        bot.send_message(user_from + " likes little boys.")
    # easter egg: do this 20% of the time..
    elif 10 < number <= 20:
        bot.send_message("how dare you, " + user_from + ", she's a nice lady!")
    # elif 20 < number <= 40:
    #     r = requests.get("https://insult.mattbas.org/api/en/insult.json?who=" + user_to)
    #     bot.send_message(r.json()["insult"])
    else:
        r = requests.get("https://amused.lib.id/insult@1.0.0/")
        bot.send_message(str.replace(r.json(), "You", user_to + " is a"))


# handle when response = "wonder"
# display arrested development reference
def handle_bot_wonder(bot):
    bot.send_message("did somebody say wonder?!")


# handle when response = "@[BOT_NAME] show scores"
# display scores for current week
def handle_bot_scores(bot):
    matchups = espn.get_scores(espn.get_current_week())
    scores = ""

    for m in matchups:
        if m.home_score >= m.away_score:
            first_team_name = m.home_team.team_name
            first_team_score = m.home_score
            second_team_name = m.away_team.team_name
            second_team_score = m.away_score
        else:
            first_team_name = m.away_team.team_name
            first_team_score = m.away_score
            second_team_name = m.home_team.team_name
            second_team_score = m.home_score

        scores += '%s (%.2f) - (%.2f) %s\n' % (first_team_name, first_team_score, second_team_score, second_team_name)

    bot.send_message(scores)


# handle when response = "@[BOT_NAME] show top [TOTAL] players"
# display top [TOTAL] players for the current week
def handle_bot_top_players(bot, total):
    players = espn.get_top_players(int(total), espn.get_current_week())

    response = "This Week's Top " + str(len(players)) + " Rostered Players:\n"
    for player in players:
        response += "%.2f - %s (%s) - %s" % (player["points"], player["name"], player["position"], player["team"])
        if not player["started"]:
            response += " *"
        response += "\n"

    response += "(*) = bench player"

    bot.send_message(response)


# handle when response = "@[BOT_NAME] show last [TOTAL] trades"
# display last [TOTAL] trades
def handle_bot_last_trades(bot, limit):
    bot.send_message("under construction")


# called from scheduler
# checks if there has been a new trade since the last attempt
# handles scenario by sending bot message
def handle_trade_alert(bot):
    global LATEST_TRADE_TIME
    latest_trade = espn.get_latest_trade()

    # if no trade has occurred, simply return
    if latest_trade is None:
        return

    if latest_trade["time"] > LATEST_TRADE_TIME:
        LATEST_TRADE_TIME = latest_trade["time"]

        team_0 = latest_trade["teams"][0]
        team_1 = latest_trade["teams"][1]
        players_0 = ""
        players_1 = ""

        for p in latest_trade["players"]:
            if p["from"] == team_1["id"]:
                players_0 += p["name"] + " " + "(" + p["position"] + ")\n"
            else:
                players_1 += p["name"] + " " + "(" + p["position"] + ")\n"

        bot.send_message("BREAKING NEWS!\n" +
                         "There has been a trade between " + team_0["name"] + " and " + team_1["name"] +
                         ". Here are the details...\n\n" +
                         team_0["abbrev"] + " receives:\n" +
                         players_0 + "\n" +
                         team_1["abbrev"] + " receives:\n" +
                         players_1)


# kill program
def kill_bot(bot):
    bot.send_message("k bye.")
    sys.exit(0)


# helper function to get current time as HH:MM:SS UTC
def get_time():
    return time.strftime("%T %Z", time.localtime(time.time()))

# put scheduled alerts here. alert ideas:
# Monday evening alert showing the top 10 players from the previous week
# Monday evening alert showing if any scores broke through the top 10 scores of the year
# Tuesday/Wednesday morning alert showing which players were recently added from waivers
# Thursday morning alert showing what players to watch in the Thursday night game
# Breaking news alert for trades


# main class
def bot_main():
    GroupMeBot(BOT_ID)


if __name__ == '__main__':
    bot_main()
